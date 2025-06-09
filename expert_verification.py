import pandas as pd
import requests
import json
import os
import time
from datetime import datetime
from config import Config
import re

class ExpertVerification:
    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.total_experts = 0
        self.verified_experts = 0
        self.results = []
        
        # 获取当前脚本所在目录
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 加载本地知识库
        self.knowledge_base = self.load_knowledge_base()
        
    def load_knowledge_base(self):
        """加载本地知识库Excel文件"""
        try:
            kb_path = os.path.join(self.base_dir, "本地知识库.xlsx")
            if os.path.exists(kb_path):
                print(f"找到本地知识库文件: {kb_path}")
                df = pd.read_excel(kb_path)
                print(f"成功加载本地知识库，包含 {len(df)} 条记录")
                return df
            print("未找到本地知识库文件")
            return pd.DataFrame()
        except Exception as e:
            print(f"加载本地知识库失败: {str(e)}")
            return pd.DataFrame()

    def get_knowledge_base_info(self, expert_name, affiliation):
        """从本地知识库获取专家信息"""
        if self.knowledge_base.empty:
            return {"school_info": None, "baike_info": None}
        
        # 同时匹配专家姓名和工作单位
        matched_records = self.knowledge_base[
            (self.knowledge_base['专家姓名'] == expert_name) & 
            (self.knowledge_base['工作单位'] == affiliation)
        ]
        
        if matched_records.empty:
            return {"school_info": None, "baike_info": None}
        
        school_info = None
        baike_info = None
        
        for _, record in matched_records.iterrows():
            source = record.get('信息来源', '')
            
            if source == '学校官网':
                school_info = {
                    "专家姓名": record.get('专家姓名', ''),
                    "出生年月": record.get('出生年月', ''),
                    "工作单位": record.get('工作单位', ''),
                    "职称职务": record.get('职称职务', ''),
                    "来源网址": record.get('来源网址', '')
                }
            elif source == '百度百科':
                baike_info = {
                    "专家姓名": record.get('专家姓名', ''),
                    "出生年月": record.get('出生年月', ''),
                    "工作单位": record.get('工作单位', ''),
                    "职称职务": record.get('职称职务', ''),
                    "来源网址": record.get('来源网址', '')
                }
        
        return {"school_info": school_info, "baike_info": baike_info}

    def query_qwen(self, name, affiliation, title):
        """调用千问API获取专家信息"""
        try:
            headers = {
                "Authorization": f"Bearer {Config.QWEN_API_KEY}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""请验证以下专家信息的真实性：
姓名：{name}
工作单位：{affiliation}
职称职务：{title}

请提供以下信息：
1. 专家基本信息（姓名、出生年月、工作单位、职称职务）
2. 是否存在负面舆情
3. 信息可信度评分（0-100分）

请以JSON格式返回，格式如下：
{{
    "basic_info": {{
        "name": "专家姓名",
        "birth_year": "出生年月",
        "affiliation": "工作单位",
        "title": "职称职务"
    }},
    "negative_news": ["负面舆情1", "负面舆情2"],
    "credibility_score": 85
}}"""

            data = {
                "model": "qwen-max",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            }
            
            response = requests.post(Config.QWEN_API_URL, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result.get('output', {}).get('text', '')
            
        except Exception as e:
            print(f"调用千问API失败: {str(e)}")
            return None

    def query_qwen_comprehensive(self, name, affiliation, title):
        """调用千问API查询专家综合信息（对齐背调python代码）"""
        try:
            headers = {
                "Authorization": f"Bearer {Config.QWEN_API_KEY}",
                "Content-Type": "application/json"
            }
            system_message = "你是一个专业的信息检索助手，请严格按照要求的格式返回信息。"
            user_prompt = f"""根据专家姓名\"{name}\"和工作单位\"{affiliation}\"搜索相关信息，不要受到职称职务\"{title}\"的限制，尽可能找到相关人员的真实信息，然后再与用户输入的信息进行比对。\n\n请严格按照以下格式返回结果：\n\n①基本信息：\n专家姓名：[根据搜索找到的姓名，不一定要与输入的完全一致]\n出生年月：[根据搜索找到的出生年月，如果不确定请写\"未知\"]\n工作单位：[根据搜索找到的工作单位，不一定要与输入的完全一致]\n职称职务：[尽可能详细地列出该专家的所有职称职务信息，包括但不限于：学术职称（如教授、副教授、研究员等）、行政职务（如院长、副院长、系主任、所长等）、学术兼职（如学会理事、期刊编委、评审专家等）、导师资格（如博士生导师、硕士生导师）、荣誉称号（如特聘教授、杰出人才等）。请用中文逗号分隔各项职务，力求信息完整]\n研究方向：[尽可能详细地列出该专家的主要研究领域、研究方向和专业特长，包括但不限于：学科分类（如材料科学、计算机科学、生物医学等）、具体研究方向（如人工智能、纳米材料、分子生物学等）、专业特长（如算法设计、材料合成、基因编辑等）。请用中文逗号分隔各项研究方向，力求信息全面准确]\n\n注意：\n- 提供的信息必须是通过搜索获取的真实信息，而不是简单复制用户输入\n- 如果搜索结果与用户输入不一致，请以搜索结果为准\n- 对于职称职务和研究方向信息，请特别注意搜索详细和全面，不要只提供简单的一两个词\n- 所有信息必须真实可靠，不得编造\n- 研究方向必须提供，这是非常重要的信息"""
            data = {
                "model": "qwen-plus-latest",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3
            }
            response = requests.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers=headers,
                json=data
            )
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content
            else:
                print(f"API调用失败，状态码: {response.status_code}，错误: {response.text}")
                return ""
        except Exception as e:
            print(f"调用AI API时出错: {str(e)}")
            return ""

    def parse_qwen_response(self, response_text):
        """解析AI返回的结构化信息"""
        try:
            basic_info = {"专家姓名": "", "出生年月": "", "工作单位": "", "职称职务": "", "研究方向": ""}
            lines = response_text.split('\n')
            current_section = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if "①基本信息" in line or "基本信息" in line:
                    current_section = "basic"
                elif current_section == "basic":
                    if "专家姓名" in line:
                        basic_info["专家姓名"] = line.split("：")[1].strip() if "：" in line else ""
                    elif "出生年月" in line:
                        basic_info["出生年月"] = line.split("：")[1].strip() if "：" in line else ""
                    elif "工作单位" in line:
                        basic_info["工作单位"] = line.split("：")[1].strip() if "：" in line else ""
                    elif "职称职务" in line:
                        basic_info["职称职务"] = line.split("：")[1].strip() if "：" in line else ""
                    elif "研究方向" in line:
                        basic_info["研究方向"] = line.split("：")[1].strip() if "：" in line else ""
            return {
                "basic_info": basic_info,
                "full_response": response_text
            }
        except Exception as e:
            print(f"解析AI响应时出错: {str(e)}")
            return {
                "basic_info": {"专家姓名": "", "出生年月": "", "工作单位": "", "职称职务": "", "研究方向": ""},
                "full_response": response_text
            }

    def compare_with_source(self, original_data, source_info, source_name):
        """比对原始数据与来源数据"""
        if not source_info:
            return {
                "name": "缺失",
                "birth_year": "缺失",
                "affiliation": "缺失",
                "title": "缺失",
                "basic_info": None
            }
        result = {}
        
        def format_date_for_display(date_str):
            """格式化日期用于显示"""
            if not date_str:
                return ""
            date_str = str(date_str).strip()
            
            # 移除末尾的.0
            if isinstance(date_str, (int, float)):
                date_str = str(int(date_str))
            elif date_str.endswith('.0'):
                date_str = date_str[:-2]
            
            # 处理8位数字格式
            if len(date_str) == 8 and date_str.isdigit():
                try:
                    date = datetime.strptime(date_str, '%Y%m%d')
                    return date.strftime('%Y-%m-%d')
                except ValueError:
                    pass
            
            # 处理年月格式
            if re.match(r'^\d{4}年\d{1,2}月$', date_str):
                return date_str
                
            # 如果是纯年份，加上"年"
            if len(date_str) == 4 and date_str.isdigit():
                return f"{date_str}年"
                
            return date_str

        def normalize_date(date_str):
            """标准化日期格式用于比较"""
            if not date_str:
                return ""
            date_str = str(date_str).strip()
            
            # 移除末尾的.0
            if isinstance(date_str, (int, float)):
                date_str = str(int(date_str))
            elif date_str.endswith('.0'):
                date_str = date_str[:-2]
            
            # 处理年份格式（如：1964年8月）
            year_month_match = re.search(r'(\d{4})年(\d{1,2})月', date_str)
            if year_month_match:
                year = year_month_match.group(1)
                month = year_month_match.group(2).zfill(2)
                return f"{year}{month}"
            
            # 尝试提取年份
            year_match = re.search(r'19\d{2}|20\d{2}', date_str)
            if not year_match:
                return date_str
            
            year = year_match.group()
            # 如果只有年份，直接返回
            if len(date_str) == 4:
                return year
            
            # 处理标准日期格式（如：1947-12-17）
            if '-' in date_str:
                try:
                    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                    return parsed_date.strftime('%Y%m%d')
                except ValueError:
                    pass
            
            # 处理8位数字格式（如：19471217）
            if len(date_str) == 8 and date_str.isdigit():
                try:
                    datetime.strptime(date_str, '%Y%m%d')
                    return date_str
                except ValueError:
                    pass
            
            return year

        def compare_dates(date1, date2):
            """比较两个日期是否匹配"""
            if not date1 or not date2:
                return False
            
            # 标准化处理
            date1 = normalize_date(str(date1).strip())
            date2 = normalize_date(str(date2).strip())
            
            # 提取年份
            year1 = re.search(r'19\d{2}|20\d{2}', str(date1))
            year2 = re.search(r'19\d{2}|20\d{2}', str(date2))
            
            if not year1 or not year2:
                return False
            
            year1 = year1.group()
            year2 = year2.group()
            
            # 如果只有年份，直接比较年份
            if len(date1) == 4 or len(date2) == 4:
                return year1 == year2
            
            # 如果年份不同，直接不匹配
            if year1 != year2:
                return False
            
            # 如果年份相同，且其中一个只有年份，认为匹配
            if len(date1) == 4 or len(date2) == 4:
                return True
            
            # 标准化后比较完整日期
            return date1 == date2

        # 比对姓名
        result["name"] = "一致" if original_data["专家姓名"] == source_info["专家姓名"] else "不一致"
        if result["name"] == "不一致":
            result["name_input"] = original_data["专家姓名"]
            result["name_source"] = source_info["专家姓名"]

        # 比对出生年月
        original_date = original_data.get("出生年月", "")
        source_date = source_info.get("出生年月", "")
        
        result["birth_year"] = "一致" if compare_dates(original_date, source_date) else "不一致"
        if result["birth_year"] == "不一致":
            result["birth_year_input"] = format_date_for_display(original_date)
            result["birth_year_source"] = format_date_for_display(source_date)

        # 比对工作单位 - 修改为部分匹配
        original_affiliation = original_data["工作单位"].strip()
        source_affiliation = source_info["工作单位"].strip()
        
        # 检查是否部分匹配
        if original_affiliation and source_affiliation:
            # 检查一方是否包含另一方
            if original_affiliation in source_affiliation or source_affiliation in original_affiliation:
                result["affiliation"] = "一致"
            else:
                result["affiliation"] = "不一致"
        else:
            result["affiliation"] = "不一致"
            
        if result["affiliation"] == "不一致":
            result["affiliation_input"] = original_data["工作单位"]
            result["affiliation_source"] = source_info["工作单位"]

        # 职称职务关键词比对 - 修改为只要有一个关键词匹配就算一致
        original_title = original_data.get("职称职务", "").lower()
        source_title = source_info.get("职称职务", "").lower()
        if original_title and source_title:
            original_keywords = set([x.strip() for x in re.split(r'[，,、\s]', original_title) if x.strip()])
            source_keywords = set([x.strip() for x in re.split(r'[，,、\s]', source_title) if x.strip()])
            
            # 检查是否有任何一个关键词匹配
            is_match = False
            for orig_keyword in original_keywords:
                for source_keyword in source_keywords:
                    if orig_keyword in source_keyword or source_keyword in orig_keyword:
                        is_match = True
                        break
                if is_match:
                    break
                    
            result["title"] = "一致" if is_match else "不一致"
        else:
            result["title"] = "不一致"
        if result["title"] == "不一致":
            result["title_input"] = original_data.get("职称职务", "")
            result["title_source"] = source_info.get("职称职务", "")
            
        # 保存原始信息
        result["basic_info"] = source_info

        return result

    def calculate_score(self, school_comparison, baike_comparison, qwen_comparison):
        """计算综合评分，并给出可信度类型"""
        basic_weights = Config.BASIC_SCORE_WEIGHTS
        
        def get_source_score(comparison):
            if not comparison:
                return 0
            score = 0
            
            # 修改评分逻辑：姓名和工作单位必须同时一致才得分
            name_match = comparison.get("name") == "一致"
            affiliation_match = comparison.get("affiliation") == "一致"
            
            # 只有当姓名和工作单位都一致时，才计算姓名和工作单位的分数
            if name_match and affiliation_match:
                score += basic_weights["name"] * 100  # 姓名分数
                score += basic_weights["affiliation"] * 100  # 工作单位分数
            
            # 其他字段正常计算
            if comparison.get("birth_year") == "一致":
                score += basic_weights["birth_year"] * 100
                
            if comparison.get("title") == "一致":
                score += basic_weights["title"] * 100
                
            return score
            
        # 获取各来源的分数
        school_score = get_source_score(school_comparison)
        baike_score = get_source_score(baike_comparison)
        qwen_score = get_source_score(qwen_comparison)
        
        # 新的评分逻辑
        total_score = 0
        
        # 标记各来源是否有效
        has_school_info = school_comparison and school_comparison.get("name") != "缺失" and school_comparison.get("affiliation") != "缺失"
        has_baike_info = baike_comparison and baike_comparison.get("name") != "缺失" and baike_comparison.get("affiliation") != "缺失"
        has_qwen_info = qwen_comparison and qwen_comparison.get("name") != "缺失" and qwen_comparison.get("affiliation") != "缺失"
        
        # 1. 如果官网信息存在，则只使用官网信息作为总分
        if has_school_info:
            total_score = school_score
            # 标记AI和百科为无效，不参与评分
            has_baike_info = False
            has_qwen_info = False
        # 2. 如果官网信息缺失，百科和AI都有信息
        elif has_baike_info and has_qwen_info:
            # 使用AI(70%)和百科(30%)的权重
            total_score = qwen_score * 0.7 + baike_score * 0.3
        # 3. 如果官网和百科缺失，只有AI有信息
        elif has_qwen_info:
            # AI权重为100%
            total_score = qwen_score
        # 4. 如果所有信息都缺失
        else:
            total_score = 0
        
        # 结果类型
        if total_score >= 80:
            result_type = "可信"
        elif total_score >= 60:
            result_type = "质疑"
        else:
            result_type = "不可信"
            
        return {
            "total_score": round(total_score, 2),
            "school_score": round(school_score, 2) if has_school_info else None,
            "baike_score": round(baike_score, 2) if has_baike_info and not has_school_info else None,
            "qwen_score": round(qwen_score, 2) if has_qwen_info and not has_school_info else None,
            "result_type": result_type,
            "has_school_info": has_school_info,
            "has_baike_info": has_baike_info and not has_school_info,
            "has_qwen_info": has_qwen_info and not has_school_info
        }

    def verify_expert(self, expert_data):
        """验证单个专家信息（对齐背调python代码）"""
        try:
            kb_info = self.get_knowledge_base_info(
                expert_data["专家姓名"],
                expert_data["工作单位"]
            )
            qwen_response = self.query_qwen_comprehensive(
                expert_data["专家姓名"],
                expert_data["工作单位"],
                expert_data["职称职务"]
            )
            qwen_info = self.parse_qwen_response(qwen_response) if qwen_response else None
            school_comparison = self.compare_with_source(expert_data, kb_info["school_info"], "学校官网")
            baike_comparison = self.compare_with_source(expert_data, kb_info["baike_info"], "百度百科")
            qwen_comparison = self.compare_with_source(expert_data, qwen_info["basic_info"] if qwen_info else None, "AI搜索")
            scores = self.calculate_score(school_comparison, baike_comparison, qwen_comparison)
            result = {
                "expert_data": expert_data,
                "comparisons": {
                    "school": school_comparison,
                    "baike": baike_comparison,
                    "qwen": qwen_comparison
                },
                "scores": scores,
                "ai_info": qwen_info["full_response"] if qwen_info else "",
                "negative_news": []  # 添加空的负面舆情列表
            }
            return result
        except Exception as e:
            print(f"验证专家信息失败: {str(e)}")
            return None

    def process_batch(self, file_path):
        """处理批量验证，兼容专家信息表字段，容错处理，确保每条都能调用千问API"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            self.total_experts = len(df)
            self.verified_experts = 0
            self.results = []
            # 字段兼容处理
            expected_cols = ["专家姓名", "出生年月", "工作单位", "工作单位统一社会信用代码", "职称职务"]
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ""
            # 处理每个专家
            for _, row in df.iterrows():
                expert_data = {
                    "专家姓名": row.get("专家姓名", ""),
                    "出生年月": row.get("出生年月", ""),
                    "工作单位": row.get("工作单位", ""),
                    "工作单位统一社会信用代码": row.get("工作单位统一社会信用代码", ""),
                    "职称职务": row.get("职称职务", "")
                }
                # 跳过无姓名的行
                if not expert_data["专家姓名"]:
                    continue
                result = self.verify_expert(expert_data)
                if result:
                    self.results.append(result)
                self.verified_experts += 1
                if self.progress_callback:
                    self.progress_callback(self.verified_experts, self.total_experts)
            return self.results
        except Exception as e:
            print(f"批量验证失败: {str(e)}")
            return None 