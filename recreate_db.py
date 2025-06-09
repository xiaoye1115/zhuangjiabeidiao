import sqlite3
import os
from datetime import datetime

# 删除现有数据库文件
db_path = 'experts.db'
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"已删除现有数据库文件: {db_path}")
    except Exception as e:
        print(f"删除数据库文件失败: {str(e)}")
        exit(1)

# 连接新数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 创建用户表
cursor.execute('''
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(120) NOT NULL,
    is_admin BOOLEAN DEFAULT 0
)
''')
print("已创建用户表")

# 创建专家表
cursor.execute('''
CREATE TABLE expert (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    birth_year VARCHAR(20),
    affiliation VARCHAR(200),
    credit_code VARCHAR(100),
    title VARCHAR(100),
    verification_status VARCHAR(20) DEFAULT 'pending',
    verification_date DATETIME,
    verified_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_score FLOAT,
    has_negative_news BOOLEAN DEFAULT 0,
    FOREIGN KEY (verified_by) REFERENCES user (id)
)
''')
print("已创建专家表")

# 创建默认管理员账户
cursor.execute('''
INSERT INTO user (username, password, is_admin)
VALUES (?, ?, ?)
''', ('admin', 'admin', 1))
print("已创建默认管理员账户")

# 提交更改
conn.commit()
print("数据库创建完成")

# 关闭连接
conn.close() 