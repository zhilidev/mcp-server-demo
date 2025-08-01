#!/usr/bin/env python3
"""
Account Analyzer MCP Server - Enterprise账号分析 (多客户版本)

这个服务器分析Enterprise级别账号变化情况。
支持Tools、Resources和Prompts三种MCP类型，支持多客户分析。
"""

import csv
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# 数据根目录路径 - 从环境变量获取，避免硬编码敏感路径
DATA_ROOT_DIR = os.getenv('ACCOUNT_DATA_DIR', os.path.expanduser('~/account-data'))

# 创建FastMCP服务器实例
mcp = FastMCP(
    "account-analyzer",
    instructions="""
    # Account Enterprise账号分析服务器

    这个服务器分析Enterprise级别账号变化情况。
    支持Tools、Resources和Prompts三种MCP功能，支持多客户分析。

    ## 多客户支持

    支持按客户分文件夹分析：
    - 客户1: /data-directory/customer1/
    - 客户2: /data-directory/customer2/
    - 其他客户可以动态添加

    ## 可用工具 (Tools)

    ### 客户管理工具
    - `get_available_customers`: 获取所有可用的客户列表
    - `compare_customers`: 比较不同客户的账号规模和变化
    - `get_all_customers_summary`: 获取所有客户的汇总信息

    ### 基础分析工具 (需要customer参数)
    - `compare_payer_changes`: 比较指定客户两个日期之间的变化
    - `simple_payer_summary`: 生成指定客户的简单摘要
    - `get_available_dates_tool`: 获取指定客户的所有可用数据日期
    - `analyze_recent_changes`: 分析指定客户最近N天的趋势
    - `get_account_details`: 获取指定客户特定日期的详细信息
    - `analyze_single_date_accounts`: 分析指定客户在特定日期的完整账号情况 (适用于单日数据)

    ### 高级追踪工具 (需要customer参数)
    - `track_account_history`: 追踪指定客户特定账号的完整历史变化
    - `analyze_payer_linked_changes`: 分析指定客户特定Payer下Linked账号的详细变化

    ## 可用资源 (Resources)

    - `customer-data://{customer}`: 访问特定客户的基本信息
    - `account-data://{customer}/{date}`: 访问特定客户特定日期的原始账号数据
    - `summary://{customer}/latest`: 获取特定客户最新的账号摘要信息

    ## 可用提示 (Prompts)

    - `analyze-trends`: 账号变化趋势分析模板
    - `monthly-report`: 月度报告生成模板
    - `multi-customer-report`: 多客户对比分析模板

    ## 数据来源

    分析指定数据目录下按客户分组的CSV文件。
    只处理Support Level为"ENTERPRISE"的记录。

    ## 使用方法

    1. 首先获取可用客户: get_available_customers()
    2. 指定客户进行分析，如: customer="customer1" 或 customer="customer2"
    3. 日期格式为4位数字，如：0723, 0730, 0731
    """
)

class AccountRecord:
    """账号记录类"""
    def __init__(self, row: Dict[str, str]):
        self.account_name = row.get("Account Name", "").strip('"')
        self.account_id = row.get("Account ID", "").strip('"')
        self.support_level = row.get("Support Level", "").strip('"')
        self.status = row.get("Status", "").strip('"')
        self.linked_accounts = row.get("Linked Accounts", "").strip('"')
        self.account_type = row.get("Account Type", "").strip('"')
        self.payer_id = row.get("Payer ID", "").strip('"')
        self.tags = row.get("Tags", "").strip('"')
    
    def is_enterprise(self) -> bool:
        """检查是否为Enterprise级别"""
        return self.support_level.upper() == "ENTERPRISE"
    
    def is_payer(self) -> bool:
        """检查是否为Payer账号"""
        return self.account_type == "PAYER_ACCOUNT"
    
    def is_linked(self) -> bool:
        """检查是否为Linked账号"""
        return self.account_type == "LINKED_ACCOUNT"
    
    def __str__(self):
        return f"{self.account_name} ({self.account_id})"

# ============ 多客户支持函数 ============

