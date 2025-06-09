from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import pandas as pd
from expert_verification import ExpertVerification
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

db = SQLAlchemy(app)

# 全局变量用于跟踪验证进度
verification_progress = {
    'verified_experts': 0,
    'total_experts': 0,
    'status': 'idle',  # idle, processing, completed, error
    'results_summary': {
        'total': 0,
        'trusted': 0,
        'questioned': 0,
        'untrusted': 0
    }
}

# 数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Expert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_year = db.Column(db.String(20))
    affiliation = db.Column(db.String(200))
    credit_code = db.Column(db.String(100))
    title = db.Column(db.String(100))
    verification_status = db.Column(db.String(20), default='pending')  # 验证状态：pending, verified, failed
    verification_date = db.Column(db.DateTime)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_score = db.Column(db.Float)  # 总分
    has_negative_news = db.Column(db.Boolean, default=False)  # 是否有负面舆情

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# 路由
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:  # 实际应用中应使用密码哈希
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))
    
@app.route('/dashboard')
@login_required
def dashboard():
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页显示10条记录
    
    # 获取所有专家记录并分页
    pagination = Expert.query.order_by(Expert.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    experts = pagination.items

    # 统计信息
    total_queries = Expert.query.count()
    
    # 获取最近30天的查询趋势
    today = datetime.now().date()
    trend_dates = []
    trend_counts = []
    for i in range(29, -1, -1):  # 从29天前到今天
        date = today - timedelta(days=i)
        count = Expert.query.filter(db.func.date(Expert.created_at) == date).count()
        trend_dates.append(date.strftime('%m-%d'))
        trend_counts.append(count)

    # 今日查询数量
    today_queries = Expert.query.filter(db.func.date(Expert.created_at) == today).count()

    # 计算可信度分布
    trusted_count = Expert.query.filter(Expert.total_score >= 80).count()
    questioned_count = Expert.query.filter(Expert.total_score.between(60, 79.99)).count()
    untrusted_count = Expert.query.filter(Expert.total_score < 60).count()
    
    # 最近查询记录
    recent_records = []
    for e in experts:
        # 确定可信度类型
        result_type = None
        if e.total_score is not None:
            if e.total_score >= 80:
                result_type = "可信"
            elif e.total_score >= 60:
                result_type = "质疑"
            else:
                result_type = "不可信"
        
        recent_records.append({
            'id': e.id,
            'query_time': e.created_at.strftime('%Y-%m-%d %H:%M'),
            'expert_name': e.name,
            'affiliation': e.affiliation,
            'verification_status': e.verification_status,
            'total_score': e.total_score,
            'result_type': result_type
        })

    stats = {
        'total_queries': total_queries,
        'today_queries': today_queries,
        'trend_dates': trend_dates,
        'trend_counts': trend_counts,
        'trust_distribution': {
            'trusted': trusted_count,
            'questioned': questioned_count,
            'untrusted': untrusted_count
        }
    }

    return render_template(
        'dashboard.html',
        experts=experts,
        stats=stats,
        recent_records=recent_records,
        pagination=pagination
    )

@app.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    """获取仪表盘实时统计数据的API"""
    experts = Expert.query.all()
    total_queries = len(experts)
    
    # 获取最近30天的查询趋势
    today = datetime.now().date()
    trend_dates = []
    trend_counts = []
    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        count = sum(1 for e in experts if e.created_at and e.created_at.date() == date)
        trend_dates.append(date.strftime('%m-%d'))
        trend_counts.append(count)

    # 今日查询数量
    today_queries = trend_counts[-1]
    
    # 可信度分布
    trusted_count = sum(1 for e in experts if e.total_score and e.total_score >= 80)
    questioned_count = sum(1 for e in experts if e.total_score and 60 <= e.total_score < 80)
    untrusted_count = sum(1 for e in experts if e.total_score and e.total_score < 60)
    
    # 负面舆情数量
    negative_news_count = sum(1 for e in experts if e.has_negative_news)

    return jsonify({
        'total_queries': total_queries,
        'today_queries': today_queries,
        'trend_dates': trend_dates,
        'trend_counts': trend_counts,
        'trust_distribution': {
            'trusted': trusted_count,
            'questioned': questioned_count,
            'untrusted': untrusted_count
        },
        'negative_news_count': negative_news_count
    })

@app.route('/verify_single', methods=['GET', 'POST'])
@login_required
def verify_single():
    if request.method == 'POST':
        expert_data = {
            "专家姓名": request.form.get('name'),
            "出生年月": request.form.get('birth_year'),
            "工作单位": request.form.get('affiliation'),
            "工作单位统一社会信用代码": request.form.get('credit_code'),
            "职称职务": request.form.get('title')
        }
        verification = ExpertVerification()
        result = verification.verify_expert(expert_data)
        if result:
            # 保存验证结果到数据库
            try:
                # 检查是否已存在相同专家记录
                existing_expert = Expert.query.filter_by(
                    name=expert_data["专家姓名"],
                    affiliation=expert_data["工作单位"]
                ).first()
                
                if existing_expert:
                    # 更新现有记录
                    existing_expert.birth_year = expert_data["出生年月"]
                    existing_expert.credit_code = expert_data["工作单位统一社会信用代码"]
                    existing_expert.title = expert_data["职称职务"]
                    existing_expert.total_score = result["scores"]["total_score"]
                    existing_expert.verification_status = "verified"
                    existing_expert.verification_date = datetime.now()
                    existing_expert.verified_by = session.get('user_id')
                    existing_expert.has_negative_news = len(result["negative_news"]) > 0
                else:
                    # 创建新记录
                    new_expert = Expert(
                        name=expert_data["专家姓名"],
                        birth_year=expert_data["出生年月"],
                        affiliation=expert_data["工作单位"],
                        credit_code=expert_data["工作单位统一社会信用代码"],
                        title=expert_data["职称职务"],
                        total_score=result["scores"]["total_score"],
                        verification_status="verified",
                        verification_date=datetime.now(),
                        verified_by=session.get('user_id'),
                        has_negative_news=len(result["negative_news"]) > 0
                    )
                    db.session.add(new_expert)
                
                db.session.commit()
                print(f"保存专家信息成功: {expert_data['专家姓名']}")
            except Exception as e:
                db.session.rollback()
                print(f"保存专家信息失败: {str(e)}")
                
            return render_template('result.html', results=[result], mode='single')
        else:
            flash('验证失败')
            return redirect(url_for('verify_single'))
    return render_template('verify_single.html')

@app.route('/verify_batch', methods=['GET', 'POST'])
@login_required
def verify_batch():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 重置进度状态
            global verification_progress
            verification_progress['status'] = 'processing'
            verification_progress['verified_experts'] = 0
            verification_progress['total_experts'] = 0
            verification_progress['results_summary'] = {
                'total': 0,
                'trusted': 0,
                'questioned': 0,
                'untrusted': 0
            }
            
            verification = ExpertVerification(progress_callback=update_progress)
            results = verification.process_batch(filepath)
            
            if results:
                # 保存批量验证结果到数据库
                try:
                    for result in results:
                        expert_data = result["expert_data"]
                        # 检查是否已存在相同专家记录
                        existing_expert = Expert.query.filter_by(
                            name=expert_data["专家姓名"],
                            affiliation=expert_data["工作单位"]
                        ).first()
                        
                        if existing_expert:
                            # 更新现有记录
                            existing_expert.birth_year = expert_data["出生年月"]
                            existing_expert.credit_code = expert_data["工作单位统一社会信用代码"]
                            existing_expert.title = expert_data["职称职务"]
                            existing_expert.total_score = result["scores"]["total_score"]
                            existing_expert.verification_status = "verified"
                            existing_expert.verification_date = datetime.now()
                            existing_expert.verified_by = session.get('user_id')
                            existing_expert.has_negative_news = len(result["negative_news"]) > 0
                        else:
                            # 创建新记录
                            new_expert = Expert(
                                name=expert_data["专家姓名"],
                                birth_year=expert_data["出生年月"],
                                affiliation=expert_data["工作单位"],
                                credit_code=expert_data["工作单位统一社会信用代码"],
                                title=expert_data["职称职务"],
                                total_score=result["scores"]["total_score"],
                                verification_status="verified",
                                verification_date=datetime.now(),
                                verified_by=session.get('user_id'),
                                has_negative_news=len(result["negative_news"]) > 0
                            )
                            db.session.add(new_expert)
                    
                    db.session.commit()
                    print(f"批量保存专家信息成功，共 {len(results)} 条记录")
                except Exception as e:
                    db.session.rollback()
                    print(f"批量保存专家信息失败: {str(e)}")
                
                # 更新结果统计
                verification_progress['status'] = 'completed'
                verification_progress['results_summary']['total'] = len(results)
                verification_progress['results_summary']['trusted'] = sum(1 for r in results if r['scores']['result_type'] == '可信')
                verification_progress['results_summary']['questioned'] = sum(1 for r in results if r['scores']['result_type'] == '质疑')
                verification_progress['results_summary']['untrusted'] = sum(1 for r in results if r['scores']['result_type'] == '不可信')
                
                return render_template('result.html', 
                                      results=results, 
                                      mode='batch', 
                                      summary=verification_progress['results_summary'])
            else:
                verification_progress['status'] = 'error'
                flash('批量验证失败')
                return redirect(url_for('verify_batch'))
        else:
            flash('请上传正确的Excel文件')
            return redirect(url_for('verify_batch'))
    return render_template('verify_batch.html')

@app.route('/batch-progress')
@login_required
def get_batch_progress():
    """获取批量验证进度的API"""
    return jsonify({
        'status': verification_progress['status'],
        'processed': verification_progress['verified_experts'],
        'total': verification_progress['total_experts'],
        'summary': verification_progress['results_summary']
    })

@app.route('/progress')
@login_required
def get_progress():
    return jsonify({
        'current': verification_progress['verified_experts'],
        'total': verification_progress['total_experts']
    })

def update_progress(current, total):
    """更新验证进度"""
    global verification_progress
    verification_progress['verified_experts'] = current
    verification_progress['total_experts'] = total

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error='页面未找到'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error='服务器内部错误'), 500

