#!/usr/bin/env python3
"""
Case Analyzer MCP Server - 工单分析服务器

这个服务器分析工单情况，支持按Category、Account PayerId、Service等维度进行统计分析。
支持Tools、Resources和Prompts三种MCP类型。
"""

import csv
import os
import re
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# 尝试导入pandas用于Excel处理
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("警告: pandas未安装，客户名称映射功能将不可用")

# 数据根目录路径 - 从环境变量获取，避免硬编码敏感路径
DATA_ROOT_DIR = os.getenv('CASE_DATA_DIR', os.path.expanduser('~/case-data'))

# 客户映射表路径
CUSTOMER_MAPPING_FILE = os.getenv('CUSTOMER_MAPPING_FILE', '/path/to/customer/mapping.xlsx')

def load_customer_mapping():
    """
    加载客户名称映射表
    
    Returns:
        Dict: PayerID -> 客户名称的映射字典
    """
    if not PANDAS_AVAILABLE:
        return {}
        
    try:
        if os.path.exists(CUSTOMER_MAPPING_FILE):
            df = pd.read_excel(CUSTOMER_MAPPING_FILE)
            
            # 创建映射字典
            mapping = {}
            for _, row in df.iterrows():
                # 使用Payer列而不是PayerID列
                payer_id = str(int(row['Payer'])) if pd.notna(row['Payer']) else None
                customer_name = row['客户'] if pd.notna(row['客户']) else None
                
                if payer_id and customer_name:
                    # 清理客户名称中的换行符和多余空格
                    customer_name = customer_name.replace('\n', '/').strip()
                    mapping[payer_id] = customer_name
            
            print(f"成功加载客户映射表，包含 {len(mapping)} 个映射关系")
            return mapping
        else:
            print(f"客户映射文件不存在: {CUSTOMER_MAPPING_FILE}")
            return {}
    except Exception as e:
        print(f"加载客户映射表时出错: {e}")
        return {}

def format_customer_display(payer_id, customer_mapping=None):
    """
    格式化客户显示名称
    
    Args:
        payer_id: 付费账户ID
        customer_mapping: 客户映射字典
        
    Returns:
        格式化的显示名称
    """
    if customer_mapping and payer_id in customer_mapping:
        customer_name = customer_mapping[payer_id]
        return f"客户: {customer_name}，账户ID: {payer_id}"
    else:
        return f"账户ID: {payer_id}"

# 创建FastMCP服务器实例
mcp = FastMCP(
    "case-analyzer",
    instructions="""
    # 工单分析服务器 - 专业的技术支持工单数据分析工具

    这个服务器专门用于分析技术支持工单数据，支持按月份、类别、付费账户、服务等多个维度进行深度分析。

    ## 🎯 核心能力

    当用户询问以下内容时，应该使用此服务器：
    - **工单相关问题**: "工单情况"、"工单分析"、"工单统计"、"case分析"
    - **月份分析**: "7月份工单"、"202507工单"、"某月工单情况"
    - **类别分析**: "工单类别分布"、"技术支持工单"、"账单工单"
    - **账户分析**: "付费账户工单"、"payer工单分布"、"账户支持情况"
    - **服务分析**: "服务工单"、"服务问题分析"、"哪个服务工单最多"
    - **General Guidance**: "指导类工单"、"General Guidance统计"
    - **综合报告**: "工单报告"、"综合分析"、"整体情况"
    - **美化表格**: "所有付费账户工单详细情况"、"详细表格"、"美化表格"

    ## 🛠️ 可用工具 (Tools)

    ### 智能分析工具
    - `analyze_monthly_cases`: 智能分析工具，自动从用户查询中提取月份和表格需求
      - 支持自然语言查询如"2025年7月份所有付费账户工单详细情况"
      - 自动识别是否需要美化表格展示
      - 自动提取月份信息并选择合适的分析方式

    ### 基础查询工具
    - `get_available_months_tool`: 获取数据目录下所有可用的月份列表
    
    ### 核心分析工具 (所有工具都支持按月份筛选)
    - `analyze_cases_by_category`: 按工单类别(Technical support、Account billing等)统计分析
    - `analyze_cases_by_payer`: 按付费账户ID分析工单分布和技术支持比例
    - `analyze_cases_by_service`: 按服务分析工单数量和类型
    - `analyze_general_guidance_cases`: 专门统计General Guidance类型的工单
    - `get_comprehensive_case_analysis`: 生成包含所有维度的综合分析报告

    ### 表格展示工具
    - `get_payer_accounts_beautiful_table`: 生成美化的markdown表格，专门用于"所有付费账户工单详细情况"类查询
    - `analyze_payer_accounts_table`: 以表格形式展示付费账户工单分布分析

    ## 📊 典型使用场景

    **美化表格场景** (推荐使用 analyze_monthly_cases):
    - "2025年7月份所有付费账户工单详细情况" → 自动使用美化表格展示
    - "所有付费账户工单详细表格" → 自动使用美化表格展示
    - "客户工单详细情况" → 自动使用美化表格展示

    **月份分析场景**:
    - "7月份工单情况" → 使用 analyze_monthly_cases(query)
    - "2025年7月的工单分析" → 使用 analyze_monthly_cases(query)
    
    **类别分析场景**:
    - "工单类别分布" → 使用 analyze_cases_by_category(data_dir)
    - "技术支持工单占比" → 使用 analyze_cases_by_category(data_dir)
    
    **账户分析场景**:
    - "哪个账户工单最多" → 使用 analyze_cases_by_payer(data_dir)
    - "付费账户支持情况" → 使用 analyze_cases_by_payer(data_dir)
    
    **服务分析场景**:
    - "服务工单分布" → 使用 analyze_cases_by_service(data_dir)
    - "哪个服务问题最多" → 使用 analyze_cases_by_service(data_dir)

    ## 🎨 表格格式说明

    ### 美化表格格式 (get_payer_accounts_beautiful_table)
    返回标准的markdown表格格式：
    ```
    ## 202507月份所有付费账户工单详细情况

    | 客户名称 | 账户ID | 总工单数 | 技术支持 | 非技术支持 | 技术占比 |
    |----------|--------|----------|----------|------------|----------|
    | 客户A    | 123456 | 15       | 12       | 3          | 80.0%    |
    | 客户B    | 789012 | 8        | 5        | 3          | 62.5%    |
    ```

    包含统计摘要、数据来源等完整信息，适合直接展示给用户。

    ## 🔧 参数说明

    - `data_dir`: 工单数据目录路径 (通过环境变量CASE_DATA_DIR设置)
    - `month`: 可选月份参数，支持格式:
      - 空字符串 "" = 分析所有月份
      - "202507" = 分析2025年7月
      - "2025-07" = 分析2025年7月
    - `query`: 用户的自然语言查询文本，用于智能分析工具

    ## 📁 数据文件格式

    支持标准的工单CSV文件，文件名格式: cases-YYYYMM.csv
    必需字段: Case ID, Category (C), Account PayerId, Type (T), Item (I), Resolver, Subject等

    ## 🎯 智能识别关键词

    以下关键词应该触发使用此服务器:
    工单、case、支持、support、技术支持、账单、billing、服务、payer、付费账户、
    General Guidance、月份分析、类别分布、服务分析、综合报告、统计分析、
    详细情况、详细表格、美化表格、所有付费账户工单详细情况
    """
)