def get_available_customers() -> List[str]:
    """获取所有可用的客户列表"""
    customers = []
    if not os.path.exists(DATA_ROOT_DIR):
        return customers
    
    for item in os.listdir(DATA_ROOT_DIR):
        item_path = os.path.join(DATA_ROOT_DIR, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            customers.append(item)
    
    return sorted(customers)

def get_customer_data_dir(customer: str) -> str:
    """获取指定客户的数据目录路径"""
    return os.path.join(DATA_ROOT_DIR, customer)

def normalize_date_format(date_str: str) -> str:
    """
    标准化日期格式，统一转换为 MMDD 格式用于内部处理
    支持输入格式：
    - MMDD (如 0513) -> 0513
    - YYYYMMDD (如 20250513) -> 0513
    """
    if len(date_str) == 4:
        # 已经是 MMDD 格式
        return date_str
    elif len(date_str) == 8:
        # YYYYMMDD 格式，提取 MMDD 部分
        return date_str[4:]
    else:
        # 其他格式，直接返回
        return date_str

def expand_date_format(date_str: str) -> List[str]:
    """
    根据输入的日期格式，生成可能的文件名日期格式
    输入 MMDD 格式，返回 [MMDD, YYYYMMDD] 格式列表
    """
    if len(date_str) == 4:
        # MMDD 格式，生成对应的 YYYYMMDD 格式
        return [date_str, f"2025{date_str}"]
    elif len(date_str) == 8:
        # YYYYMMDD 格式，提取 MMDD 部分
        mmdd = date_str[4:]
        return [mmdd, date_str]
    else:
        return [date_str]

def get_available_dates(customer: str) -> List[str]:
    """获取指定客户所有可用的数据日期，统一返回 MMDD 格式"""
    dates = []
    customer_dir = get_customer_data_dir(customer)
    
    if not os.path.exists(customer_dir):
        return dates
    
    # 支持多种文件名格式
    patterns = [
        re.compile(rf'{re.escape(customer)}-CMC-accounts-(\d{{4}})\.csv'),  # customer-CMC-accounts-0731.csv
        re.compile(rf'{re.escape(customer)}-CMC-accounts-(\d{{8}})\.csv'),  # customer-CMC-accounts-20250731.csv
        re.compile(rf'{re.escape(customer)}-accounts-(\d{{4}})\.csv'),  # customer-accounts-0731.csv
        re.compile(rf'{re.escape(customer)}-accounts-(\d{{8}})\.csv'),  # customer-accounts-20250731.csv
        re.compile(r'accounts-(\d{4})\.csv'),  # accounts-0731.csv (MMDD格式)
        re.compile(r'accounts-(\d{8})\.csv'),  # accounts-20250513.csv (YYYYMMDD格式)
        re.compile(r'CMC-accounts-(\d{4})\.csv'),  # CMC-accounts-0731.csv
        re.compile(r'CMC-accounts-(\d{8})\.csv'),  # CMC-accounts-20250513.csv
    ]
    
    for filename in os.listdir(customer_dir):
        for pattern in patterns:
            match = pattern.match(filename)
            if match:
                raw_date = match.group(1)
                # 标准化为 MMDD 格式
                normalized_date = normalize_date_format(raw_date)
                if normalized_date not in dates:
                    dates.append(normalized_date)
                break
    
    return sorted(dates)

def load_accounts_data(customer: str, date: str) -> List[AccountRecord]:
    """加载指定客户指定日期的账号数据"""
    customer_dir = get_customer_data_dir(customer)
    
    # 生成可能的日期格式
    date_formats = expand_date_format(date)
    
    # 尝试多种文件名格式
    possible_filenames = []
    for date_fmt in date_formats:
        possible_filenames.extend([
            f"{customer}-CMC-accounts-{date_fmt}.csv",
            f"{customer}-accounts-{date_fmt}.csv",  # 新增支持
            f"accounts-{date_fmt}.csv",
            f"CMC-accounts-{date_fmt}.csv",
        ])
    
    filepath = None
    for filename in possible_filenames:
        test_path = os.path.join(customer_dir, filename)
        if os.path.exists(test_path):
            filepath = test_path
            break
    
    if not filepath:
        raise FileNotFoundError(f"找不到客户 {customer} 日期 {date} 的数据文件。尝试的文件名: {possible_filenames}")
    
    accounts = []
    with open(filepath, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            account = AccountRecord(row)
            if account.is_enterprise():  # 只处理Enterprise级别的账号
                accounts.append(account)
    
    return accounts

def parse_date_string(date_str: str) -> datetime:
    """将MMDD格式的日期字符串转换为datetime对象"""
    # 假设是当前年份
    current_year = datetime.now().year
    month = int(date_str[:2])
    day = int(date_str[2:])
    return datetime(current_year, month, day)

def get_recent_dates(customer: str, days: int = 7) -> List[str]:
    """获取指定客户最近N天的可用日期"""
    all_dates = get_available_dates(customer)
    if not all_dates:
        return []
    
    # 转换为datetime对象并排序
    date_objects = []
    for date_str in all_dates:
        try:
            dt = parse_date_string(date_str)
            date_objects.append((date_str, dt))
        except ValueError:
            continue
    
    date_objects.sort(key=lambda x: x[1], reverse=True)
    
    # 返回最近的N个日期
    return [date_str for date_str, _ in date_objects[:days]]

def analyze_enterprise_accounts(accounts: List[AccountRecord]) -> Dict:
    """分析Enterprise账号数据"""
    payer_accounts = []
    linked_accounts = []
    payer_to_linked = defaultdict(list)
    
    for account in accounts:
        if account.is_payer():
            payer_accounts.append(account)
        elif account.is_linked():
            linked_accounts.append(account)
            payer_to_linked[account.payer_id].append(account)
    
    return {
        "payer_accounts": payer_accounts,
        "linked_accounts": linked_accounts,
        "payer_to_linked": dict(payer_to_linked),
        "total_payers": len(payer_accounts),
        "total_linked": len(linked_accounts),
        "total_accounts": len(accounts)
    }

# ============ 新增客户管理工具 ============

@mcp.tool()
def get_available_customers_tool() -> str:
    """获取所有可用的客户列表"""
    try:
        customers = get_available_customers()
        if not customers:
            return "❌ 未找到任何客户数据文件夹"
        
        result = f"🏢 **可用客户** ({len(customers)} 个):\n\n"
        for customer in customers:
            customer_dir = get_customer_data_dir(customer)
            dates = get_available_dates(customer)
            result += f"- **{customer}**\n"
            result += f"  - 📁 路径: {customer_dir}\n"
            result += f"  - 📅 数据日期: {len(dates)} 个 ({', '.join(dates) if dates else '无'})\n"
            
            # 显示最新数据的简要信息
            if dates:
                try:
                    latest_date = dates[-1]
                    accounts = load_accounts_data(customer, latest_date)
                    analysis = analyze_enterprise_accounts(accounts)
                    result += f"  - 📊 最新数据({latest_date}): {analysis['total_payers']} Payer, {analysis['total_linked']} Linked\n"
                except Exception:
                    result += f"  - ⚠️  最新数据加载失败\n"
            result += "\n"
        
        return result
    except Exception as e:
        return f"获取客户列表失败: {str(e)}"

@mcp.tool()
def compare_customers(
    date: str = Field(description="比较日期 (格式: 0731)")
) -> str:
    """比较不同客户在指定日期的账号规模"""
    try:
        customers = get_available_customers()
        if not customers:
            return "❌ 未找到任何客户"
        
        customer_stats = []
        for customer in customers:
            try:
                accounts = load_accounts_data(customer, date)
                analysis = analyze_enterprise_accounts(accounts)
                customer_stats.append({
                    "customer": customer,
                    "payers": analysis["total_payers"],
                    "linked": analysis["total_linked"],
                    "total": analysis["total_accounts"]
                })
            except Exception as e:
                customer_stats.append({
                    "customer": customer,
                    "error": str(e)
                })
        
        # 生成对比报告
        report = f"# 🏢 客户账号规模对比 ({date})\n\n"
        
        # 成功加载的客户统计
        valid_stats = [s for s in customer_stats if "error" not in s]
        if valid_stats:
            # 按总账号数排序
            valid_stats.sort(key=lambda x: x["total"], reverse=True)
            
            report += "## 📊 账号规模排名\n\n"
            report += "| 排名 | 客户 | Payer账号 | Linked账号 | 总计 |\n"
            report += "|------|------|-----------|------------|------|\n"
            
            for i, stat in enumerate(valid_stats, 1):
                report += f"| {i} | {stat['customer']} | {stat['payers']} | {stat['linked']} | {stat['total']} |\n"
            
            # 汇总统计
            total_payers = sum(s["payers"] for s in valid_stats)
            total_linked = sum(s["linked"] for s in valid_stats)
            total_accounts = sum(s["total"] for s in valid_stats)
            
            report += f"\n**📈 汇总统计**:\n"
            report += f"- 总客户数: {len(valid_stats)} 个\n"
            report += f"- 总Payer账号: {total_payers} 个\n"
            report += f"- 总Linked账号: {total_linked} 个\n"
            report += f"- 总Enterprise账号: {total_accounts} 个\n"
        
        # 加载失败的客户
        error_stats = [s for s in customer_stats if "error" in s]
        if error_stats:
            report += "\n## ⚠️  数据加载失败的客户\n\n"
            for stat in error_stats:
                report += f"- **{stat['customer']}**: {stat['error']}\n"
        
        return report
        
    except Exception as e:
        return f"客户对比分析失败: {str(e)}"

# ============ 更新后的基础分析工具 ============

@mcp.tool()
def get_available_dates_tool(
    customer: str = Field(description="客户名称 (如: customer1, customer2)")
) -> str:
    """获取指定客户所有可用的数据日期"""
    try:
        dates = get_available_dates(customer)
        if not dates:
            return f"❌ 未找到客户 {customer} 的任何数据文件"
        
        result = f"📅 **客户 {customer} 可用数据日期** ({len(dates)} 个):\n\n"
        for date in dates:
            try:
                dt = parse_date_string(date)
                formatted_date = dt.strftime("%m月%d日")
                result += f"- `{date}` ({formatted_date})\n"
            except ValueError:
                result += f"- `{date}` (格式异常)\n"
        
        return result
    except Exception as e:
        return f"获取客户 {customer} 日期失败: {str(e)}"

@mcp.tool()
def compare_payer_changes(
    customer: str = Field(description="客户名称 (如: customer1, customer2)"),
    date1: str = Field(description="第一个日期 (格式: 0723)"),
    date2: str = Field(description="第二个日期 (格式: 0724)")
) -> str:
    """比较指定客户两个日期之间Enterprise Payer账号和其下Linked账号的变化"""
    
    try:
        # 加载两个日期的数据
        accounts1 = load_accounts_data(customer, date1)
        accounts2 = load_accounts_data(customer, date2)
        
        # 分析数据
        analysis1 = analyze_enterprise_accounts(accounts1)
        analysis2 = analyze_enterprise_accounts(accounts2)
        
        # 比较Payer账号变化
        payers1 = {acc.account_id: acc for acc in analysis1["payer_accounts"]}
        payers2 = {acc.account_id: acc for acc in analysis2["payer_accounts"]}
        
        new_payers = set(payers2.keys()) - set(payers1.keys())
        removed_payers = set(payers1.keys()) - set(payers2.keys())
        common_payers = set(payers1.keys()) & set(payers2.keys())
        
        # 生成报告
        report = f"""# 🏢 {customer} Enterprise账号变化分析报告 ({date1} → {date2})

## 总体统计
- {date1}: {analysis1['total_payers']} 个Payer账号, {analysis1['total_linked']} 个Linked账号
- {date2}: {analysis2['total_payers']} 个Payer账号, {analysis2['total_linked']} 个Linked账号

## Payer账号变化
- 新增Payer账号: {len(new_payers)} 个
- 移除Payer账号: {len(removed_payers)} 个
- 保持不变: {len(common_payers)} 个

"""
        
        if new_payers:
            report += "### 🆕 新增的Payer账号:\n"
            for payer_id in new_payers:
                payer = payers2[payer_id]
                linked_count = len(analysis2["payer_to_linked"].get(payer_id, []))
                first_seen = find_account_first_appearance(customer, payer_id, "PAYER")
                
                report += f"- **{payer.account_name}** ({payer_id})\n"
                report += f"  - 📅 首次出现日期: {first_seen or '未知'}\n"
                report += f"  - 🔗 下属Linked账号: {linked_count} 个\n"
                
                if linked_count > 0:
                    report += f"  - 📋 Linked账号列表:\n"
                    for linked in analysis2["payer_to_linked"][payer_id][:5]:  # 显示前5个
                        report += f"    - {linked.account_name} ({linked.account_id})\n"
                    if linked_count > 5:
                        report += f"    - ... 还有 {linked_count - 5} 个账号\n"
                report += "\n"
        
        if removed_payers:
            report += "### ❌ 移除的Payer账号:\n"
            for payer_id in removed_payers:
                payer = payers1[payer_id]
                linked_count = len(analysis1["payer_to_linked"].get(payer_id, []))
                last_seen = find_account_last_appearance(customer, payer_id, "PAYER")
                
                report += f"- **{payer.account_name}** ({payer_id})\n"
                report += f"  - 📅 最后出现日期: {last_seen or '未知'}\n"
                report += f"  - 🔗 原有Linked账号: {linked_count} 个\n"
                report += "\n"
        
        # 详细的Linked账号变化分析
        linked_changes = analyze_linked_account_changes(customer, date1, date2)
        if linked_changes and "error" not in linked_changes:
            report += "## 🔗 Linked账号详细变化分析\n\n"
            
            has_changes = False
            for payer_id, changes in linked_changes.items():
                if changes["new"] or changes["removed"]:
                    has_changes = True
                    payer_name = changes["new"][0]["payer_name"] if changes["new"] else changes["removed"][0]["payer_name"]
                    
                    report += f"### 🏢 {payer_name} ({payer_id})\n"
                    
                    if changes["new"]:
                        report += f"**🆕 新增Linked账号 ({len(changes['new'])} 个):**\n"
                        for item in changes["new"]:
                            account = item["account"]
                            first_seen = item["first_seen"]
                            payer_info = f"挂在Payer: **{item['payer_name']}** ({item['payer_id']})"
                            report += f"- **{account.account_name}** (ID: {account.account_id})\n"
                            report += f"  - 🏢 {payer_info}\n"
                            report += f"  - 📅 首次出现: {first_seen or '未知'}\n"
                            report += f"  - 📊 状态: {account.status}\n"
                            report += f"  - 🏷️  标签: {account.tags or '无'}\n"
                    
                    if changes["removed"]:
                        report += f"**❌ 移除Linked账号 ({len(changes['removed'])} 个):**\n"
                        for item in changes["removed"]:
                            account = item["account"]
                            last_seen = item["last_seen"]
                            payer_info = f"原挂在Payer: **{item['payer_name']}** ({item['payer_id']})"
                            report += f"- **{account.account_name}** (ID: {account.account_id})\n"
                            report += f"  - 🏢 {payer_info}\n"
                            report += f"  - 📅 最后出现: {last_seen or '未知'}\n"
                            report += f"  - 📊 状态: {account.status}\n"
                            report += f"  - 🏷️  标签: {account.tags or '无'}\n"
                    
                    report += "\n"
            
            if not has_changes:
                report += "✅ **无Linked账号变化**\n"
        else:
            report += "## 🔗 Linked账号变化\n"
            if "error" in linked_changes:
                report += f"❌ 分析失败: {linked_changes['error']}\n"
            else:
                report += "✅ 无变化\n"
        
        return report
        
    except Exception as e:
        return f"分析客户 {customer} 失败: {str(e)}"

# ============ 辅助函数 ============

def find_account_first_appearance(customer: str, account_id: str, account_type: str = "PAYER") -> Optional[str]:
    """查找指定客户账号首次出现的日期"""
    dates = get_available_dates(customer)
    
    for date in dates:
        try:
            accounts = load_accounts_data(customer, date)
            for account in accounts:
                if account.account_id == account_id:
                    if account_type == "PAYER" and account.is_payer():
                        return date
                    elif account_type == "LINKED" and account.is_linked():
                        return date
        except Exception:
            continue
    
    return None

def find_account_last_appearance(customer: str, account_id: str, account_type: str = "PAYER") -> Optional[str]:
    """查找指定客户账号最后出现的日期"""
    dates = get_available_dates(customer)
    
    for date in reversed(dates):  # 从最新日期开始查找
        try:
            accounts = load_accounts_data(customer, date)
            for account in accounts:
                if account.account_id == account_id:
                    if account_type == "PAYER" and account.is_payer():
                        return date
                    elif account_type == "LINKED" and account.is_linked():
                        return date
        except Exception:
            continue
    
    return None

def get_payer_name_by_id(customer: str, payer_id: str, date: str) -> str:
    """根据客户、Payer ID和日期获取Payer名称"""
    try:
        accounts = load_accounts_data(customer, date)
        for account in accounts:
            if account.account_id == payer_id and account.is_payer():
                return account.account_name
    except Exception:
        pass
    return f"Unknown Payer ({payer_id})"

def analyze_linked_account_changes(customer: str, date1: str, date2: str) -> Dict:
    """详细分析指定客户Linked账号的变化情况"""
    try:
        accounts1 = load_accounts_data(customer, date1)
        accounts2 = load_accounts_data(customer, date2)
        
        analysis1 = analyze_enterprise_accounts(accounts1)
        analysis2 = analyze_enterprise_accounts(accounts2)
        
        # 创建Linked账号映射
        linked1 = {acc.account_id: acc for acc in analysis1["linked_accounts"]}
        linked2 = {acc.account_id: acc for acc in analysis2["linked_accounts"]}
        
        new_linked_ids = set(linked2.keys()) - set(linked1.keys())
        removed_linked_ids = set(linked1.keys()) - set(linked2.keys())
        
        # 按Payer分组分析变化
        payer_changes = defaultdict(lambda: {"new": [], "removed": []})
        
        # 分析新增的Linked账号
        for linked_id in new_linked_ids:
            linked_account = linked2[linked_id]
            payer_id = linked_account.payer_id
            payer_name = get_payer_name_by_id(customer, payer_id, date2)
            
            payer_changes[payer_id]["new"].append({
                "account": linked_account,
                "payer_name": payer_name,
                "payer_id": payer_id,
                "first_seen": find_account_first_appearance(customer, linked_id, "LINKED")
            })
        
        # 分析移除的Linked账号
        for linked_id in removed_linked_ids:
            linked_account = linked1[linked_id]
            payer_id = linked_account.payer_id
            payer_name = get_payer_name_by_id(customer, payer_id, date1)
            
            payer_changes[payer_id]["removed"].append({
                "account": linked_account,
                "payer_name": payer_name,
                "payer_id": payer_id,
                "last_seen": find_account_last_appearance(customer, linked_id, "LINKED")
            })
        
        return dict(payer_changes)
        
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_detailed_linked_changes(
    customer: str = Field(description="客户名称 (如: customer1, )"),
    date1: str = Field(description="第一个日期 (格式: 0723)"),
    date2: str = Field(description="第二个日期 (格式: 0724)")
) -> str:
    """获取详细的Linked账号变化信息，包括具体账号名称、ID和所属Payer"""
    
    try:
        # 加载两个日期的数据
        accounts1 = load_accounts_data(customer, date1)
        accounts2 = load_accounts_data(customer, date2)
        
        # 分析数据
        analysis1 = analyze_enterprise_accounts(accounts1)
        analysis2 = analyze_enterprise_accounts(accounts2)
        
        # 创建Linked账号映射
        linked1 = {acc.account_id: acc for acc in analysis1["linked_accounts"]}
        linked2 = {acc.account_id: acc for acc in analysis2["linked_accounts"]}
        
        new_linked_ids = set(linked2.keys()) - set(linked1.keys())
        removed_linked_ids = set(linked1.keys()) - set(linked2.keys())
        
        # 生成详细报告
        report = f"""# 🔗 {customer} Linked账号详细变化报告 ({date1} → {date2})

## 📊 变化概览
- 🆕 新增Linked账号: {len(new_linked_ids)} 个
- ❌ 移除Linked账号: {len(removed_linked_ids)} 个
- 📈 净变化: {len(new_linked_ids) - len(removed_linked_ids):+d} 个

"""
        
        # 详细的新增Linked账号信息
        if new_linked_ids:
            report += "## 🆕 新增Linked账号详细信息\n\n"
            
            # 按Payer分组显示
            new_by_payer = defaultdict(list)
            for linked_id in new_linked_ids:
                linked_account = linked2[linked_id]
                payer_id = linked_account.payer_id
                payer_name = get_payer_name_by_id(customer, payer_id, date2)
                first_seen = find_account_first_appearance(customer, linked_id, "LINKED")
                
                new_by_payer[payer_id].append({
                    "account": linked_account,
                    "payer_name": payer_name,
                    "payer_id": payer_id,
                    "first_seen": first_seen
                })
            
            for payer_id, linked_list in new_by_payer.items():
                payer_name = linked_list[0]["payer_name"]
                report += f"### 🏢 Payer: {payer_name} ({payer_id})\n"
                report += f"**新增 {len(linked_list)} 个Linked账号:**\n\n"
                
                for i, item in enumerate(linked_list, 1):
                    account = item["account"]
                    first_seen = item["first_seen"]
                    payer_info = f"挂在Payer: **{item['payer_name']}** ({item['payer_id']})"
                    report += f"{i}. **{account.account_name}**\n"
                    report += f"   - 📋 账号ID: `{account.account_id}`\n"
                    report += f"   - 🏢 {payer_info}\n"
                    report += f"   - 📅 首次出现: {first_seen or '未知'}\n"
                    report += f"   - 📊 状态: {account.status}\n"
                    report += f"   - 🏷️  标签: {account.tags or '无'}\n"
                    report += "\n"
                
                report += "\n"
        
        # 详细的移除Linked账号信息
        if removed_linked_ids:
            report += "## ❌ 移除Linked账号详细信息\n\n"
            
            # 按Payer分组显示
            removed_by_payer = defaultdict(list)
            for linked_id in removed_linked_ids:
                linked_account = linked1[linked_id]
                payer_id = linked_account.payer_id
                payer_name = get_payer_name_by_id(customer, payer_id, date1)
                last_seen = find_account_last_appearance(customer, linked_id, "LINKED")
                
                removed_by_payer[payer_id].append({
                    "account": linked_account,
                    "payer_name": payer_name,
                    "payer_id": payer_id,
                    "last_seen": last_seen
                })
            
            for payer_id, linked_list in removed_by_payer.items():
                payer_name = linked_list[0]["payer_name"]
                report += f"### 🏢 Payer: {payer_name} ({payer_id})\n"
                report += f"**移除 {len(linked_list)} 个Linked账号:**\n\n"
                
                for i, item in enumerate(linked_list, 1):
                    account = item["account"]
                    last_seen = item["last_seen"]
                    payer_info = f"原挂在Payer: **{item['payer_name']}** ({item['payer_id']})"
                    report += f"{i}. **{account.account_name}**\n"
                    report += f"   - 📋 账号ID: `{account.account_id}`\n"
                    report += f"   - 🏢 {payer_info}\n"
                    report += f"   - 📅 最后出现: {last_seen or '未知'}\n"
                    report += f"   - 📊 状态: {account.status}\n"
                    report += f"   - 🏷️  标签: {account.tags or '无'}\n"
                    report += "\n"
                
                report += "\n"
        
        # 如果没有变化
        if not new_linked_ids and not removed_linked_ids:
            report += "## ✅ 无Linked账号变化\n\n"
            report += "在指定的时间段内，没有发现任何Linked账号的新增或移除。\n"
        
        # 汇总统计
        report += "## 📈 汇总统计\n\n"
        report += f"- **{date1}** Linked账号总数: {len(linked1)} 个\n"
        report += f"- **{date2}** Linked账号总数: {len(linked2)} 个\n"
        report += f"- **净变化**: {len(linked2) - len(linked1):+d} 个\n"
        
        if new_linked_ids or removed_linked_ids:
            # 按Payer统计变化
            all_affected_payers = set()
            if new_linked_ids:
                for linked_id in new_linked_ids:
                    all_affected_payers.add(linked2[linked_id].payer_id)
            if removed_linked_ids:
                for linked_id in removed_linked_ids:
                    all_affected_payers.add(linked1[linked_id].payer_id)
            
            report += f"- **受影响的Payer账号**: {len(all_affected_payers)} 个\n"
        
        return report
        
    except Exception as e:
        return f"获取详细Linked变化信息失败: {str(e)}"


@mcp.tool()
def analyze_single_date_accounts(
    customer: str = Field(description="客户名称 (如: customer1, customer2)"),
    date: str = Field(description="分析日期 (格式: 0731)")
) -> str:
    """分析指定客户在特定日期的完整账号情况，适用于单日数据分析"""
    
    try:
        # 加载指定日期的数据
        accounts = load_accounts_data(customer, date)
        analysis = analyze_enterprise_accounts(accounts)
        
        # 生成详细的单日分析报告
        report = f"""# 📊 {customer} 账号情况详细分析 ({date})

## 🔢 整体统计概览
- **总账号数**: {len(accounts)} 个
- **Payer账号**: {analysis['total_payers']} 个
- **Linked账号**: {analysis['total_linked']} 个
- **Payer/Linked比例**: 1:{analysis['total_linked']/analysis['total_payers']:.1f} (每个Payer平均管理{analysis['total_linked']/analysis['total_payers']:.1f}个Linked账号)

## 🏢 Payer账号详细分析

### 📋 所有Payer账号列表
"""
        
        # 按Linked账号数量排序显示Payer账号
        payer_with_counts = []
        for payer in analysis['payer_accounts']:
            linked_accounts = analysis['payer_to_linked'].get(payer.account_id, [])
            linked_count = len(linked_accounts)
            payer_with_counts.append((payer, linked_count, linked_accounts))
        
        # 按Linked账号数量降序排序
        payer_with_counts.sort(key=lambda x: x[1], reverse=True)
        
        for i, (payer, linked_count, linked_accounts) in enumerate(payer_with_counts, 1):
            report += f"""
### {i}. **{payer.account_name}** (ID: {payer.account_id})
- 📊 状态: {payer.status}
- 🔗 管理的Linked账号数: {linked_count} 个
- 🏷️  标签: {payer.tags or '无'}
"""
            
            if linked_count > 0:
                report += f"- 📋 下属Linked账号详细列表:\n"
                for j, linked in enumerate(linked_accounts, 1):
                    tags_info = f"标签: {linked.tags}" if linked.tags else "标签: 无"
                    report += f"  {j}. **{linked.account_name}** (ID: {linked.account_id}) - 状态: {linked.status} - {tags_info}\n"
            else:
                report += f"- 📋 下属Linked账号: 无\n"
        
        # 业务分析
        report += f"""

## 🏷️  业务标签分析

### 标签使用统计
"""
        
        # 统计标签使用情况
        tag_stats = {}
        tagged_accounts = 0
        
        for account in accounts:
            if account.tags:
                tagged_accounts += 1
                # 分割标签（可能有多个标签用分号或逗号分隔）
                tags = [tag.strip() for tag in account.tags.replace(';', ',').split(',') if tag.strip()]
                for tag in tags:
                    tag_stats[tag] = tag_stats.get(tag, 0) + 1
        
        report += f"- 有标签的账号: {tagged_accounts} 个 ({tagged_accounts/len(accounts)*100:.1f}%)\n"
        report += f"- 无标签的账号: {len(accounts) - tagged_accounts} 个 ({(len(accounts) - tagged_accounts)/len(accounts)*100:.1f}%)\n"
        
        if tag_stats:
            report += f"\n### 标签分布 (前10个)\n"
            sorted_tags = sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)
            for tag, count in sorted_tags[:10]:
                report += f"- **{tag}**: {count} 个账号\n"
        
        # 账号状态分析
        report += f"""

## 📊 账号状态分析

### 状态分布
"""
        
        status_stats = {}
        for account in accounts:
            status = account.status or 'Unknown'
            status_stats[status] = status_stats.get(status, 0) + 1
        
        for status, count in sorted(status_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(accounts) * 100
            report += f"- **{status}**: {count} 个账号 ({percentage:.1f}%)\n"
        
        # 管理效率分析
        report += f"""

## 📈 管理效率分析

### Payer账号管理负载分布
"""
        
        # 按管理的Linked账号数量分组
        load_distribution = {}
        for _, linked_count, _ in payer_with_counts:
            if linked_count == 0:
                category = "无Linked账号"
            elif linked_count <= 2:
                category = "轻负载 (1-2个)"
            elif linked_count <= 5:
                category = "中负载 (3-5个)"
            elif linked_count <= 10:
                category = "重负载 (6-10个)"
            else:
                category = "超重负载 (10+个)"
            
            load_distribution[category] = load_distribution.get(category, 0) + 1
        
        for category, count in load_distribution.items():
            percentage = count / len(payer_with_counts) * 100
            report += f"- **{category}**: {count} 个Payer ({percentage:.1f}%)\n"
        
        # 建议和观察
        report += f"""

## 💡 关键观察和建议

### 📋 规模特征
- 账号总规模: {len(accounts)} 个 ({'大型' if len(accounts) > 100 else '中型' if len(accounts) > 50 else '小型'}规模)
- 管理结构: {'分散式' if analysis['total_payers'] > analysis['total_linked']/3 else '集中式'}管理 (Payer占比{analysis['total_payers']/len(accounts)*100:.1f}%)

### 🎯 管理建议
"""
        
        # 根据数据特征生成建议
        avg_linked_per_payer = analysis['total_linked'] / analysis['total_payers'] if analysis['total_payers'] > 0 else 0
        
        if avg_linked_per_payer > 8:
            report += f"- ⚠️  平均每个Payer管理{avg_linked_per_payer:.1f}个Linked账号，建议考虑增加Payer账号以降低管理复杂度\n"
        elif avg_linked_per_payer < 2:
            report += f"- 💡 平均每个Payer仅管理{avg_linked_per_payer:.1f}个Linked账号，可考虑整合部分Payer账号提高效率\n"
        else:
            report += f"- ✅ 平均每个Payer管理{avg_linked_per_payer:.1f}个Linked账号，管理负载较为合理\n"
        
        if tagged_accounts / len(accounts) < 0.5:
            report += f"- 📝 仅{tagged_accounts/len(accounts)*100:.1f}%的账号有标签，建议完善账号标签以便更好地分类管理\n"
        else:
            report += f"- ✅ {tagged_accounts/len(accounts)*100:.1f}%的账号已有标签，标签使用情况良好\n"
        
        # 如果是单日数据，给出特别说明
        available_dates = get_available_dates(customer)
        if len(available_dates) == 1:
            report += f"""
### 📅 数据说明
- 当前仅有{date}一天的数据，无法进行趋势分析
- 建议后续收集更多日期的数据以进行变化趋势分析
- 可使用 `compare_payer_changes()` 和 `get_detailed_linked_changes()` 进行对比分析
"""
        
        return report
        
    except Exception as e:
        return f"分析客户 {customer} 在 {date} 的账号情况失败: {str(e)}"


# ============ MCP Resources ============

@mcp.resource("customer-data://{customer}")
def get_customer_data_resource(customer: str) -> str:
    """获取特定客户的基本信息资源"""
    try:
        dates = get_available_dates(customer)
        if not dates:
            return f"客户 {customer} 没有可用数据"
        
        latest_date = dates[-1]
        accounts = load_accounts_data(customer, latest_date)
        analysis = analyze_enterprise_accounts(accounts)
        
        resource_data = f"""# 客户数据资源: {customer}

## 基本信息
- 客户名称: {customer}
- 数据更新日期: {latest_date}
- 可用数据日期: {', '.join(dates)}

## 账号统计
- Payer账号总数: {analysis['total_payers']}
- Linked账号总数: {analysis['total_linked']}
- 总账号数: {len(accounts)}

## 数据文件路径
- 数据目录: {DATA_ROOT_DIR}/{customer}/
- 最新数据文件: {customer}-CMC-accounts-{latest_date}.csv

## 使用说明
使用相关工具函数分析此客户的详细账号变化情况。
"""
        return resource_data
        
    except Exception as e:
        return f"获取客户 {customer} 数据资源失败: {str(e)}"


@mcp.resource("account-data://{customer}/{date}")
def get_account_data_resource(customer: str, date: str) -> str:
    """获取特定客户特定日期的原始账号数据资源"""
    try:
        accounts = load_accounts_data(customer, date)
        analysis = analyze_enterprise_accounts(accounts)
        
        resource_data = f"""# 账号数据资源: {customer} - {date}

## 数据概览
- 数据日期: {date}
- 总账号数: {len(accounts)}
- Enterprise账号数: {len([acc for acc in accounts if acc.is_enterprise()])}

## 账号分类统计
- Payer账号: {analysis['total_payers']} 个
- Linked账号: {analysis['total_linked']} 个

## Payer账号列表
"""
        
        for payer in analysis['payer_accounts'][:10]:  # 显示前10个
            linked_count = len(analysis['payer_to_linked'].get(payer.account_id, []))
            resource_data += f"- {payer.account_name} ({payer.account_id}) - {linked_count}个Linked账号\n"
        
        if len(analysis['payer_accounts']) > 10:
            resource_data += f"- ... 还有 {len(analysis['payer_accounts']) - 10} 个Payer账号\n"
        
        resource_data += f"""
## 数据质量
- 状态为Active的账号: {len([acc for acc in accounts if acc.status == 'Active'])} 个
- 有标签的账号: {len([acc for acc in accounts if acc.tags])} 个

## 原始数据访问
使用 load_accounts_data('{customer}', '{date}') 获取完整的原始数据。
"""
        return resource_data
        
    except Exception as e:
        return f"获取账号数据资源失败: {str(e)}"


@mcp.resource("summary://{customer}/latest")
def get_customer_summary_resource(customer: str) -> str:
    """获取特定客户最新的账号摘要信息资源"""
    try:
        dates = get_available_dates(customer)
        if not dates:
            return f"客户 {customer} 没有可用数据"
        
        latest_date = dates[-1]
        accounts = load_accounts_data(customer, latest_date)
        analysis = analyze_enterprise_accounts(accounts)
        
        # 如果有多个日期，计算变化趋势
        trend_info = ""
        if len(dates) >= 2:
            prev_date = dates[-2]
            prev_accounts = load_accounts_data(customer, prev_date)
            prev_analysis = analyze_enterprise_accounts(prev_accounts)
            
            payer_change = analysis['total_payers'] - prev_analysis['total_payers']
            linked_change = analysis['total_linked'] - prev_analysis['total_linked']
            
            trend_info = f"""
## 最近变化趋势 ({prev_date} → {latest_date})
- Payer账号变化: {payer_change:+d} 个
- Linked账号变化: {linked_change:+d} 个
"""
        
        summary_data = f"""# 客户摘要: {customer} (最新数据)

## 当前状态 ({latest_date})
- Payer账号: {analysis['total_payers']} 个
- Linked账号: {analysis['total_linked']} 个
- 总账号数: {len(accounts)}

{trend_info}

## 前5大Payer账号
"""
        
        # 按Linked账号数量排序显示前5个Payer
        payer_with_counts = []
        for payer in analysis['payer_accounts']:
            linked_count = len(analysis['payer_to_linked'].get(payer.account_id, []))
            payer_with_counts.append((payer, linked_count))
        
        payer_with_counts.sort(key=lambda x: x[1], reverse=True)
        
        for i, (payer, linked_count) in enumerate(payer_with_counts[:5], 1):
            summary_data += f"{i}. {payer.account_name} ({payer.account_id}) - {linked_count}个Linked账号\n"
        
        summary_data += f"""
## 数据完整性
- 可用数据日期: {len(dates)} 个 ({dates[0]} 至 {dates[-1]})
- 最新更新: {latest_date}

## 建议操作
- 使用 compare_payer_changes() 分析账号变化
- 使用 get_detailed_linked_changes() 获取详细变化信息
- 使用 track_account_history() 追踪特定账号历史
"""
        return summary_data
        
    except Exception as e:
        return f"获取客户摘要资源失败: {str(e)}"


# ============ MCP Prompts ============

@mcp.prompt("analyze-trends")
def analyze_trends_prompt() -> str:
    """账号变化趋势分析模板"""
    return """# Enterprise账号变化趋势分析模板

## 分析目标
分析指定客户的Enterprise账号在特定时间段内的变化趋势，识别关键的业务变化和增长模式。

## 分析步骤

### 1. 数据收集
- 使用 `get_available_customers()` 获取可用客户列表
- 使用 `get_available_dates_tool(customer)` 获取指定客户的所有可用数据日期
- 选择合适的时间范围进行分析

### 2. 整体趋势分析
- 使用 `compare_payer_changes(customer, date1, date2)` 比较不同时间点的账号变化
- 关注Payer账号和Linked账号的数量变化
- 识别增长期、收缩期和稳定期

### 3. 详细变化分析
- 使用 `get_detailed_linked_changes(customer, date1, date2)` 获取详细的账号变化信息
- 分析新增账号的业务属性（通过标签和命名模式）
- 分析移除账号的原因和影响

### 4. 业务模式识别
- 根据账号命名和标签识别业务线
- 分析不同业务线的扩张或收缩趋势
- 识别新兴业务和传统业务的变化

### 5. 关键观察点
- 大规模账号变化的时间点和原因
- 新Payer账号的建立及其业务意义
- 账号管理策略的变化（如账号整合、业务分离）

## 输出格式
- 整体变化趋势图表
- 关键变化阶段分析
- 业务变化总结
- 管理建议和观察点

## 示例使用
```
customer = customer1"
dates = get_available_dates_tool(customer)
# 分析最近3个月的变化
compare_payer_changes(customer, dates[-3], dates[-1])
get_detailed_linked_changes(customer, dates[-3], dates[-1])
```
"""


@mcp.prompt("monthly-report")
def monthly_report_prompt() -> str:
    """月度报告生成模板"""
    return """# Enterprise账号月度报告模板

## 报告目标
为指定客户生成全面的月度Enterprise账号管理报告，包括账号变化、业务发展和管理建议。

## 报告结构

### 1. 执行摘要
- 本月账号变化概览
- 关键业务发展亮点
- 主要管理建议

### 2. 账号统计分析
- 当前账号总数（Payer + Linked）
- 月度变化统计
- 同比/环比分析

### 3. 详细变化分析
- 新增账号详细列表（包括业务归属）
- 移除账号分析（包括移除原因）
- 账号重组和调整情况

### 4. 业务发展分析
- 新兴业务线识别
- 业务扩张/收缩分析
- 跨业务线账号管理优化

### 5. 管理效率分析
- Payer账号管理策略
- 账号标签和分类情况
- 管理复杂度评估

### 6. 风险和建议
- 账号管理风险识别
- 优化建议
- 下月关注重点

## 数据收集清单
```
# 基础数据
customer = "客户名称"
current_month_date = "当月最新日期"
previous_month_date = "上月对应日期"

# 执行分析
monthly_summary = simple_payer_summary(customer, previous_month_date, current_month_date)
detailed_changes = get_detailed_linked_changes(customer, previous_month_date, current_month_date)
recent_trends = analyze_recent_changes(customer, 30)  # 最近30天趋势
```

## 报告质量检查
- [ ] 数据完整性验证
- [ ] 变化原因分析
- [ ] 业务影响评估
- [ ] 管理建议可操作性
- [ ] 图表和可视化清晰度

## 分发和跟进
- 报告分发对象确认
- 关键发现讨论安排
- 下月跟进计划制定
"""


@mcp.prompt("multi-customer-report")
def multi_customer_report_prompt() -> str:
    """多客户对比分析模板"""
    return """# 多客户 Enterprise账号对比分析模板

## 分析目标
对比分析多个客户的Enterprise账号管理情况，识别最佳实践和改进机会。

## 对比维度

### 1. 规模对比
- 各客户账号总数对比
- Payer/Linked账号比例分析
- 账号增长速度对比

### 2. 管理效率对比
- 平均每个Payer管理的Linked账号数
- 账号标签使用情况
- 账号命名规范程度

### 3. 业务发展对比
- 新业务线扩张速度
- 账号变化频率
- 业务多元化程度

### 4. 最佳实践识别
- 优秀的账号管理模式
- 有效的业务分离策略
- 成功的扩张管理经验

## 分析步骤

### 1. 数据收集
```
# 获取所有客户
customers = get_available_customers()

# 为每个客户收集基础数据
for customer in customers:
    dates = get_available_dates_tool(customer)
    latest_summary = simple_payer_summary(customer, dates[-2], dates[-1])
    customer_data = get_customer_data_resource(customer)
```

### 2. 横向对比分析
- 使用 `compare_customers()` 进行客户间对比
- 使用 `get_all_customers_summary()` 获取整体概览

### 3. 深度案例分析
- 选择代表性客户进行详细分析
- 识别成功模式和问题模式
- 提取可复制的管理经验

## 输出格式

### 1. 对比概览表
| 客户 | Payer账号 | Linked账号 | 总账号 | 月增长率 | 管理效率 |
|------|-----------|------------|--------|----------|----------|

### 2. 关键发现
- 规模领先客户的管理特点
- 增长最快客户的扩张策略
- 管理最优客户的最佳实践

### 3. 改进建议
- 针对各客户的具体改进建议
- 通用管理原则和最佳实践
- 行业标杆和参考案例

### 4. 行动计划
- 短期改进措施
- 中长期优化目标
- 定期评估和调整机制

## 质量保证
- 数据一致性检查
- 对比公平性确保
- 结论客观性验证
- 建议可操作性评估
"""


# ============ 主函数 ============

def main():
    """运行MCP服务器"""
    print("🚀 启动 Account Analyzer MCP服务器 (多客户版本)...")
    print(f"📁 数据根目录: {DATA_ROOT_DIR}")
    
    # 检查数据目录
    if os.path.exists(DATA_ROOT_DIR):
        customers = get_available_customers()
        print(f"🏢 发现 {len(customers)} 个客户: {', '.join(customers)}")
        
        for customer in customers:
            dates = get_available_dates(customer)
            print(f"   📅 {customer}: {len(dates)} 个数据文件")
    else:
        print(f"⚠️  数据根目录不存在: {DATA_ROOT_DIR}")
    
    print("🔧 支持的功能:")
    print("   📋 Tools: 多客户分析工具")
    print("   📦 Resources: 按客户分组的数据资源")
    print("   📝 Prompts: 多客户分析和报告模板")
    print()
    
    mcp.run()

if __name__ == "__main__":
    main()