@app.route('/verification/<int:expert_id>')
@login_required
def expert_detail(expert_id):
    """查看专家详情"""
    expert = Expert.query.get_or_404(expert_id)
    
    # 根据可信度分数确定结果类型
    if expert.total_score is not None:
        if expert.total_score >= 80:
            result_type = "可信"
        elif expert.total_score >= 60:
            result_type = "质疑"
        else:
            result_type = "不可信"
    else:
        result_type = "未评分"
    
    # 重新进行验证以获取完整的比对信息
    expert_data = {
        "专家姓名": expert.name,
        "出生年月": expert.birth_year,
        "工作单位": expert.affiliation,
        "工作单位统一社会信用代码": expert.credit_code,
        "职称职务": expert.title
    }
    
    verification = ExpertVerification()
    verification_result = verification.verify_expert(expert_data)
    
    # 如果验证成功，使用验证结果；否则创建一个基本结果对象
    if verification_result:
        result = verification_result
    else:
        # 创建一个与expert_detail.html模板兼容的结果对象
        result = {
            "expert_data": expert_data,
            "scores": {
                "total_score": expert.total_score,
                "result_type": result_type
            },
            "negative_news": [],  # 默认为空列表
            "comparisons": {
                "school": {
                    "name": "缺失", "birth_year": "缺失", "affiliation": "缺失", "title": "缺失",
                    "name_input": expert.name, "birth_year_input": expert.birth_year,
                    "affiliation_input": expert.affiliation, "title_input": expert.title,
                    "name_source": "", "birth_year_source": "", "affiliation_source": "", "title_source": ""
                },
                "baike": {
                    "name": "缺失", "birth_year": "缺失", "affiliation": "缺失", "title": "缺失",
                    "name_input": expert.name, "birth_year_input": expert.birth_year,
                    "affiliation_input": expert.affiliation, "title_input": expert.title,
                    "name_source": "", "birth_year_source": "", "affiliation_source": "", "title_source": ""
                },
                "qwen": {
                    "name": "缺失", "birth_year": "缺失", "affiliation": "缺失", "title": "缺失",
                    "name_input": expert.name, "birth_year_input": expert.birth_year,
                    "affiliation_input": expert.affiliation, "title_input": expert.title,
                    "name_source": "", "birth_year_source": "", "affiliation_source": "", "title_source": "",
                    "basic_info": {"研究方向": "未知"}
                }
            },
            "ai_info": "未能获取AI信息"
        }
    
    return render_template('expert_detail.html', result=result, expert=expert)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # 创建默认管理员账户
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='admin', is_admin=True)
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True) 