def load_case_data(data_dir: str, month: str = "") -> List[Dict]:
    """
    加载指定目录下的工单CSV文件
    
    Args:
        data_dir: 数据目录路径
        month: 可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空加载所有文件
        
    Returns:
        包含工单数据的列表
    """
    all_cases = []
    
    if not os.path.exists(data_dir):
        return all_cases
    
    # 如果指定了月份，只加载对应月份的文件
    if month and month.strip():
        # 标准化月份格式为YYYYMM
        month = month.strip()
        if '-' in month:
            month = month.replace('-', '')
        
        target_filename = f"cases-{month}.csv"
        file_path = os.path.join(data_dir, target_filename)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        row['_source_file'] = target_filename
                        all_cases.append(row)
            except Exception as e:
                print(f"Error reading {target_filename}: {e}")
        else:
            print(f"File not found: {target_filename}")
    else:
        # 查找所有符合格式的CSV文件
        for filename in os.listdir(data_dir):
            if filename.startswith('cases-') and filename.endswith('.csv'):
                file_path = os.path.join(data_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # 添加文件来源信息
                            row['_source_file'] = filename
                            all_cases.append(row)
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    continue
    
    return all_cases

def get_available_months(data_dir: str) -> List[str]:
    """
    获取数据目录下所有可用的月份
    
    Args:
        data_dir: 数据目录路径
        
    Returns:
        可用月份列表，格式为YYYYMM
    """
    months = []
    
    if not os.path.exists(data_dir):
        return months
    
    for filename in os.listdir(data_dir):
        if filename.startswith('cases-') and filename.endswith('.csv'):
            # 提取月份信息
            match = re.search(r'cases-(\d{6})\.csv', filename)
            if match:
                months.append(match.group(1))
    
    return sorted(months)

def extract_month_from_text(text: str) -> str:
    """
    从自然语言文本中提取月份信息
    
    Args:
        text: 用户输入的文本
        
    Returns:
        提取的月份，格式为YYYYMM，如果未找到则返回空字符串
    """
    import re
    from datetime import datetime
    
    # 当前年份
    current_year = datetime.now().year
    
    # 匹配模式
    patterns = [
        r'(\d{4})[年\-]?(\d{1,2})[月份]?',  # 2025年7月, 2025-07
        r'(\d{6})',  # 202507
        r'(\d{1,2})[月份]',  # 7月, 7月份
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.group(1)) == 6:  # 202507格式
                return match.group(1)
            elif len(match.group(1)) == 4:  # 2025年7月格式
                year = match.group(1)
                month = match.group(2).zfill(2)
                return f"{year}{month}"
            elif len(match.group(1)) <= 2:  # 7月格式
                month = match.group(1).zfill(2)
                return f"{current_year}{month}"
    
    return ""

@mcp.tool()
def analyze_monthly_cases(query: str = Field(description="用户的查询文本，如'7月份工单情况'、'分析2025年7月的工单'")) -> Dict:
    """
    智能分析月份工单情况 - 从用户查询中自动提取月份信息
    
    当用户询问以下问题时使用此工具：
    - "7月份工单情况"
    - "分析2025年7月的工单"
    - "202507工单分析"
    - "7月工单类别分布"
    - "工单综合分析"
    - "2025年7月份所有付费账户工单详细情况"
    
    这个工具会自动从用户查询中提取月份信息，然后进行综合分析。
    如果查询中包含"详细情况"、"表格"、"表"等关键词，会优先使用美化表格展示。
    
    Args:
        query: 用户的查询文本
        
    Returns:
        基于提取月份的综合工单分析报告
    """
    # 从查询中提取月份
    month = extract_month_from_text(query)
    
    # 检查是否需要美化表格展示
    beautiful_table_keywords = ["详细情况", "详细表格", "美化表格", "所有付费账户工单详细情况"]
    needs_beautiful_table = any(keyword in query for keyword in beautiful_table_keywords)
    
    # 检查是否需要表格式展示
    table_keywords = ["表格", "表", "分层", "客户分层", "大客户", "中等客户", "小客户"]
    needs_table = any(keyword in query for keyword in table_keywords)
    
    # 检查是否专门询问付费账户
    payer_keywords = ["付费账户", "payer", "账户分布", "客户分布"]
    is_payer_query = any(keyword in query for keyword in payer_keywords)
    
    if needs_beautiful_table and is_payer_query:
        # 使用美化表格式付费账户分析
        result = get_payer_accounts_beautiful_table(month)
        result["extracted_month"] = month if month else "all"
        result["original_query"] = query
        result["analysis_type"] = "beautiful_table_payer_analysis"
        return result
    elif needs_table and is_payer_query:
        # 使用表格式付费账户分析
        result = analyze_payer_accounts_table(month)
        result["extracted_month"] = month if month else "all"
        result["original_query"] = query
        result["analysis_type"] = "table_payer_analysis"
        return result
    elif is_payer_query:
        # 使用详细付费账户分析
        result = analyze_cases_by_payer(month)
        result["extracted_month"] = month if month else "all"
        result["original_query"] = query
        result["analysis_type"] = "detailed_payer_analysis"
        return result
    else:
        # 使用综合分析
        result = get_comprehensive_case_analysis(month)
        result["extracted_month"] = month if month else "all"
        result["original_query"] = query
        result["analysis_type"] = "comprehensive_analysis"
        return result

@mcp.tool()
def get_available_months_tool() -> Dict:
    """
    获取工单数据目录下所有可用的月份列表
    
    当用户询问"有哪些月份的工单数据"、"可以分析哪些月份"时使用此工具。
    数据目录路径自动从环境变量CASE_DATA_DIR获取。
        
    Returns:
        可用月份列表和详细信息，包括文件名和格式化日期
    """
    data_dir = DATA_ROOT_DIR
    months = get_available_months(data_dir)
    
    if not months:
        return {"error": f"未找到工单数据文件在目录: {data_dir}"}
    
    # 格式化月份信息
    month_info = []
    for month in months:
        year = month[:4]
        mon = month[4:]
        formatted = f"{year}-{mon}"
        month_info.append({
            "month_code": month,
            "formatted": formatted,
            "filename": f"cases-{month}.csv"
        })
    
    return {
        "available_months": month_info,
        "total_months": len(months),
        "date_range": f"{months[0]} to {months[-1]}" if months else "",
        "data_directory": data_dir,
        "summary": f"找到 {len(months)} 个月份的工单数据文件"
    }
@mcp.tool()
def analyze_cases_by_category(month: str = Field(default="", description="可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份")) -> Dict:
    """
    按工单类别(Category)统计分析工单数量和分布情况
    
    当用户询问以下问题时使用此工具：
    - "工单类别分布"、"工单分类情况"
    - "技术支持工单有多少"、"账单工单占比"
    - "Technical support和其他类型工单比例"
    
    数据目录路径自动从环境变量CASE_DATA_DIR获取。
    
    Args:
        month: 可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)
        
    Returns:
        按类别统计的工单数量、百分比和分析范围
    """
    data_dir = DATA_ROOT_DIR
    cases = load_case_data(data_dir, month)
    
    if not cases:
        month_info = f" (月份: {month})" if month else ""
        return {"error": f"未找到工单数据文件在目录: {data_dir}{month_info}"}
    
    category_stats = Counter()
    total_cases = len(cases)
    
    for case in cases:
        category = case.get('Category (C)', '').strip()
        if category:
            category_stats[category] += 1
    
    # 计算百分比
    category_analysis = {}
    for category, count in category_stats.most_common():
        percentage = (count / total_cases) * 100 if total_cases > 0 else 0
        category_analysis[category] = {
            "count": count,
            "percentage": round(percentage, 2)
        }
    
    analysis_scope = f"月份 {month} 的" if month else "所有"
    source_files = list(set(case.get('_source_file', '') for case in cases))
    
    return {
        "total_cases": total_cases,
        "categories": category_analysis,
        "analysis_scope": analysis_scope,
        "source_files": source_files,
        "summary": f"共分析了{analysis_scope} {total_cases} 个工单，涵盖 {len(category_stats)} 个不同类别"
    }

@mcp.tool()
def get_payer_accounts_beautiful_table(month: str = Field(default="", description="可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份")) -> Dict:
    """
    生成美化的付费账户工单分布表格，专门用于"所有付费账户工单详细情况"类查询
    
    当用户询问以下问题时使用此工具：
    - "2025年7月份所有付费账户工单详细情况"
    - "所有付费账户工单分布表格"
    - "付费账户工单统计表"
    - "客户工单详细表格"
    
    返回标准的markdown表格格式，包含客户名称、账户ID、总工单数、技术支持、非技术支持、技术占比等信息。
    
    Args:
        month: 可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份
        
    Returns:
        美化的markdown表格格式的付费账户工单分布分析
    """
    data_dir = DATA_ROOT_DIR
    cases = load_case_data(data_dir, month)
    
    if not cases:
        month_info = f" (月份: {month})" if month and month.strip() else ""
        return {"error": f"未找到工单数据文件在目录: {data_dir}{month_info}"}
    
    # 加载客户映射表
    customer_mapping = load_customer_mapping()
    
    # 统计每个payer的工单情况
    payer_stats = defaultdict(lambda: {
        "total_cases": 0,
        "technical_support": 0,
        "non_technical_support": 0,
        "categories": set()
    })
    
    for case in cases:
        payer_id = case.get('Account PayerId', '').strip()
        category = case.get('Category (C)', '').strip()
        
        if payer_id:
            payer_stats[payer_id]["total_cases"] += 1
            payer_stats[payer_id]["categories"].add(category)
            
            if category.lower() == "technical support":
                payer_stats[payer_id]["technical_support"] += 1
            else:
                payer_stats[payer_id]["non_technical_support"] += 1
    
    # 准备表格数据
    table_data = []
    for payer_id, stats in payer_stats.items():
        tech_percentage = (stats["technical_support"] / stats["total_cases"]) * 100 if stats["total_cases"] > 0 else 0
        
        # 获取客户名称
        if customer_mapping and payer_id in customer_mapping:
            customer_name = customer_mapping[payer_id]
        else:
            customer_name = "未知客户"
        
        table_data.append({
            "customer_name": customer_name,
            "account_id": payer_id,
            "total_cases": stats["total_cases"],
            "tech_support": stats["technical_support"],
            "non_tech": stats["non_technical_support"],
            "tech_percentage": tech_percentage
        })
    
    # 按工单数量排序
    table_data.sort(key=lambda x: x["total_cases"], reverse=True)
    
    # 生成美化的markdown表格
    table_lines = []
    
    # 表格标题
    analysis_scope = f"{month}月份" if month and month.strip() else "全部"
    table_lines.append(f"## {analysis_scope}所有付费账户工单详细情况")
    table_lines.append("")
    
    # 表格头部
    header = "| 客户名称 | 账户ID | 总工单数 | 技术支持 | 非技术支持 | 技术占比 |"
    separator = "|----------|--------|----------|----------|------------|----------|"
    table_lines.append(header)
    table_lines.append(separator)
    
    # 表格内容
    for row in table_data:
        line = f"| {row['customer_name']} | {row['account_id']} | {row['total_cases']} | {row['tech_support']} | {row['non_tech']} | {row['tech_percentage']:.1f}% |"
        table_lines.append(line)
    
    # 添加统计摘要
    table_lines.append("")
    table_lines.append("### 统计摘要")
    table_lines.append("")
    
    total_payers = len(payer_stats)
    total_cases = sum(stats["total_cases"] for stats in payer_stats.values())
    total_tech = sum(stats["technical_support"] for stats in payer_stats.values())
    total_non_tech = sum(stats["non_technical_support"] for stats in payer_stats.values())
    overall_tech_percentage = (total_tech / total_cases) * 100 if total_cases > 0 else 0
    
    mapped_customers = sum(1 for row in table_data if customer_mapping and row['account_id'] in customer_mapping)
    
    summary_lines = [
        f"- **总付费账户数**: {total_payers}",
        f"- **总工单数**: {total_cases}",
        f"- **技术支持工单**: {total_tech} ({overall_tech_percentage:.1f}%)",
        f"- **非技术支持工单**: {total_non_tech} ({100-overall_tech_percentage:.1f}%)",
        f"- **客户名称映射覆盖率**: {mapped_customers}/{total_payers} ({mapped_customers/total_payers*100:.1f}%)" if total_payers > 0 else "- **客户名称映射覆盖率**: 0/0 (0%)",
        f"- **平均每账户工单数**: {total_cases/total_payers:.1f}" if total_payers > 0 else "- **平均每账户工单数**: 0"
    ]
    
    table_lines.extend(summary_lines)
    
    # 添加数据来源信息
    source_files = list(set(case.get('_source_file', '') for case in cases))
    table_lines.append("")
    table_lines.append("### 数据来源")
    table_lines.append("")
    for file in source_files:
        table_lines.append(f"- {file}")
    
    beautiful_table = "\n".join(table_lines)
    
    return {
        "beautiful_table": beautiful_table,
        "table_format": "markdown",
        "total_accounts": total_payers,
        "total_cases": total_cases,
        "analysis_period": analysis_scope,
        "customer_mapping_rate": f"{mapped_customers/total_payers*100:.1f}%" if total_payers > 0 else "0%",
        "tech_support_rate": f"{overall_tech_percentage:.1f}%",
        "summary": f"生成了{analysis_scope}的付费账户工单详细表格，包含{total_payers}个账户的{total_cases}个工单信息，客户名称映射覆盖率{mapped_customers/total_payers*100:.1f}%。"
    }

@mcp.tool()
def analyze_payer_accounts_table(month: str = Field(default="", description="可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份")) -> Dict:
    """
    以表格形式展示付费账户工单分布分析，支持客户名称映射
    
    当用户询问以下问题时使用此工具：
    - "付费账户工单分布表格"
    - "账户工单统计表"
    - "客户分层分析"
    - "大客户工单情况"
    
    数据目录路径自动从环境变量CASE_DATA_DIR获取。
    如果提供了客户映射文件，会显示客户名称而不是只显示账户ID。
    
    Args:
        month: 可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份
        
    Returns:
        表格式的付费账户工单分布分析，包含客户名称映射
    """
    data_dir = DATA_ROOT_DIR
    cases = load_case_data(data_dir, month)
    
    if not cases:
        month_info = f" (月份: {month})" if month and month.strip() else ""
        return {"error": f"未找到工单数据文件在目录: {data_dir}{month_info}"}
    
    # 加载客户映射表
    customer_mapping = load_customer_mapping()
    
    # 统计每个payer的工单情况
    payer_stats = defaultdict(lambda: {
        "total_cases": 0,
        "technical_support": 0,
        "non_technical_support": 0,
        "categories": set()
    })
    
    for case in cases:
        payer_id = case.get('Account PayerId', '').strip()
        category = case.get('Category (C)', '').strip()
        
        if payer_id:
            payer_stats[payer_id]["total_cases"] += 1
            payer_stats[payer_id]["categories"].add(category)
            
            if category.lower() == "technical support":
                payer_stats[payer_id]["technical_support"] += 1
            else:
                payer_stats[payer_id]["non_technical_support"] += 1
    
    # 按工单数量分层并生成表格
    large_customers = []  # ≥10工单
    medium_customers = []  # 3-9工单
    small_customers = []  # 1-2工单
    
    for payer_id, stats in payer_stats.items():
        tech_percentage = (stats["technical_support"] / stats["total_cases"]) * 100 if stats["total_cases"] > 0 else 0
        
        customer_data = {
            "payer_id": payer_id,
            "display_name": format_customer_display(payer_id, customer_mapping),
            "total_cases": stats["total_cases"],
            "tech_support": stats["technical_support"],
            "non_tech": stats["non_technical_support"],
            "tech_percentage": tech_percentage
        }
        
        if stats["total_cases"] >= 10:
            large_customers.append(customer_data)
        elif stats["total_cases"] >= 3:
            medium_customers.append(customer_data)
        else:
            small_customers.append(customer_data)
    
    # 按工单数量排序
    large_customers.sort(key=lambda x: x["total_cases"], reverse=True)
    medium_customers.sort(key=lambda x: x["total_cases"], reverse=True)
    small_customers.sort(key=lambda x: x["total_cases"], reverse=True)
    
    # 生成美化的表格式展示
    def format_customer_table(customers, title):
        if not customers:
            return f"{title}\n(无)"
        
        table_lines = [title]
        table_lines.append("")  # 空行分隔
        
        # 表格头部
        header = "| 客户名称 | 账户ID | 总工单数 | 技术支持 | 非技术支持 | 技术占比 |"
        separator = "|----------|--------|----------|----------|------------|----------|"
        table_lines.append(header)
        table_lines.append(separator)
        
        # 表格内容
        for customer in customers:
            # 提取客户名称和账户ID
            if customer_mapping and customer['payer_id'] in customer_mapping:
                customer_name = customer_mapping[customer['payer_id']]
                account_id = customer['payer_id']
            else:
                customer_name = "未知客户"
                account_id = customer['payer_id']
            
            # 格式化表格行
            row = f"| {customer_name:<8} | {account_id:<6} | {customer['total_cases']:<8} | {customer['tech_support']:<8} | {customer['non_tech']:<10} | {customer['tech_percentage']:.1f}% |"
            table_lines.append(row)
        
        return "\n".join(table_lines)
    
    table_sections = []
    if large_customers:
        table_sections.append(format_customer_table(large_customers, "### 🔥 大客户 (≥10工单)"))
    if medium_customers:
        table_sections.append(format_customer_table(medium_customers, "### 🎯 中等客户 (3-9工单)"))
    if small_customers:
        table_sections.append(format_customer_table(small_customers, "### 📱 小客户 (1-2工单)"))
    
    formatted_table = "\n\n".join(table_sections)
    
    # 统计摘要
    total_payers = len(payer_stats)
    total_cases = sum(stats["total_cases"] for stats in payer_stats.values())
    large_cases = sum(c["total_cases"] for c in large_customers)
    medium_cases = sum(c["total_cases"] for c in medium_customers)
    small_cases = sum(c["total_cases"] for c in small_customers)
    
    analysis_scope = f"月份 {month} 的" if month and month.strip() else "所有"
    source_files = list(set(case.get('_source_file', '') for case in cases))
    
    # 统计映射情况
    mapped_customers = sum(1 for c in large_customers + medium_customers + small_customers 
                          if customer_mapping and c['payer_id'] in customer_mapping)
    
    return {
        "table_display": formatted_table,
        "summary_stats": {
            "total_payers": total_payers,
            "total_cases": total_cases,
            "analysis_scope": analysis_scope,
            "customer_segments": {
                "large_customers": f"{len(large_customers)}个账户，{large_cases}个工单 ({large_cases/total_cases*100:.1f}%)" if total_cases > 0 else "0个账户，0个工单",
                "medium_customers": f"{len(medium_customers)}个账户，{medium_cases}个工单 ({medium_cases/total_cases*100:.1f}%)" if total_cases > 0 else "0个账户，0个工单",
                "small_customers": f"{len(small_customers)}个账户，{small_cases}个工单 ({small_cases/total_cases*100:.1f}%)" if total_cases > 0 else "0个账户，0个工单"
            },
            "customer_mapping": {
                "total_mapped": mapped_customers,
                "total_unmapped": total_payers - mapped_customers,
                "mapping_rate": f"{mapped_customers/total_payers*100:.1f}%" if total_payers > 0 else "0%",
                "mapping_file": CUSTOMER_MAPPING_FILE if customer_mapping else "未提供"
            }
        },
        "key_insights": {
            "客户集中度": f"前{len(large_customers)}个大客户贡献了{large_cases/total_cases*100:.1f}%的工单" if total_cases > 0 and large_customers else "无大客户",
            "平均工单数": f"{total_cases/total_payers:.1f}个/账户" if total_payers > 0 else "0",
            "最活跃账户": large_customers[0]["display_name"] if large_customers else (medium_customers[0]["display_name"] if medium_customers else "无"),
            "客户映射覆盖率": f"{mapped_customers}/{total_payers} ({mapped_customers/total_payers*100:.1f}%)" if total_payers > 0 else "0/0 (0%)"
        },
        "source_files": source_files,
        "summary": f"共分析了{analysis_scope} {total_payers} 个付费账户的 {total_cases} 个工单。大客户 {len(large_customers)} 个，中等客户 {len(medium_customers)} 个，小客户 {len(small_customers)} 个。客户名称映射覆盖率: {mapped_customers/total_payers*100:.1f}%。"
    }

@mcp.tool()
def analyze_cases_by_payer(month: str = Field(default="", description="可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份")) -> Dict:
    """
    按Account PayerId统计每个payer开工单的数量，以及每个payer下多少个Category (C)是technical support和非technical support的
    
    数据目录路径自动从环境变量CASE_DATA_DIR获取。
    
    Args:
        month: 可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份
        
    Returns:
        按付费账户统计的工单分析
    """
    data_dir = DATA_ROOT_DIR
    cases = load_case_data(data_dir, month)
    
    if not cases:
        month_info = f" (月份: {month})" if month else ""
        return {"error": f"未找到工单数据文件在目录: {data_dir}{month_info}"}
    
    payer_stats = defaultdict(lambda: {
        "total_cases": 0,
        "technical_support": 0,
        "non_technical_support": 0,
        "categories": set()
    })
    
    for case in cases:
        payer_id = case.get('Account PayerId', '').strip()
        category = case.get('Category (C)', '').strip()
        
        if payer_id:
            payer_stats[payer_id]["total_cases"] += 1
            payer_stats[payer_id]["categories"].add(category)
            
            # 判断是否为技术支持
            if category.lower() == 'technical support':
                payer_stats[payer_id]["technical_support"] += 1
            else:
                payer_stats[payer_id]["non_technical_support"] += 1
    
    # 转换为可序列化的格式，并优化显示
    payer_analysis = {}
    for payer_id, stats in payer_stats.items():
        tech_percentage = (stats["technical_support"] / stats["total_cases"]) * 100 if stats["total_cases"] > 0 else 0
        non_tech_percentage = (stats["non_technical_support"] / stats["total_cases"]) * 100 if stats["total_cases"] > 0 else 0
        
        # 生成易读的摘要
        if tech_percentage >= 80:
            support_profile = "技术导向型"
        elif tech_percentage >= 50:
            support_profile = "技术为主型"
        elif tech_percentage >= 20:
            support_profile = "混合型"
        else:
            support_profile = "非技术型"
        
        payer_analysis[payer_id] = {
            "total_cases": stats["total_cases"],
            "support_profile": support_profile,
            "technical_support": {
                "count": stats["technical_support"],
                "percentage": round(tech_percentage, 1)
            },
            "non_technical_support": {
                "count": stats["non_technical_support"],
                "percentage": round(non_tech_percentage, 1)
            },
            "unique_categories": list(stats["categories"]),
            "category_count": len(stats["categories"]),
            "summary": f"{stats['total_cases']}个工单 ({support_profile}, 技术支持{round(tech_percentage, 1)}%)"
        }
    
    # 按工单总数排序
    sorted_payers = dict(sorted(payer_analysis.items(), 
                               key=lambda x: x[1]["total_cases"], 
                               reverse=True))
    
    # 生成统计摘要
    total_payers = len(payer_stats)
    total_cases = sum(stats["total_cases"] for stats in payer_analysis.values())
    
    # 按支持类型分组统计
    tech_oriented = sum(1 for stats in payer_analysis.values() if stats["support_profile"] == "技术导向型")
    tech_primary = sum(1 for stats in payer_analysis.values() if stats["support_profile"] == "技术为主型")
    mixed_type = sum(1 for stats in payer_analysis.values() if stats["support_profile"] == "混合型")
    non_tech = sum(1 for stats in payer_analysis.values() if stats["support_profile"] == "非技术型")
    
    # 找出工单最多的前3个账户
    top_3_payers = list(sorted_payers.items())[:3]
    
    analysis_scope = f"月份 {month} 的" if month and month.strip() else "所有"
    source_files = list(set(case.get('_source_file', '') for case in cases))
    
    return {
        "overview": {
            "total_payers": total_payers,
            "total_cases": total_cases,
            "analysis_scope": analysis_scope,
            "source_files": source_files
        },
        "payer_profiles": {
            "技术导向型": f"{tech_oriented}个账户 (技术支持≥80%)",
            "技术为主型": f"{tech_primary}个账户 (技术支持50-79%)",
            "混合型": f"{mixed_type}个账户 (技术支持20-49%)",
            "非技术型": f"{non_tech}个账户 (技术支持<20%)"
        },
        "top_accounts": {
            f"排名{i+1}": {
                "account_id": payer_id,
                "summary": info["summary"],
                "details": {
                    "技术支持": f"{info['technical_support']['count']}个 ({info['technical_support']['percentage']}%)",
                    "非技术支持": f"{info['non_technical_support']['count']}个 ({info['non_technical_support']['percentage']}%)",
                    "涉及类别": f"{info['category_count']}种类别"
                }
            }
            for i, (payer_id, info) in enumerate(top_3_payers)
        },
        "detailed_analysis": sorted_payers,
        "insights": {
            "最活跃账户": top_3_payers[0][0] if top_3_payers else "无",
            "平均工单数": round(total_cases / total_payers, 1) if total_payers > 0 else 0,
            "技术支持占主导": f"{tech_oriented + tech_primary}个账户 ({round((tech_oriented + tech_primary) / total_payers * 100, 1)}%)" if total_payers > 0 else "0%",
            "需要关注的账户": [payer_id for payer_id, info in top_3_payers if info["total_cases"] > (total_cases / total_payers * 2)] if total_payers > 0 else []
        },
        "summary": f"共分析了{analysis_scope} {total_payers} 个付费账户的 {total_cases} 个工单。技术导向型账户 {tech_oriented} 个，技术为主型 {tech_primary} 个，混合型 {mixed_type} 个，非技术型 {non_tech} 个。"
    }

@mcp.tool()
def analyze_cases_by_service(month: str = Field(default="", description="可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份")) -> Dict:
    """
    结合Resolver和Type (T)列分析各个service的工单数量
    
    数据目录路径自动从环境变量CASE_DATA_DIR获取。
    
    Args:
        month: 可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份
        
    Returns:
        按服务统计的工单分析
    """
    data_dir = DATA_ROOT_DIR
    cases = load_case_data(data_dir, month)
    
    if not cases:
        month_info = f" (月份: {month})" if month else ""
        return {"error": f"未找到工单数据文件在目录: {data_dir}{month_info}"}
    
    service_stats = defaultdict(lambda: {
        "total_cases": 0,
        "types": defaultdict(int),
        "resolvers": set()
    })
    
    for case in cases:
        resolver = case.get('Resolver', '').strip()
        case_type = case.get('Type (T)', '').strip()
        
        if resolver:
            service_stats[resolver]["total_cases"] += 1
            service_stats[resolver]["resolvers"].add(resolver)
            
            if case_type:
                service_stats[resolver]["types"][case_type] += 1
    
    # 转换为可序列化的格式
    service_analysis = {}
    for service, stats in service_stats.items():
        type_analysis = {}
        for case_type, count in stats["types"].items():
            percentage = (count / stats["total_cases"]) * 100 if stats["total_cases"] > 0 else 0
            type_analysis[case_type] = {
                "count": count,
                "percentage": round(percentage, 2)
            }
        
        service_analysis[service] = {
            "total_cases": stats["total_cases"],
            "types": dict(sorted(type_analysis.items(), 
                               key=lambda x: x[1]["count"], 
                               reverse=True)),
            "unique_types": len(stats["types"])
        }
    
    # 按工单总数排序
    sorted_services = dict(sorted(service_analysis.items(), 
                                key=lambda x: x[1]["total_cases"], 
                                reverse=True))
    
    analysis_scope = f"月份 {month} 的" if month else "所有"
    source_files = list(set(case.get('_source_file', '') for case in cases))
    
    return {
        "total_services": len(service_stats),
        "service_analysis": sorted_services,
        "analysis_scope": analysis_scope,
        "source_files": source_files,
        "summary": f"共分析了{analysis_scope} {len(service_stats)} 个不同服务的工单分布情况"
    }

@mcp.tool()
def analyze_general_guidance_cases(month: str = Field(default="", description="可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份")) -> Dict:
    """
    统计Item (I)为General Guidance的工单数量
    
    数据目录路径自动从环境变量CASE_DATA_DIR获取。
    
    Args:
        month: 可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份
        
    Returns:
        General Guidance工单的统计分析
    """
    data_dir = DATA_ROOT_DIR
    cases = load_case_data(data_dir, month)
    
    if not cases:
        month_info = f" (月份: {month})" if month else ""
        return {"error": f"未找到工单数据文件在目录: {data_dir}{month_info}"}
    
    total_cases = len(cases)
    general_guidance_cases = []
    
    for case in cases:
        item = case.get('Item (I)', '').strip()
        if item.lower() == 'general guidance':
            general_guidance_cases.append({
                "case_id": case.get('Case ID', ''),
                "subject": case.get('Subject', ''),
                "resolver": case.get('Resolver', ''),
                "category": case.get('Category (C)', ''),
                "payer_id": case.get('Account PayerId', ''),
                "status": case.get('Status', ''),
                "severity": case.get('Severity', ''),
                "source_file": case.get('_source_file', '')
            })
    
    general_guidance_count = len(general_guidance_cases)
    percentage = (general_guidance_count / total_cases) * 100 if total_cases > 0 else 0
    
    # 按服务分组统计
    service_breakdown = defaultdict(int)
    payer_breakdown = defaultdict(int)
    
    for case in general_guidance_cases:
        service_breakdown[case["resolver"]] += 1
        payer_breakdown[case["payer_id"]] += 1
    
    return {
        "total_cases": total_cases,
        "general_guidance_count": general_guidance_count,
        "percentage": round(percentage, 2),
        "service_breakdown": dict(sorted(service_breakdown.items(), 
                                       key=lambda x: x[1], 
                                       reverse=True)),
        "payer_breakdown": dict(sorted(payer_breakdown.items(), 
                                     key=lambda x: x[1], 
                                     reverse=True)),
        "cases_detail": general_guidance_cases[:10],  # 只返回前10个详细信息
        "analysis_scope": f"月份 {month} 的" if month else "所有",
        "source_files": list(set(case.get('_source_file', '') for case in cases)),
        "summary": f"共找到{f'月份 {month} 的' if month else ''} {general_guidance_count} 个General Guidance工单，占总工单的 {round(percentage, 2)}%"
    }

@mcp.tool()
def get_comprehensive_case_analysis(month: str = Field(default="", description="可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份")) -> Dict:
    """
    获取综合工单分析报告，包含所有维度的统计信息
    
    当用户询问以下问题时使用此工具：
    - "工单综合分析"、"整体工单情况"
    - "7月份工单报告"、"某月综合分析"
    - "工单总体情况"、"完整的工单分析"
    - "生成工单报告"、"工单数据概览"
    
    数据目录路径自动从环境变量CASE_DATA_DIR获取。
    
    Args:
        month: 可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份
        
    Returns:
        包含类别、付费账户、服务、General Guidance等所有维度的综合分析报告
    """
    data_dir = DATA_ROOT_DIR
    cases = load_case_data(data_dir, month)
    
    if not cases:
        month_info = f" (月份: {month})" if month else ""
        return {"error": f"未找到工单数据文件在目录: {data_dir}{month_info}"}
    
    # 基础统计
    total_cases = len(cases)
    
    # 按文件统计
    file_stats = defaultdict(int)
    for case in cases:
        file_stats[case.get('_source_file', 'unknown')] += 1
    
    # 状态统计
    status_stats = Counter()
    severity_stats = Counter()
    
    for case in cases:
        status = case.get('Status', '').strip()
        severity = case.get('Severity', '').strip()
        
        if status:
            status_stats[status] += 1
        if severity:
            severity_stats[severity] += 1
    
    # 获取各维度分析
    category_analysis = analyze_cases_by_category(month)
    payer_analysis = analyze_cases_by_payer(month)
    service_analysis = analyze_cases_by_service(month)
    guidance_analysis = analyze_general_guidance_cases(month)
    
    analysis_scope = f"月份 {month} 的" if month else "所有"
    
    return {
        "overview": {
            "total_cases": total_cases,
            "files_analyzed": len(file_stats),
            "file_breakdown": dict(file_stats),
            "status_distribution": dict(status_stats.most_common()),
            "severity_distribution": dict(severity_stats.most_common()),
            "analysis_scope": analysis_scope
        },
        "category_analysis": category_analysis,
        "payer_analysis": {
            "total_payers": payer_analysis["overview"]["total_payers"],
            "payer_profiles": payer_analysis["payer_profiles"],
            "top_3_accounts": payer_analysis["top_accounts"],
            "key_insights": payer_analysis["insights"]
        },
        "service_analysis": {
            "total_services": service_analysis["total_services"],
            "top_10_services": dict(list(service_analysis["service_analysis"].items())[:10])
        },
        "general_guidance_analysis": guidance_analysis,
        "summary": f"""
        {analysis_scope}综合工单分析报告:
        - 总工单数: {total_cases}
        - 涉及付费账户: {payer_analysis['overview']['total_payers']}
        - 涉及服务: {service_analysis['total_services']}
        - General Guidance工单: {guidance_analysis['general_guidance_count']} ({guidance_analysis['percentage']}%)
        - 主要类别: {list(category_analysis['categories'].keys())[:3] if 'categories' in category_analysis else []}
        """
    }

if __name__ == "__main__":
    # 运行MCP服务器
    mcp.run()
