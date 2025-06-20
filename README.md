# 专家背调系统

这是一个用于验证专家信息的系统，通过整合多个数据源（官网、百度百科、AI）来评估专家信息的真实性。

## 项目结构

```
.
├── app.py                 # Flask应用主文件
├── config.py             # 配置文件
├── expert_verification.py # 专家验证核心逻辑
├── requirements.txt      # 项目依赖
├── static/              # 静态文件
│   ├── css/            # CSS样式文件
│   └── js/             # JavaScript文件
├── templates/           # HTML模板
│   ├── base.html       # 基础模板
│   ├── index.html      # 首页
│   ├── login.html      # 登录页
│   ├── dashboard.html  # 仪表盘
│   ├── verify.html     # 验证页面
│   ├── result.html     # 结果页面
│   └── error.html      # 错误页面
├── reports/            # 报告输出目录
└── uploads/           # 文件上传目录
```

## 功能说明

1. 用户认证
   - 登录功能（默认账号密码：admin/admin）
   - 会话管理

2. 专家信息验证
   - 单条查询：输入专家基本信息进行验证
   - 批量查询：上传Excel文件进行批量验证
   - 实时进度显示

3. 验证结果展示
   - 分数据源展示（官网、百度百科、AI）
   - 评分详情（基础资质一致性评分）
   - 比对结果（一致、不一致、缺失）

4. 评分规则
   - 官网占比：50%
   - AI占比：35%
   - 百科占比：15%
   - 基础资质一致性评分：100分
     - 姓名：25%
     - 出生年月：25%
     - 工作单位：25%
     - 职称职务：25%

## 安装说明

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
创建 .env 文件并设置以下变量：
```
SECRET_KEY=your-secret-key
QWEN_API_KEY=your-qwen-api-key
```

3. 运行应用：
```bash
python app.py
```

## 使用说明

1. 访问系统：
   - 打开浏览器访问 http://localhost:5000
   - 使用默认账号密码登录（admin/admin）

2. 单条查询：
   - 在验证页面填写专家信息
   - 点击"开始查询"按钮
   - 等待验证完成，查看结果

3. 批量查询：
   - 在验证页面点击"批量查询"
   - 上传符合格式要求的Excel文件
   - 等待验证完成，查看结果

## 注意事项

1. 确保本地知识库文件（本地知识库.xlsx）存在且格式正确
2. 确保有正确的千问API密钥
3. 批量查询时注意Excel文件格式要求 #   z h u a n g j i a b e i d i a o  
 #   z h u a n g j i a b e i d i a o  
 #   z h u a n g j i a b e i d i a o  
 #   z h u a n g j i a b e i d i a o  
 