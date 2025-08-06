#!/usr/bin/env python3
"""
Case Analyzer MCP Server - 工单分析服务器（优化版）

专注于核心工单分析功能，去除冗余代码。
"""

import csv
import os
import re
from collections import defaultdict, Counter
from typing import Dict, List
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# 数据根目录路径 - 从环境变量获取
DATA_ROOT_DIR = os.getenv('CASE_DATA_DIR', os.path.expanduser('~/case-data'))

# 客户映射表路径
CUSTOMER_MAPPING_FILE = os.getenv('CUSTOMER_MAPPING_FILE', os.path.expanduser('~/case-data/customer-mapping.csv'))

# 启动时打印环境变量调试信息
print("=== MCP服务器启动 - 环境变量调试 ===")
print(f"CASE_DATA_DIR: {DATA_ROOT_DIR}")
print(f"CUSTOMER_MAPPING_FILE: {CUSTOMER_MAPPING_FILE}")
print(f"CASE_DATA_DIR exists: {os.path.exists(DATA_ROOT_DIR)}")
print(f"CUSTOMER_MAPPING_FILE exists: {os.path.exists(CUSTOMER_MAPPING_FILE)}")
print("=" * 50)

def load_customer_mapping():
    """加载客户名称映射表 - 增强版，支持CSV和XLSX格式"""
    mapping = {}
    
    print(f"尝试加载客户映射文件: {CUSTOMER_MAPPING_FILE}")
    
    if os.path.exists(CUSTOMER_MAPPING_FILE):
        try:
            file_ext = os.path.splitext(CUSTOMER_MAPPING_FILE)[1].lower()
            
            if file_ext == '.xlsx':
                # 处理XLSX文件
                try:
                    import pandas as pd
                    df = pd.read_excel(CUSTOMER_MAPPING_FILE)
                    headers = df.columns.tolist()
                    print(f"XLSX文件头部: {headers}")
                    
                    for _, row in df.iterrows():
                        # 尝试多种可能的列名
                        payer_id = None
                        customer_name = None
                        
                        # 查找Payer ID列
                        for payer_col in ['Payer', 'PayerID', 'Account PayerId', 'payer_id', 'account_id']:
                            if payer_col in row and pd.notna(row[payer_col]):
                                try:
                                    payer_id = str(int(float(row[payer_col])))
                                    break
                                except (ValueError, TypeError):
                                    payer_id = str(row[payer_col]).strip()
                                    break
                        
                        # 查找客户名称列
                        for customer_col in ['客户', 'Customer', 'customer_name', '客户名称', 'CustomerName']:
                            if customer_col in row and pd.notna(row[customer_col]):
                                customer_name = str(row[customer_col]).strip().replace('\n', '/').replace('\r', '')
                                break
                        
                        if payer_id and customer_name:
                            mapping[payer_id] = customer_name
                            print(f"映射添加: {payer_id} -> {customer_name}")
                            
                except ImportError:
                    print("警告: 需要安装pandas库来支持XLSX格式，回退到CSV格式处理")
                    return mapping
                    
            else:
                # 处理CSV文件
                with open(CUSTOMER_MAPPING_FILE, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    print(f"CSV文件头部: {headers}")
                    
                    for row_num, row in enumerate(reader, 1):
                        # 尝试多种可能的列名
                        payer_id = None
                        customer_name = None
                        
                        # 查找Payer ID列
                        for payer_col in ['Payer', 'PayerID', 'Account PayerId', 'payer_id', 'account_id']:
                            if payer_col in row and row[payer_col] and row[payer_col].strip():
                                try:
                                    payer_id = str(int(float(row[payer_col])))
                                    break
                                except (ValueError, TypeError):
                                    payer_id = str(row[payer_col]).strip()
                                    break
                        
                        # 查找客户名称列
                        for customer_col in ['客户', 'Customer', 'customer_name', '客户名称', 'CustomerName']:
                            if customer_col in row and row[customer_col] and row[customer_col].strip():
                                customer_name = row[customer_col].strip().replace('\n', '/').replace('\r', '')
                                break
                        
                        if payer_id and customer_name:
                            mapping[payer_id] = customer_name
                            print(f"映射添加: {payer_id} -> {customer_name}")
            
            print(f"成功加载客户映射表，包含 {len(mapping)} 个映射关系")
        except Exception as e:
            print(f"加载客户映射表时出错: {e}")
    else:
        print(f"客户映射文件不存在: {CUSTOMER_MAPPING_FILE}")
    
    return mapping

def load_case_data(data_dir: str, month: str = "") -> List[Dict]:
    """加载指定目录下的工单CSV文件"""
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
        # 查找所有符合格式的CSV文件
        for filename in os.listdir(data_dir):
            if filename.startswith('cases-') and filename.endswith('.csv'):
                file_path = os.path.join(data_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            row['_source_file'] = filename
                            all_cases.append(row)
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
                    continue
    
    return all_cases

def get_available_months(data_dir: str) -> List[str]:
    """获取数据目录下所有可用的月份"""
    months = []
    
    if not os.path.exists(data_dir):
        return months
    
    for filename in os.listdir(data_dir):
        if filename.startswith('cases-') and filename.endswith('.csv'):
            match = re.search(r'cases-(\d{6})\.csv', filename)
            if match:
                months.append(match.group(1))
    
    return sorted(months)

def format_aligned_table(headers: List[str], rows: List[List[str]], title: str = None) -> str:
    """
    生成对齐的表格格式
    
    Args:
        headers: 表格头部列表
        rows: 表格行数据列表
        title: 可选的表格标题
        
    Returns:
        格式化的对齐表格字符串
    """
    if not rows:
        return f"{title}\n\n(无数据)" if title else "(无数据)"
    
    # 计算每列的最大宽度（考虑中文字符）
    def get_display_width(text):
        """计算字符串的显示宽度（中文字符算2个宽度）"""
        width = 0
        for char in str(text):
            if ord(char) > 127:  # 中文字符
                width += 2
            else:  # 英文字符
                width += 1
        return width
    
    # 计算列宽
    col_widths = []
    for i, header in enumerate(headers):
        max_width = get_display_width(header)
        for row in rows:
            if i < len(row):
                max_width = max(max_width, get_display_width(row[i]))
        col_widths.append(max_width + 2)  # 额外padding
    
    # 生成表格
    table_lines = []
    
    if title:
        table_lines.append(f"## {title}")
        table_lines.append("")
    
    # 表格头部
    header_line = "|"
    separator_line = "|"
    for i, (header, width) in enumerate(zip(headers, col_widths)):
        padding = width - get_display_width(header)
        header_line += f" {header}{' ' * padding}|"
        separator_line += f"{'-' * (width + 1)}|"
    
    table_lines.append(header_line)
    table_lines.append(separator_line)
    
    # 表格内容
    for row in rows:
        row_line = "|"
        for i, (cell, width) in enumerate(zip(row, col_widths)):
            cell_str = str(cell)
            padding = width - get_display_width(cell_str)
            row_line += f" {cell_str}{' ' * padding}|"
        table_lines.append(row_line)
    
    return "\n".join(table_lines)

# 创建FastMCP服务器实例
mcp = FastMCP(
    "case-analyzer",
    instructions="""
    工单分析服务器 - 专业的技术支持工单数据分析工具
    
    核心功能：
    - 按月份、类别、付费账户、服务等维度分析工单
    - 支持客户名称映射
    - 生成美化表格输出
    - 统计General Guidance工单
    
    主要工具：
    - analyze_cases_by_category: 按类别统计
    - analyze_cases_by_payer: 按付费账户统计（含表格输出）
    - analyze_cases_by_service: 按服务统计
    - analyze_general_guidance_cases: General Guidance统计
    - get_available_months: 获取可用月份
    """
)

@mcp.tool()
def get_available_months() -> Dict:
    """获取工单数据目录下所有可用的月份列表"""
    data_dir = DATA_ROOT_DIR
    months = get_available_months(data_dir)
    
    if not months:
        return {"error": f"未找到工单数据文件在目录: {data_dir}"}
    
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
        "data_directory": data_dir,
        "summary": f"找到 {len(months)} 个月份的工单数据文件"
    }

@mcp.tool()
def analyze_cases_by_category(month: str = Field(default="", description="可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份")) -> Dict:
    """按工单类别(Category)统计分析工单数量和分布情况"""
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
def analyze_cases_by_payer(month: str = Field(default="", description="可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份")) -> Dict:
    """
    按Account PayerId统计每个payer开工单的数量，以及每个payer下多少个Category (C)是technical support和非technical support的。
    并以表格输出。如果客户通过CUSTOMER_MAPPING_FILE提供了 payer和客户名字对应关系时，就把客户名字显示到生成的结果表格中。
    输出表格包含以下列：客户名称 | 账户ID | 总工单数 | 技术工单数 | 非技术工单数 | 技术占比
    
    优化功能：
    1. 增强客户映射文件加载，支持多种列名格式
    2. 优化表格对齐，考虑中文字符宽度
    3. 提供详细的调试信息
    4. 确保显示所有payer账号
    """
    data_dir = DATA_ROOT_DIR
    cases = load_case_data(data_dir, month)
    
    if not cases:
        month_info = f" (月份: {month})" if month else ""
        return {"error": f"未找到工单数据文件在目录: {data_dir}{month_info}"}
    
    # 加载客户映射表（增强版）
    customer_mapping = load_customer_mapping()
    
    # 统计每个payer的工单情况
    payer_stats = defaultdict(lambda: {
        "total_cases": 0,
        "technical_support": 0,
        "non_technical_support": 0,
        "categories": set()
    })
    
    # 调试信息收集
    empty_payer_count = 0
    unique_payers = set()
    
    for case in cases:
        payer_id = case.get('Account PayerId', '').strip()
        category = case.get('Category (C)', '').strip()
        
        if not payer_id:
            empty_payer_count += 1
            continue
            
        unique_payers.add(payer_id)
        
        if payer_id:
            payer_stats[payer_id]["total_cases"] += 1
            payer_stats[payer_id]["categories"].add(category)
            
            if category.lower() == "technical support":
                payer_stats[payer_id]["technical_support"] += 1
            else:
                payer_stats[payer_id]["non_technical_support"] += 1
    
    # 准备表格数据
    table_data = []
    table_rows = []
    
    # 确保所有payer都被处理
    for payer_id, stats in payer_stats.items():
        tech_percentage = (stats["technical_support"] / stats["total_cases"]) * 100 if stats["total_cases"] > 0 else 0
        
        # 获取客户名称（增强版映射）
        if customer_mapping and payer_id in customer_mapping:
            customer_name = customer_mapping[payer_id]
        else:
            customer_name = "未知客户"
        
        # 为了表格对齐，截断过长的账户ID
        display_account_id = payer_id
        if len(payer_id) > 12:
            display_account_id = f"{payer_id[:8]}...{payer_id[-4:]}"
        
        table_data.append({
            "customer_name": customer_name,
            "account_id": payer_id,
            "display_account_id": display_account_id,
            "total_cases": stats["total_cases"],
            "tech_support": stats["technical_support"],
            "non_tech": stats["non_technical_support"],
            "tech_percentage": tech_percentage
        })
    
    # 按工单数量排序
    table_data.sort(key=lambda x: x["total_cases"], reverse=True)
    
    # 准备表格行数据（添加编号）
    table_rows = []
    for i, data in enumerate(table_data, 1):
        table_rows.append([
            str(i),  # 编号
            data["customer_name"],
            data["display_account_id"],
            str(data["total_cases"]),
            str(data["tech_support"]),
            str(data["non_tech"]),
            f"{data['tech_percentage']:.1f}%"
        ])
    
    # 生成对齐的表格（添加编号列）
    analysis_scope = f"{month}月份" if month and month.strip() else "全部"
    headers = ["编号", "客户名称", "账户ID", "总工单数", "技术工单数", "非技术工单数", "技术占比"]
    
    aligned_table = format_aligned_table(
        headers=headers,
        rows=table_rows,
        title=f"{analysis_scope}付费账户工单分布表（完整版 - 共{len(table_rows)}个账户）"
    )
    
    # 添加统计摘要
    total_payers = len(payer_stats)
    total_cases = sum(stats["total_cases"] for stats in payer_stats.values())
    total_tech = sum(stats["technical_support"] for stats in payer_stats.values())
    total_non_tech = sum(stats["non_technical_support"] for stats in payer_stats.values())
    overall_tech_percentage = (total_tech / total_cases) * 100 if total_cases > 0 else 0
    
    mapped_customers = sum(1 for row in table_data if customer_mapping and row['account_id'] in customer_mapping)
    
    summary_lines = [
        "",
        "### 📊 统计摘要",
        "",
        f"- **总付费账户数**: {total_payers} 个",
        f"- **总工单数**: {total_cases} 个",
        f"- **空PayerId记录数**: {empty_payer_count} 个",
        f"- **有效PayerId记录数**: {total_cases} 个",
        f"- **技术支持工单**: {total_tech} 个 ({overall_tech_percentage:.1f}%)",
        f"- **非技术支持工单**: {total_non_tech} 个 ({100-overall_tech_percentage:.1f}%)",
        f"- **客户名称映射覆盖率**: {mapped_customers}/{total_payers} ({mapped_customers/total_payers*100:.1f}%)" if total_payers > 0 else "- **客户名称映射覆盖率**: 0/0 (0%)",
        f"- **平均每账户工单数**: {total_cases/total_payers:.1f} 个" if total_payers > 0 else "- **平均每账户工单数**: 0 个"
    ]
    
    # 添加完整的payer列表（用于调试）
    payer_list_lines = [
        "",
        "### 🔍 完整Payer账户列表（调试信息）",
        ""
    ]
    for i, (payer_id, stats) in enumerate(sorted(payer_stats.items(), key=lambda x: x[1]["total_cases"], reverse=True), 1):
        customer_name = customer_mapping.get(payer_id, "未知客户") if customer_mapping else "未知客户"
        payer_list_lines.append(f"{i:2d}. {payer_id} ({customer_name}) - 总工单:{stats['total_cases']}, 技术:{stats['technical_support']}, 非技术:{stats['non_technical_support']}")
    
    # 添加数据来源信息
    source_files = list(set(case.get('_source_file', '') for case in cases))
    source_lines = [
        "",
        "### 📁 数据来源",
        ""
    ]
    for file in source_files:
        source_lines.append(f"- {file}")
    
    full_output = aligned_table + "\n" + "\n".join(summary_lines + payer_list_lines + source_lines)
    
    return {
        "table_output": full_output,
        "raw_data": table_data,
        "total_accounts": total_payers,
        "total_cases": total_cases,
        "analysis_period": analysis_scope,
        "customer_mapping_rate": f"{mapped_customers/total_payers*100:.1f}%" if total_payers > 0 else "0%",
        "tech_support_rate": f"{overall_tech_percentage:.1f}%",
        "debug_info": {
            "unique_payers_found": len(unique_payers),
            "payer_stats_count": len(payer_stats),
            "empty_payer_records": empty_payer_count,
            "all_payers_list": sorted(list(unique_payers)),
            "table_rows_generated": len(table_rows)
        },
        "mapping_debug": {
            "mapping_file_exists": os.path.exists(CUSTOMER_MAPPING_FILE),
            "mapping_file_path": CUSTOMER_MAPPING_FILE,
            "loaded_mappings": len(customer_mapping),
            "mapped_accounts": mapped_customers,
            "unmapped_accounts": total_payers - mapped_customers
        },
        "summary": f"生成了{analysis_scope}的完整付费账户工单分布表格，包含{total_payers}个账户的{total_cases}个工单信息，确保显示所有payer账号。客户名称映射覆盖率{mapped_customers/total_payers*100:.1f}%。"
    }

@mcp.tool()
def analyze_cases_by_service(month: str = Field(default="", description="可选的月份参数，格式为YYYYMM (如: 202507) 或 YYYY-MM (如: 2025-07)，留空分析所有月份")) -> Dict:
    """结合Resolver和Type (T)列分析各个service的工单数量"""
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
    """统计Item (I)为General Guidance的工单数量"""
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


if __name__ == "__main__":
    # 运行MCP服务器
    mcp.run()
