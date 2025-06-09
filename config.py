import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///experts_new.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 报告输出配置
    REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    
    # 千问API配置
    QWEN_API_KEY = "sk-7d87b5a8b0b3483a9ab191a0f3f1c456"
    QWEN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    # 评分权重配置
    SCORE_WEIGHTS = {
        'official_website': 0.50,  # 官网权重
        'ai_search': 0.35,        # AI搜索权重
        'baidu_baike': 0.15       # 百度百科权重
    }
    
    # 基础资质评分权重
    BASIC_SCORE_WEIGHTS = {
        'name': 0.25,             # 姓名权重
        'birth_year': 0.25,       # 出生年月权重
        'affiliation': 0.25,      # 工作单位权重
        'title': 0.25             # 职称职务权重
    }
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    
    @staticmethod
    def init_app(app):
        # 确保必要的目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.REPORTS_FOLDER, exist_ok=True) 