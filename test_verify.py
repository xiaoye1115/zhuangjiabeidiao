import sqlite3
import os
from datetime import datetime

# 模拟一个专家验证结果
mock_expert_data = {
    "专家姓名": "测试专家",
    "出生年月": "1980年1月",
    "工作单位": "测试单位",
    "工作单位统一社会信用代码": "12345678901234567X",
    "职称职务": "教授"
}

mock_result = {
    "expert_data": mock_expert_data,
    "scores": {
        "total_score": 85.5,
        "result_type": "可信"
    },
    "negative_news": []
}

# 连接数据库
conn = sqlite3.connect('experts.db')
cursor = conn.cursor()

print("当前数据库专家记录数量:")
cursor.execute("SELECT COUNT(*) FROM expert")
count_before = cursor.fetchone()[0]
print(f"- 专家记录数: {count_before}")

# 模拟保存专家记录
try:
    # 检查是否已存在相同专家记录
    cursor.execute(
        "SELECT id FROM expert WHERE name = ? AND affiliation = ?",
        (mock_expert_data["专家姓名"], mock_expert_data["工作单位"])
    )
    existing_expert = cursor.fetchone()
    
    if existing_expert:
        # 更新现有记录
        cursor.execute(
            """
            UPDATE expert SET 
                birth_year = ?,
                credit_code = ?,
                title = ?,
                total_score = ?,
                verification_status = ?,
                verification_date = ?,
                has_negative_news = ?
            WHERE id = ?
            """,
            (
                mock_expert_data["出生年月"],
                mock_expert_data["工作单位统一社会信用代码"],
                mock_expert_data["职称职务"],
                mock_result["scores"]["total_score"],
                "verified",
                datetime.now().isoformat(),
                len(mock_result["negative_news"]) > 0,
                existing_expert[0]
            )
        )
        print(f"更新了专家记录: {mock_expert_data['专家姓名']}")
    else:
        # 创建新记录
        cursor.execute(
            """
            INSERT INTO expert (
                name, birth_year, affiliation, credit_code, title,
                total_score, verification_status, verification_date, has_negative_news, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mock_expert_data["专家姓名"],
                mock_expert_data["出生年月"],
                mock_expert_data["工作单位"],
                mock_expert_data["工作单位统一社会信用代码"],
                mock_expert_data["职称职务"],
                mock_result["scores"]["total_score"],
                "verified",
                datetime.now().isoformat(),
                len(mock_result["negative_news"]) > 0,
                datetime.now().isoformat()
            )
        )
        print(f"新增了专家记录: {mock_expert_data['专家姓名']}")
    
    conn.commit()
    print("数据库操作成功")
except Exception as e:
    conn.rollback()
    print(f"数据库操作失败: {str(e)}")

# 验证数据库记录增加
print("\n测试后数据库专家记录数量:")
cursor.execute("SELECT COUNT(*) FROM expert")
count_after = cursor.fetchone()[0]
print(f"- 专家记录数: {count_after}")

if count_after > count_before:
    print("测试成功: 专家记录数量增加")
elif count_after == count_before and existing_expert:
    print("测试成功: 更新了现有专家记录")
else:
    print("测试失败: 专家记录数量未增加")

# 查看新增/更新的记录
cursor.execute(
    "SELECT * FROM expert WHERE name = ? AND affiliation = ?", 
    (mock_expert_data["专家姓名"], mock_expert_data["工作单位"])
)
record = cursor.fetchone()
if record:
    print("\n专家记录详情:")
    print(f"- ID: {record[0]}")
    print(f"- 姓名: {record[1]}")
    print(f"- 出生年月: {record[2]}")
    print(f"- 工作单位: {record[3]}")
    print(f"- 评分: {record[10]}")
    print(f"- 验证状态: {record[6]}")
    print(f"- 创建时间: {record[9]}")
else:
    print("\n未找到专家记录")

# 关闭数据库连接
conn.close() 