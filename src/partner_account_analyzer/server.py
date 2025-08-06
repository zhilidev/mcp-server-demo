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
    # Account Enterprise账号分析服务器 (深度分析增强版)

    这个服务器分析Enterprise级别账号变化情况，并新增了Overall业务分析功能和深度业务洞察分析。
    支持Tools、Resources和Prompts三种MCP功能，支持多客户分析。

    ## 多客户支持

    支持按客户分文件夹分析：
    - 客户1: /data-directory/customer1/
    - 客户2: /data-directory/customer2/
    - 其他客户可以动态添加

    ## 可用工具 (Tools)

    ### Enterprise账号分析工具 (需要customer参数)
    - `compare_payer_changes`: 比较指定客户两个日期之间的Enterprise变化
    - `get_available_dates_tool`: 获取指定客户的所有可用数据日期
    - `analyze_single_date_accounts`: 分析指定客户在特定日期的Enterprise账号情况
    - `get_detailed_linked_changes`: 获取详细的Enterprise Linked账号变化信息

    ### 🆕 深度业务分析工具 
    - `analyze_payer_detailed_distribution`: 深度分析Payer账号分布和每个Payer的详细特征
    - `analyze_industry_insights`: 从账号信息中分析推断行业特征和业务模式
    - `analyze_comprehensive_business_insights`: 综合分析业务洞察，整合多维度分析结果

    ### 🆕 Overall业务分析工具 
    - `analyze_partner_overall_business`: 分析指定客户的整体业务情况 (所有支持级别)
    - `compare_partner_overall_changes`: 比较指定客户两个日期之间的整体业务变化
    - `analyze_partner_business_segments`: 分析指定客户的业务细分情况 (通过标签识别业务线)

    ## 功能对比

    ### Enterprise专用分析 vs Overall业务分析 vs 深度业务洞察
    
    **Enterprise专用分析** :
    - 只分析Support Level为"ENTERPRISE"的账号
    - 专注于高价值客户的详细变化
    - 适用于Enterprise客户管理和优化
    
    **Overall业务分析** :
    - 分析所有支持级别的账号 (Enterprise, Business, Developer, Basic)
    - 了解partner的完整业务图景
    - 识别业务线和客户结构特征
    - 评估业务价值分布和成熟度

    **深度业务洞察** :
    - 🏢 **Payer分布分析**: 详细分析每个Payer的管理负载和特征
    - 🏭 **行业特征识别**: 从账号名称和标签推断行业和业务模式
    - 📝 **命名模式分析**: 分析账号命名规律，评估管理规范化程度
    - 🎯 **综合业务洞察**: 整合多维度分析，提供战略建议和成熟度评估

    ## 深度分析功能详解

    ### 🏢 Payer分布深度分析
    - **负载分布**: 分析每个Payer管理的Linked账号数量分布
    - **支持级别分析**: 每个Payer下属账号的支持级别构成
    - **业务标签分析**: 基于标签的业务线识别和分布
    - **管理效率评估**: 基尼系数计算管理负载均衡度
    - **优化建议**: 基于负载分析的管理结构优化建议

    ### 🏭 行业特征智能识别
    - **关键词匹配**: 基于10大行业的关键词库进行智能匹配
    - **行业分布**: 计算各行业的信号强度和占比
    - **多样性评估**: 评估业务的行业多元化程度
    - **主要行业识别**: 识别客户的主要业务领域
    - **业务模式推断**: 基于行业特征推断业务模式

    ### 📝 命名模式深度分析
    - **模式识别**: 识别7种主要命名模式 (环境、区域、功能、团队、项目、编号、层级)
    - **一致性评分**: 计算命名规范化程度得分
    - **架构推断**: 基于命名模式推断技术架构特征
    - **成熟度评估**: 评估组织的技术和管理成熟度
    - **规范化建议**: 提供命名规范优化建议

    ### 🎯 综合业务洞察
    - **多维度整合**: 整合Payer分布、行业特征、命名模式等分析结果
    - **成熟度评估**: 5个维度的业务成熟度评分系统
    - **关键发现**: 自动识别和总结关键业务特征
    - **战略建议**: 基于分析结果生成具体的改进建议
    - **监控指标**: 推荐关键业务指标和监控方案

    ## 可用资源 (Resources)

    - `customer-data://{customer}`: 访问特定客户的基本信息 (Enterprise数据)
    - `account-data://{customer}/{date}`: 访问特定客户特定日期的原始账号数据 (Enterprise数据)
    - `summary://{customer}/latest`: 获取特定客户最新的账号摘要信息 (Enterprise数据)

    ## 可用提示 (Prompts)

    - `analyze-trends`: 账号变化趋势分析模板
    - `monthly-report`: 月度报告生成模板
    - `overall-business-analysis`: Overall业务分析模板 

    ## 数据来源

    分析指定数据目录下按客户分组的CSV文件。
    - Enterprise分析: 只处理Support Level为"ENTERPRISE"的记录
    - Overall分析: 处理所有Support Level的记录
    - 深度分析: 基于所有账号数据进行多维度分析

    ## 使用方法

    ### Enterprise分析 
    1. 分析Enterprise变化: compare_payer_changes(customer, date1, date2)
    2. 获取详细信息: get_detailed_linked_changes(customer, date1, date2)
    3. 获取可用日期: get_available_dates_tool(customer)

    ### Overall业务分析
    1. 整体业务分析: analyze_partner_overall_business(customer, date)
    2. 业务变化对比: compare_partner_overall_changes(customer, date1, date2)
    3. 业务细分分析: analyze_partner_business_segments(customer, date)

    ### 深度业务洞察
    1. Payer分布分析: analyze_payer_detailed_distribution(customer, date)
    2. 行业特征分析: analyze_industry_insights(customer, date)
    3. 综合业务洞察: analyze_comprehensive_business_insights(customer, date)

    ## 分析维度对比

    | 分析类型 | 数据范围 | 主要用途 | 分析深度 |
    |---------|---------|---------|---------|
    | Enterprise专用 | 仅Enterprise账号 | 高价值客户管理 | 基础分析 |
    | Overall业务 | 所有支持级别 | 完整业务图景 | 中等分析 |
    | 深度洞察 | 所有账号+智能推断 | 战略决策支持 | 深度分析 |

    ## 日期格式
    日期格式为4位数字，如：0723, 0730, 0731
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
    
    def is_business(self) -> bool:
        """检查是否为Business级别"""
        return self.support_level.upper() == "BUSINESS"
    
    def is_developer(self) -> bool:
        """检查是否为Developer级别"""
        return self.support_level.upper() == "DEVELOPER"
    
    def is_basic(self) -> bool:
        """检查是否为Basic级别"""
        return self.support_level.upper() == "BASIC"
    
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
            accounts.append(account)  # 加载所有账号，不再只限制Enterprise
    
    return accounts

def load_enterprise_accounts_data(customer: str, date: str) -> List[AccountRecord]:
    """加载指定客户指定日期的Enterprise账号数据（保持向后兼容）"""
    all_accounts = load_accounts_data(customer, date)
    return [account for account in all_accounts if account.is_enterprise()]

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
    enterprise_accounts = [account for account in accounts if account.is_enterprise()]
    payer_accounts = []
    linked_accounts = []
    payer_to_linked = defaultdict(list)
    
    for account in enterprise_accounts:
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
        "total_accounts": len(enterprise_accounts)
    }

def analyze_all_accounts(accounts: List[AccountRecord]) -> Dict:
    """分析所有账号数据（不限制支持级别）"""
    # 按支持级别分类
    support_level_stats = defaultdict(int)
    account_type_stats = defaultdict(int)
    status_stats = defaultdict(int)
    
    payer_accounts = []
    linked_accounts = []
    payer_to_linked = defaultdict(list)
    
    # 按支持级别分组
    enterprise_accounts = []
    business_accounts = []
    developer_accounts = []
    basic_accounts = []
    other_accounts = []
    
    for account in accounts:
        # 统计支持级别
        support_level_stats[account.support_level] += 1
        account_type_stats[account.account_type] += 1
        status_stats[account.status] += 1
        
        # 分类账号类型
        if account.is_payer():
            payer_accounts.append(account)
        elif account.is_linked():
            linked_accounts.append(account)
            payer_to_linked[account.payer_id].append(account)
        
        # 按支持级别分组
        if account.is_enterprise():
            enterprise_accounts.append(account)
        elif account.is_business():
            business_accounts.append(account)
        elif account.is_developer():
            developer_accounts.append(account)
        elif account.is_basic():
            basic_accounts.append(account)
        else:
            other_accounts.append(account)
    
    return {
        "all_accounts": accounts,
        "payer_accounts": payer_accounts,
        "linked_accounts": linked_accounts,
        "payer_to_linked": dict(payer_to_linked),
        "total_payers": len(payer_accounts),
        "total_linked": len(linked_accounts),
        "total_accounts": len(accounts),
        
        # 按支持级别分组
        "enterprise_accounts": enterprise_accounts,
        "business_accounts": business_accounts,
        "developer_accounts": developer_accounts,
        "basic_accounts": basic_accounts,
        "other_accounts": other_accounts,
        
        # 统计信息
        "support_level_stats": dict(support_level_stats),
        "account_type_stats": dict(account_type_stats),
        "status_stats": dict(status_stats),
        
        # 支持级别计数
        "total_enterprise": len(enterprise_accounts),
        "total_business": len(business_accounts),
        "total_developer": len(developer_accounts),
        "total_basic": len(basic_accounts),
        "total_other": len(other_accounts)
    }

# ============ 基础分析工具 ============

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
        accounts1 = load_enterprise_accounts_data(customer, date1)  # 使用Enterprise专用函数
        accounts2 = load_enterprise_accounts_data(customer, date2)  # 使用Enterprise专用函数
        
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
        accounts1 = load_enterprise_accounts_data(customer, date1)  # 使用Enterprise专用函数
        accounts2 = load_enterprise_accounts_data(customer, date2)  # 使用Enterprise专用函数
        
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
        accounts1 = load_enterprise_accounts_data(customer, date1)  # 使用Enterprise专用函数
        accounts2 = load_enterprise_accounts_data(customer, date2)  # 使用Enterprise专用函数
        
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
        accounts = load_enterprise_accounts_data(customer, date)  # 使用Enterprise专用函数
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
        return f"❌ 分析过程中发生错误: {str(e)}"

# ============ 深度分析工具 ============

def analyze_payer_distribution(accounts: List[AccountRecord]) -> Dict:
    """深度分析Payer账号分布和特征"""
    payer_accounts = [account for account in accounts if account.is_payer()]
    linked_accounts = [account for account in accounts if account.is_linked()]
    
    # 按Payer分组Linked账号
    payer_to_linked = defaultdict(list)
    for linked in linked_accounts:
        payer_to_linked[linked.payer_id].append(linked)
    
    # 分析每个Payer的详细信息
    payer_analysis = []
    for payer in payer_accounts:
        linked_list = payer_to_linked.get(payer.account_id, [])
        
        # 分析Linked账号的支持级别分布
        support_level_dist = defaultdict(int)
        for linked in linked_list:
            support_level_dist[linked.support_level] += 1
        
        # 分析标签分布
        tag_analysis = defaultdict(int)
        for linked in linked_list:
            if linked.tags:
                tags = [tag.strip() for tag in linked.tags.replace(';', ',').split(',') if tag.strip()]
                for tag in tags:
                    tag_analysis[tag] += 1
        
        payer_info = {
            'payer': payer,
            'linked_count': len(linked_list),
            'linked_accounts': linked_list,
            'support_level_distribution': dict(support_level_dist),
            'tag_distribution': dict(tag_analysis),
            'avg_linked_per_support_level': len(linked_list) / max(1, len(support_level_dist))
        }
        payer_analysis.append(payer_info)
    
    # 按管理的账号数量排序
    payer_analysis.sort(key=lambda x: x['linked_count'], reverse=True)
    
    return {
        'payer_analysis': payer_analysis,
        'total_payers': len(payer_accounts),
        'total_linked': len(linked_accounts),
        'avg_linked_per_payer': len(linked_accounts) / max(1, len(payer_accounts)),
        'payer_load_distribution': _calculate_payer_load_distribution(payer_analysis)
    }

def _calculate_payer_load_distribution(payer_analysis: List[Dict]) -> Dict:
    """计算Payer负载分布"""
    load_categories = {
        'no_linked': 0,      # 0个Linked
        'light_load': 0,     # 1-3个Linked
        'medium_load': 0,    # 4-10个Linked
        'heavy_load': 0,     # 11-20个Linked
        'super_heavy': 0     # 20+个Linked
    }
    
    for payer_info in payer_analysis:
        linked_count = payer_info['linked_count']
        if linked_count == 0:
            load_categories['no_linked'] += 1
        elif linked_count <= 3:
            load_categories['light_load'] += 1
        elif linked_count <= 10:
            load_categories['medium_load'] += 1
        elif linked_count <= 20:
            load_categories['heavy_load'] += 1
        else:
            load_categories['super_heavy'] += 1
    
    return load_categories

def infer_industry_from_account_info(accounts: List[AccountRecord]) -> Dict:
    """从账号信息推断行业特征"""
    
    # 行业关键词映射
    industry_keywords = {
        'technology': ['tech', 'software', 'dev', 'api', 'cloud', 'data', 'ai', 'ml', 'analytics'],
        'finance': ['bank', 'finance', 'payment', 'trading', 'fintech', 'credit', 'loan', 'insurance'],
        'healthcare': ['health', 'medical', 'hospital', 'pharma', 'bio', 'clinic', 'patient'],
        'retail': ['retail', 'shop', 'store', 'ecommerce', 'marketplace', 'commerce', 'sales'],
        'media': ['media', 'content', 'streaming', 'video', 'audio', 'broadcast', 'news'],
        'education': ['edu', 'school', 'university', 'learning', 'training', 'course'],
        'gaming': ['game', 'gaming', 'entertainment', 'mobile', 'studio'],
        'logistics': ['logistics', 'shipping', 'delivery', 'transport', 'supply'],
        'manufacturing': ['manufacturing', 'factory', 'production', 'industrial'],
        'government': ['gov', 'government', 'public', 'municipal', 'federal']
    }
    
    industry_scores = defaultdict(int)
    account_industry_mapping = {}
    
    for account in accounts:
        account_text = f"{account.account_name} {account.tags or ''}".lower()
        account_industries = []
        
        for industry, keywords in industry_keywords.items():
            for keyword in keywords:
                if keyword in account_text:
                    industry_scores[industry] += 1
                    if industry not in account_industries:
                        account_industries.append(industry)
        
        account_industry_mapping[account.account_id] = account_industries
    
    # 计算行业多样性
    total_accounts = len(accounts)
    industry_distribution = {}
    for industry, score in industry_scores.items():
        industry_distribution[industry] = {
            'score': score,
            'percentage': (score / total_accounts) * 100 if total_accounts > 0 else 0
        }
    
    # 确定主要行业
    primary_industries = sorted(industry_distribution.items(), 
                              key=lambda x: x[1]['score'], reverse=True)[:3]
    
    return {
        'industry_distribution': industry_distribution,
        'primary_industries': primary_industries,
        'account_industry_mapping': account_industry_mapping,
        'industry_diversity_score': len([i for i in industry_scores.values() if i > 0]),
        'total_industry_signals': sum(industry_scores.values())
    }

def analyze_account_naming_patterns(accounts: List[AccountRecord]) -> Dict:
    """分析账号命名模式以获取更多业务洞察"""
    
    naming_patterns = {
        'environment_based': 0,  # prod, dev, test, staging
        'region_based': 0,       # us, eu, asia, east, west
        'function_based': 0,     # api, web, db, analytics
        'team_based': 0,         # team, dept, division
        'project_based': 0,      # project, app, service
        'numbered': 0,           # 包含数字的账号
        'hierarchical': 0        # 包含层级结构的账号
    }
    
    environment_keywords = ['prod', 'production', 'dev', 'development', 'test', 'testing', 'staging', 'demo']
    region_keywords = ['us', 'eu', 'asia', 'east', 'west', 'north', 'south', 'global', 'region']
    function_keywords = ['api', 'web', 'db', 'database', 'analytics', 'data', 'ml', 'ai', 'backend', 'frontend']
    team_keywords = ['team', 'dept', 'department', 'division', 'group', 'unit']
    project_keywords = ['project', 'app', 'application', 'service', 'platform', 'system']
    
    pattern_examples = defaultdict(list)
    
    for account in accounts:
        name_lower = account.account_name.lower()
        
        # 检查各种模式
        if any(keyword in name_lower for keyword in environment_keywords):
            naming_patterns['environment_based'] += 1
            pattern_examples['environment_based'].append(account.account_name)
        
        if any(keyword in name_lower for keyword in region_keywords):
            naming_patterns['region_based'] += 1
            pattern_examples['region_based'].append(account.account_name)
        
        if any(keyword in name_lower for keyword in function_keywords):
            naming_patterns['function_based'] += 1
            pattern_examples['function_based'].append(account.account_name)
        
        if any(keyword in name_lower for keyword in team_keywords):
            naming_patterns['team_based'] += 1
            pattern_examples['team_based'].append(account.account_name)
        
        if any(keyword in name_lower for keyword in project_keywords):
            naming_patterns['project_based'] += 1
            pattern_examples['project_based'].append(account.account_name)
        
        if any(char.isdigit() for char in account.account_name):
            naming_patterns['numbered'] += 1
            pattern_examples['numbered'].append(account.account_name)
        
        if '-' in account.account_name or '_' in account.account_name:
            naming_patterns['hierarchical'] += 1
            pattern_examples['hierarchical'].append(account.account_name)
    
    # 限制示例数量
    for pattern in pattern_examples:
        pattern_examples[pattern] = pattern_examples[pattern][:5]
    
    return {
        'naming_patterns': naming_patterns,
        'pattern_examples': dict(pattern_examples),
        'total_accounts': len(accounts),
        'naming_consistency_score': _calculate_naming_consistency(accounts)
    }

def _calculate_naming_consistency(accounts: List[AccountRecord]) -> float:
    """计算命名一致性得分"""
    if len(accounts) < 2:
        return 1.0
    
    # 分析命名长度的一致性
    name_lengths = [len(account.account_name) for account in accounts]
    avg_length = sum(name_lengths) / len(name_lengths)
    length_variance = sum((length - avg_length) ** 2 for length in name_lengths) / len(name_lengths)
    
    # 分析分隔符使用的一致性
    separator_usage = defaultdict(int)
    for account in accounts:
        if '-' in account.account_name:
            separator_usage['hyphen'] += 1
        if '_' in account.account_name:
            separator_usage['underscore'] += 1
        if ' ' in account.account_name:
            separator_usage['space'] += 1
    
    # 计算一致性得分 (0-1之间)
    length_consistency = max(0, 1 - (length_variance / (avg_length ** 2)))
    separator_consistency = max(separator_usage.values()) / len(accounts) if separator_usage else 0.5
    
    return (length_consistency + separator_consistency) / 2

@mcp.tool()
def analyze_payer_detailed_distribution(
    customer: str = Field(description="客户名称 (如: 泰岳, verycloud)"),
    date: str = Field(description="分析日期 (格式: 0731)")
) -> str:
    """深度分析指定客户的Payer账号分布和每个Payer的详细特征"""
    
    try:
        # 加载指定日期的所有账号数据
        accounts = load_accounts_data(customer, date)
        payer_analysis = analyze_payer_distribution(accounts)
        
        # 生成详细的Payer分布分析报告
        report = f"""# 🏢 {customer} Payer账号深度分析报告 ({date})

## 📊 Payer账号总体概览
- **Payer账号总数**: {payer_analysis['total_payers']} 个
- **Linked账号总数**: {payer_analysis['total_linked']} 个
- **平均每个Payer管理**: {payer_analysis['avg_linked_per_payer']:.1f} 个Linked账号

## 📈 Payer负载分布分析
"""
        
        load_dist = payer_analysis['payer_load_distribution']
        total_payers = payer_analysis['total_payers']
        
        load_categories = [
            ('无Linked账号', load_dist['no_linked'], '🔴'),
            ('轻负载 (1-3个)', load_dist['light_load'], '🟢'),
            ('中负载 (4-10个)', load_dist['medium_load'], '🟡'),
            ('重负载 (11-20个)', load_dist['heavy_load'], '🟠'),
            ('超重负载 (20+个)', load_dist['super_heavy'], '🔴')
        ]
        
        for category, count, icon in load_categories:
            if count > 0:
                percentage = (count / total_payers) * 100 if total_payers > 0 else 0
                report += f"- {icon} **{category}**: {count} 个Payer ({percentage:.1f}%)\n"
        
        # 详细的Payer账号分析
        report += f"""

## 🔍 Top 10 Payer账号详细分析

### 按管理的Linked账号数量排序
"""
        
        for i, payer_info in enumerate(payer_analysis['payer_analysis'][:10], 1):
            payer = payer_info['payer']
            linked_count = payer_info['linked_count']
            support_dist = payer_info['support_level_distribution']
            tag_dist = payer_info['tag_distribution']
            
            report += f"""
### {i}. **{payer.account_name}** (ID: {payer.account_id})
- 📊 **管理规模**: {linked_count} 个Linked账号
- 🏷️  **Payer标签**: {payer.tags or '无'}
- 📈 **状态**: {payer.status}

#### 下属账号支持级别分布:
"""
            
            if support_dist:
                for level, count in sorted(support_dist.items(), key=lambda x: x[1], reverse=True):
                    level_icon = {"ENTERPRISE": "🏆", "BUSINESS": "💼", "DEVELOPER": "👨‍💻", "BASIC": "📱"}.get(level, "❓")
                    percentage = (count / linked_count) * 100 if linked_count > 0 else 0
                    report += f"- {level_icon} **{level}**: {count} 个 ({percentage:.1f}%)\n"
            else:
                report += "- 无Linked账号\n"
            
            if tag_dist:
                report += f"\n#### 下属账号业务标签分布:\n"
                for tag, count in sorted(tag_dist.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / linked_count) * 100 if linked_count > 0 else 0
                    report += f"- 🏷️ **{tag}**: {count} 个账号 ({percentage:.1f}%)\n"
        
        # 管理效率分析
        report += f"""

## 📊 管理效率分析

### 负载均衡评估
"""
        
        if load_dist['super_heavy'] > 0:
            report += f"- ⚠️ **管理过载风险**: {load_dist['super_heavy']} 个Payer管理超过20个Linked账号，建议考虑分拆\n"
        
        if load_dist['no_linked'] > total_payers * 0.2:
            report += f"- 💡 **资源优化机会**: {load_dist['no_linked']} 个Payer无Linked账号，可考虑整合或重新分配\n"
        
        optimal_payers = load_dist['light_load'] + load_dist['medium_load']
        if optimal_payers > total_payers * 0.6:
            report += f"- ✅ **管理结构良好**: {optimal_payers} 个Payer ({(optimal_payers/total_payers)*100:.1f}%) 处于最佳管理负载范围\n"
        
        # 业务集中度分析
        report += f"""

### 业务集中度分析
"""
        
        # 计算基尼系数来衡量Linked账号分布的不均匀程度
        linked_counts = [info['linked_count'] for info in payer_analysis['payer_analysis']]
        if linked_counts:
            gini_coefficient = _calculate_gini_coefficient(linked_counts)
            if gini_coefficient > 0.7:
                report += f"- 📊 **高度集中**: 基尼系数 {gini_coefficient:.2f}，少数Payer管理大部分Linked账号\n"
            elif gini_coefficient > 0.4:
                report += f"- 📊 **中度集中**: 基尼系数 {gini_coefficient:.2f}，管理负载分布不均\n"
            else:
                report += f"- 📊 **分布均匀**: 基尼系数 {gini_coefficient:.2f}，管理负载分布相对均匀\n"
        
        return report
        
    except Exception as e:
        return f"分析客户 {customer} Payer分布失败: {str(e)}"

def _calculate_gini_coefficient(values: List[int]) -> float:
    """计算基尼系数"""
    if not values or all(v == 0 for v in values):
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    cumsum = sum(sorted_values)
    
    if cumsum == 0:
        return 0.0
    
    # 计算基尼系数
    gini = 0
    for i, value in enumerate(sorted_values):
        gini += (2 * (i + 1) - n - 1) * value
    
    return gini / (n * cumsum)

@mcp.tool()
def analyze_industry_insights(
    customer: str = Field(description="客户名称 (如: 泰岳, verycloud)"),
    date: str = Field(description="分析日期 (格式: 0731)")
) -> str:
    """从账号信息中分析推断行业特征和业务模式"""
    
    try:
        # 加载指定日期的所有账号数据
        accounts = load_accounts_data(customer, date)
        industry_analysis = infer_industry_from_account_info(accounts)
        naming_analysis = analyze_account_naming_patterns(accounts)
        
        # 生成行业洞察分析报告
        report = f"""# 🏭 {customer} 行业特征与业务模式分析 ({date})

## 🎯 行业特征识别

### 主要行业分布
"""
        
        industry_dist = industry_analysis['industry_distribution']
        if industry_dist:
            # 按得分排序显示行业分布
            sorted_industries = sorted(industry_dist.items(), 
                                     key=lambda x: x[1]['score'], reverse=True)
            
            for industry, data in sorted_industries[:5]:  # 显示前5个行业
                if data['score'] > 0:
                    industry_icons = {
                        'technology': '💻',
                        'finance': '💰',
                        'healthcare': '🏥',
                        'retail': '🛒',
                        'media': '📺',
                        'education': '🎓',
                        'gaming': '🎮',
                        'logistics': '🚚',
                        'manufacturing': '🏭',
                        'government': '🏛️'
                    }
                    icon = industry_icons.get(industry, '🏢')
                    report += f"- {icon} **{industry.title()}**: {data['score']} 个信号 ({data['percentage']:.1f}%)\n"
        else:
            report += "- ❓ 无法从账号信息中识别明确的行业特征\n"
        
        # 行业多样性分析
        diversity_score = industry_analysis['industry_diversity_score']
        total_signals = industry_analysis['total_industry_signals']
        
        report += f"""

### 行业多样性评估
- **行业多样性得分**: {diversity_score} 个不同行业
- **总行业信号数**: {total_signals} 个
- **平均每账号信号**: {total_signals / len(accounts):.2f} 个

"""
        
        if diversity_score >= 5:
            report += "- 🌈 **高度多元化**: 业务涵盖多个行业领域，具有良好的风险分散\n"
        elif diversity_score >= 3:
            report += "- 🔄 **中度多元化**: 业务涉及几个主要行业，有一定的多样性\n"
        elif diversity_score >= 1:
            report += "- 🎯 **专业化聚焦**: 业务主要集中在特定行业领域\n"
        else:
            report += "- ❓ **行业特征不明**: 无法从现有信息识别明确的行业定位\n"
        
        # 命名模式分析
        report += f"""

## 📝 账号命名模式分析

### 命名规律识别
"""
        
        naming_patterns = naming_analysis['naming_patterns']
        total_accounts = naming_analysis['total_accounts']
        
        pattern_descriptions = [
            ('environment_based', '环境导向', '🌍', '基于环境的命名 (prod, dev, test)'),
            ('region_based', '区域导向', '🗺️', '基于地理区域的命名 (us, eu, asia)'),
            ('function_based', '功能导向', '⚙️', '基于功能的命名 (api, web, db)'),
            ('team_based', '团队导向', '👥', '基于团队的命名 (team, dept)'),
            ('project_based', '项目导向', '📋', '基于项目的命名 (project, app)'),
            ('numbered', '编号系统', '🔢', '使用数字编号的账号'),
            ('hierarchical', '层级结构', '🏗️', '使用分隔符的层级命名')
        ]
        
        for pattern_key, pattern_name, icon, description in pattern_descriptions:
            count = naming_patterns.get(pattern_key, 0)
            if count > 0:
                percentage = (count / total_accounts) * 100
                report += f"- {icon} **{pattern_name}**: {count} 个账号 ({percentage:.1f}%) - {description}\n"
        
        # 命名一致性分析
        consistency_score = naming_analysis['naming_consistency_score']
        report += f"""

### 命名规范化程度
- **一致性得分**: {consistency_score:.2f} (0-1之间，越高越一致)

"""
        
        if consistency_score >= 0.8:
            report += "- ✅ **高度规范化**: 账号命名非常一致，管理规范良好\n"
        elif consistency_score >= 0.6:
            report += "- 💼 **中度规范化**: 账号命名较为一致，有一定的管理规范\n"
        elif consistency_score >= 0.4:
            report += "- 📱 **初步规范化**: 账号命名有一定规律，但仍有改进空间\n"
        else:
            report += "- ⚠️ **规范化不足**: 账号命名缺乏一致性，建议建立命名规范\n"
        
        # 业务模式推断
        report += f"""

## 🔍 业务模式推断

### 组织架构特征
"""
        
        # 基于命名模式推断组织架构
        if naming_patterns.get('team_based', 0) > total_accounts * 0.3:
            report += "- 👥 **团队导向型组织**: 账号按团队划分，可能采用敏捷或DevOps模式\n"
        
        if naming_patterns.get('environment_based', 0) > total_accounts * 0.4:
            report += "- 🌍 **环境分离型**: 严格的开发/测试/生产环境分离，规范的软件开发流程\n"
        
        if naming_patterns.get('region_based', 0) > total_accounts * 0.3:
            report += "- 🗺️ **全球化运营**: 按地理区域部署，可能是跨国或多地区业务\n"
        
        if naming_patterns.get('function_based', 0) > total_accounts * 0.4:
            report += "- ⚙️ **微服务架构**: 按功能模块划分账号，可能采用微服务或SOA架构\n"
        
        # 技术成熟度评估
        report += f"""

### 技术成熟度评估
"""
        
        tech_indicators = 0
        if 'technology' in [item[0] for item in industry_analysis['primary_industries'][:3]]:
            tech_indicators += 2
        if naming_patterns.get('environment_based', 0) > 0:
            tech_indicators += 1
        if naming_patterns.get('function_based', 0) > 0:
            tech_indicators += 1
        if consistency_score > 0.6:
            tech_indicators += 1
        
        if tech_indicators >= 4:
            report += "- 🚀 **高技术成熟度**: 具备先进的技术架构和管理实践\n"
        elif tech_indicators >= 2:
            report += "- 💼 **中等技术成熟度**: 有一定的技术基础和规范\n"
        else:
            report += "- 📱 **基础技术水平**: 技术架构相对简单，有提升空间\n"
        
        # 示例展示
        if naming_analysis['pattern_examples']:
            report += f"""

## 📋 命名模式示例

"""
            for pattern, examples in naming_analysis['pattern_examples'].items():
                if examples:
                    pattern_name = next((desc[1] for desc in pattern_descriptions if desc[0] == pattern), pattern)
                    report += f"### {pattern_name}示例:\n"
                    for example in examples[:3]:  # 只显示前3个示例
                        report += f"- `{example}`\n"
                    report += "\n"
        
        return report
        
    except Exception as e:
        return f"分析客户 {customer} 行业特征失败: {str(e)}"

# ============ 新增Overall分析工具 ============

@mcp.tool()
def analyze_comprehensive_business_insights(
    customer: str = Field(description="客户名称 (如: 泰岳, verycloud)"),
    date: str = Field(description="分析日期 (格式: 0731)")
) -> str:
    """综合分析指定客户的业务洞察，整合Payer分布、行业特征、命名模式等多维度分析"""
    
    try:
        # 加载指定日期的所有账号数据
        accounts = load_accounts_data(customer, date)
        
        # 执行多维度分析
        overall_analysis = analyze_all_accounts(accounts)
        payer_analysis = analyze_payer_distribution(accounts)
        industry_analysis = infer_industry_from_account_info(accounts)
        naming_analysis = analyze_account_naming_patterns(accounts)
        
        # 生成综合业务洞察报告
        report = f"""# 🎯 {customer} 综合业务洞察分析报告 ({date})

## 📊 执行摘要

### 核心指标概览
- **账号总规模**: {overall_analysis['total_accounts']} 个账号
- **管理架构**: {payer_analysis['total_payers']} 个Payer管理 {payer_analysis['total_linked']} 个Linked账号
- **支持级别分布**: Enterprise({overall_analysis['total_enterprise']}) | Business({overall_analysis['total_business']}) | Developer({overall_analysis['total_developer']}) | Basic({overall_analysis['total_basic']})
- **行业多样性**: {industry_analysis['industry_diversity_score']} 个行业领域
- **命名规范化**: {naming_analysis['naming_consistency_score']:.1%} 一致性得分

### 🎯 关键发现
"""
        
        # 生成关键发现
        key_findings = []
        
        # 规模特征
        if overall_analysis['total_accounts'] > 100:
            key_findings.append("🏢 **大型企业级客户**: 账号规模超过100个，属于大型企业客户")
        elif overall_analysis['total_accounts'] > 50:
            key_findings.append("🏢 **中型企业客户**: 账号规模50-100个，属于中型企业客户")
        else:
            key_findings.append("🏢 **小型企业客户**: 账号规模较小，属于小型或初创企业")
        
        # 业务价值特征
        enterprise_ratio = overall_analysis['total_enterprise'] / overall_analysis['total_accounts']
        if enterprise_ratio > 0.5:
            key_findings.append("💎 **高价值客户群体**: Enterprise账号占比超过50%，具有很高的商业价值")
        elif enterprise_ratio > 0.2:
            key_findings.append("💼 **中高价值客户**: Enterprise账号占比较高，具有良好的商业价值")
        
        # 管理效率特征
        avg_linked_per_payer = payer_analysis['avg_linked_per_payer']
        if avg_linked_per_payer > 10:
            key_findings.append("⚠️ **管理复杂度较高**: 平均每个Payer管理超过10个Linked账号")
        elif avg_linked_per_payer > 5:
            key_findings.append("📊 **管理负载适中**: 平均每个Payer管理5-10个Linked账号")
        else:
            key_findings.append("✅ **管理结构精简**: 平均每个Payer管理少于5个Linked账号")
        
        # 行业特征
        primary_industries = industry_analysis['primary_industries']
        if primary_industries and primary_industries[0][1]['score'] > 0:
            primary_industry = primary_industries[0][0]
            key_findings.append(f"🏭 **主要行业**: {primary_industry.title()} 行业特征明显")
        
        # 技术成熟度
        if naming_analysis['naming_consistency_score'] > 0.7:
            key_findings.append("🚀 **高技术成熟度**: 命名规范化程度高，管理体系成熟")
        
        for finding in key_findings:
            report += f"- {finding}\n"
        
        # 详细分析部分
        report += f"""

## 🏢 组织架构深度分析

### Payer账号管理分布
"""
        
        load_dist = payer_analysis['payer_load_distribution']
        total_payers = payer_analysis['total_payers']
        
        # 管理负载可视化
        report += f"```\n"
        report += f"Payer负载分布:\n"
        report += f"无Linked    │{'█' * (load_dist['no_linked'] * 20 // max(1, total_payers))}│ {load_dist['no_linked']} 个\n"
        report += f"轻负载(1-3) │{'█' * (load_dist['light_load'] * 20 // max(1, total_payers))}│ {load_dist['light_load']} 个\n"
        report += f"中负载(4-10)│{'█' * (load_dist['medium_load'] * 20 // max(1, total_payers))}│ {load_dist['medium_load']} 个\n"
        report += f"重负载(11+) │{'█' * ((load_dist['heavy_load'] + load_dist['super_heavy']) * 20 // max(1, total_payers))}│ {load_dist['heavy_load'] + load_dist['super_heavy']} 个\n"
        report += f"```\n"
        
        # Top 5 Payer账号
        report += f"""
### 🏆 Top 5 Payer账号 (按管理规模)
"""
        
        for i, payer_info in enumerate(payer_analysis['payer_analysis'][:5], 1):
            payer = payer_info['payer']
            linked_count = payer_info['linked_count']
            support_dist = payer_info['support_level_distribution']
            
            # 计算主要支持级别
            main_support_level = "Mixed"
            if support_dist:
                main_support_level = max(support_dist.items(), key=lambda x: x[1])[0]
            
            report += f"{i}. **{payer.account_name}** - {linked_count} 个Linked账号 (主要: {main_support_level})\n"
        
        # 行业与业务模式分析
        report += f"""

## 🏭 行业特征与业务模式

### 行业分布热力图
"""
        
        if industry_analysis['industry_distribution']:
            sorted_industries = sorted(industry_analysis['industry_distribution'].items(), 
                                     key=lambda x: x[1]['score'], reverse=True)[:5]
            
            max_score = max(item[1]['score'] for item in sorted_industries) if sorted_industries else 1
            
            report += f"```\n"
            for industry, data in sorted_industries:
                if data['score'] > 0:
                    bar_length = int((data['score'] / max_score) * 20)
                    bar = '█' * bar_length + '░' * (20 - bar_length)
                    report += f"{industry:12} │{bar}│ {data['score']} 信号 ({data['percentage']:.1f}%)\n"
            report += f"```\n"
        
        # 命名模式分析
        report += f"""

### 命名模式特征分析
"""
        
        naming_patterns = naming_analysis['naming_patterns']
        total_accounts = naming_analysis['total_accounts']
        
        pattern_insights = []
        if naming_patterns.get('environment_based', 0) > total_accounts * 0.3:
            pattern_insights.append("🌍 **环境分离导向**: 严格的开发/测试/生产环境管理")
        if naming_patterns.get('region_based', 0) > total_accounts * 0.2:
            pattern_insights.append("🗺️ **地理分布式**: 多区域或全球化业务部署")
        if naming_patterns.get('function_based', 0) > total_accounts * 0.3:
            pattern_insights.append("⚙️ **功能模块化**: 微服务或模块化架构特征")
        if naming_patterns.get('team_based', 0) > total_accounts * 0.2:
            pattern_insights.append("👥 **团队协作型**: 基于团队的组织架构")
        
        if pattern_insights:
            for insight in pattern_insights:
                report += f"- {insight}\n"
        else:
            report += "- 📝 **自由命名模式**: 未发现明显的命名规律，可能需要建立命名规范\n"
        
        # 业务成熟度评估
        report += f"""

## 📈 业务成熟度综合评估

### 成熟度维度评分
"""
        
        # 计算各维度成熟度得分
        scale_score = min(5, (overall_analysis['total_accounts'] // 20) + 1)  # 规模得分
        value_score = min(5, int(enterprise_ratio * 5) + 1)  # 价值得分
        management_score = min(5, int((1 - abs(avg_linked_per_payer - 5) / 10) * 5) + 1)  # 管理得分
        standardization_score = min(5, int(naming_analysis['naming_consistency_score'] * 5) + 1)  # 标准化得分
        diversity_score = min(5, industry_analysis['industry_diversity_score'])  # 多样性得分
        
        dimensions = [
            ("业务规模", scale_score, "账号数量和组织规模"),
            ("客户价值", value_score, "Enterprise客户占比"),
            ("管理效率", management_score, "Payer/Linked管理比例"),
            ("标准化程度", standardization_score, "命名和管理规范"),
            ("业务多样性", diversity_score, "行业覆盖广度")
        ]
        
        total_score = 0
        for dimension, score, description in dimensions:
            stars = "★" * score + "☆" * (5 - score)
            report += f"- **{dimension}**: {stars} ({score}/5) - {description}\n"
            total_score += score
        
        avg_score = total_score / len(dimensions)
        report += f"\n**综合成熟度得分**: {avg_score:.1f}/5.0\n"
        
        if avg_score >= 4.0:
            maturity_level = "🏆 **高度成熟**: 具备企业级管理水平和技术架构"
        elif avg_score >= 3.0:
            maturity_level = "💼 **中等成熟**: 有良好的基础，部分领域需要提升"
        elif avg_score >= 2.0:
            maturity_level = "📱 **发展阶段**: 基础设施完备，管理体系待完善"
        else:
            maturity_level = "🌱 **初期阶段**: 业务快速发展，管理体系需要建立"
        
        report += f"\n{maturity_level}\n"
        
        # 战略建议
        report += f"""

## 💡 战略建议与行动计划

### 🎯 优先改进领域
"""
        
        recommendations = []
        
        # 基于分析结果生成建议
        if load_dist['super_heavy'] > 0:
            recommendations.append("⚠️ **管理负载优化**: 考虑分拆管理超过20个Linked账号的Payer，降低管理复杂度")
        
        if enterprise_ratio < 0.3 and overall_analysis['total_business'] > 0:
            recommendations.append("📈 **客户价值提升**: 重点培育Business客户升级为Enterprise，提高整体价值")
        
        if naming_analysis['naming_consistency_score'] < 0.6:
            recommendations.append("📝 **标准化建设**: 建立统一的账号命名规范，提高管理效率")
        
        if industry_analysis['industry_diversity_score'] < 2:
            recommendations.append("🌈 **业务多元化**: 考虑拓展更多行业领域，降低业务风险")
        
        if overall_analysis['total_developer'] > overall_analysis['total_enterprise']:
            recommendations.append("🚀 **开发者生态**: 建立完善的开发者支持体系，促进技术创新")
        
        if not recommendations:
            recommendations.append("✅ **持续优化**: 当前业务结构良好，建议保持现有策略并持续监控")
        
        for rec in recommendations:
            report += f"- {rec}\n"
        
        # 监控指标建议
        report += f"""

### 📊 关键监控指标
- **规模增长率**: 月度账号总数变化
- **价值提升率**: Enterprise客户占比变化
- **管理效率**: 平均每Payer管理的Linked账号数
- **标准化进度**: 命名规范化得分变化
- **业务健康度**: 各支持级别分布均衡性

### 🔄 定期评估建议
- **月度**: 账号数量和分布变化
- **季度**: 业务价值和管理效率评估
- **年度**: 综合成熟度和战略调整评估
"""
        
        return report
        
    except Exception as e:
        return f"综合业务洞察分析失败: {str(e)}"

# ============ 新增Overall分析工具 ============

@mcp.tool()
def analyze_partner_overall_business(
    customer: str = Field(description="客户名称 (如: customer1, customer2)"),
    date: str = Field(description="分析日期 (格式: 0731)")
) -> str:
    """分析指定客户的整体业务情况，包括所有支持级别的账号"""
    
    try:
        # 加载指定日期的所有账号数据
        accounts = load_accounts_data(customer, date)
        analysis = analyze_all_accounts(accounts)
        
        # 生成详细的整体业务分析报告
        report = f"""# 🏢 {customer} 整体业务分析报告 ({date})

## 📊 总体规模概览
- **账号总数**: {analysis['total_accounts']} 个
- **Payer账号**: {analysis['total_payers']} 个 ({analysis['total_payers']/analysis['total_accounts']*100:.1f}%)
- **Linked账号**: {analysis['total_linked']} 个 ({analysis['total_linked']/analysis['total_accounts']*100:.1f}%)

## 🎯 支持级别分布
"""
        
        # 支持级别统计
        support_levels = [
            ("Enterprise", analysis['total_enterprise'], "🏆"),
            ("Business", analysis['total_business'], "💼"),
            ("Developer", analysis['total_developer'], "👨‍💻"),
            ("Basic", analysis['total_basic'], "📱"),
            ("Other", analysis['total_other'], "❓")
        ]
        
        for level_name, count, icon in support_levels:
            if count > 0:
                percentage = count / analysis['total_accounts'] * 100
                report += f"- {icon} **{level_name}**: {count} 个账号 ({percentage:.1f}%)\n"
        
        # 业务价值分析
        report += f"""

## 💰 业务价值分析
- **高价值客户** (Enterprise): {analysis['total_enterprise']} 个 ({analysis['total_enterprise']/analysis['total_accounts']*100:.1f}%)
- **中价值客户** (Business): {analysis['total_business']} 个 ({analysis['total_business']/analysis['total_accounts']*100:.1f}%)
- **开发者客户** (Developer): {analysis['total_developer']} 个 ({analysis['total_developer']/analysis['total_accounts']*100:.1f}%)
- **基础客户** (Basic): {analysis['total_basic']} 个 ({analysis['total_basic']/analysis['total_accounts']*100:.1f}%)

### 客户结构特征
"""
        
        # 分析客户结构特征
        if analysis['total_enterprise'] > analysis['total_accounts'] * 0.3:
            report += "- 🏆 **企业级主导型**: Enterprise客户占比较高，属于高价值客户群体\n"
        elif analysis['total_business'] > analysis['total_accounts'] * 0.4:
            report += "- 💼 **商业级主导型**: Business客户为主体，具有良好的商业价值\n"
        elif analysis['total_developer'] > analysis['total_accounts'] * 0.5:
            report += "- 👨‍💻 **开发者主导型**: Developer客户占主导，具有技术创新潜力\n"
        else:
            report += "- 📊 **混合型结构**: 各支持级别分布相对均衡\n"
        
        # 账号状态分析
        report += f"""

## 📈 账号状态分析
"""
        
        for status, count in sorted(analysis['status_stats'].items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                percentage = count / analysis['total_accounts'] * 100
                status_icon = "✅" if status.lower() == "active" else "⚠️" if status.lower() in ["suspended", "pending"] else "❓"
                report += f"- {status_icon} **{status}**: {count} 个账号 ({percentage:.1f}%)\n"
        
        return report
        
    except Exception as e:
        return f"分析客户 {customer} 整体业务情况失败: {str(e)}"

@mcp.tool()
def compare_partner_overall_changes(
    customer: str = Field(description="客户名称 (如: customer1, customer2)"),
    date1: str = Field(description="第一个日期 (格式: 0723)"),
    date2: str = Field(description="第二个日期 (格式: 0724)")
) -> str:
    """比较指定客户两个日期之间的整体业务变化（包括所有支持级别）"""
    
    try:
        # 加载两个日期的所有账号数据
        accounts1 = load_accounts_data(customer, date1)
        accounts2 = load_accounts_data(customer, date2)
        
        # 分析数据
        analysis1 = analyze_all_accounts(accounts1)
        analysis2 = analyze_all_accounts(accounts2)
        
        # 生成对比报告
        report = f"""# 🔄 {customer} 整体业务变化分析 ({date1} → {date2})

## 📊 总体变化概览
- **账号总数**: {analysis1['total_accounts']} → {analysis2['total_accounts']} ({analysis2['total_accounts'] - analysis1['total_accounts']:+d})
- **Payer账号**: {analysis1['total_payers']} → {analysis2['total_payers']} ({analysis2['total_payers'] - analysis1['total_payers']:+d})
- **Linked账号**: {analysis1['total_linked']} → {analysis2['total_linked']} ({analysis2['total_linked'] - analysis1['total_linked']:+d})

## 🎯 支持级别变化分析
"""
        
        # 支持级别变化对比
        support_changes = [
            ("Enterprise", analysis1['total_enterprise'], analysis2['total_enterprise'], "🏆"),
            ("Business", analysis1['total_business'], analysis2['total_business'], "💼"),
            ("Developer", analysis1['total_developer'], analysis2['total_developer'], "👨‍💻"),
            ("Basic", analysis1['total_basic'], analysis2['total_basic'], "📱"),
            ("Other", analysis1['total_other'], analysis2['total_other'], "❓")
        ]
        
        for level_name, count1, count2, icon in support_changes:
            change = count2 - count1
            if change != 0 or count2 > 0:  # 只显示有变化或有数量的级别
                change_str = f"({change:+d})" if change != 0 else ""
                report += f"- {icon} **{level_name}**: {count1} → {count2} {change_str}\n"
        
        # 业务价值变化分析
        report += f"""

## 💰 业务价值变化分析

### 高价值客户变化 (Enterprise)
"""
        
        enterprise_change = analysis2['total_enterprise'] - analysis1['total_enterprise']
        if enterprise_change > 0:
            report += f"- 📈 **增长**: 新增 {enterprise_change} 个Enterprise客户，业务价值提升\n"
        elif enterprise_change < 0:
            report += f"- 📉 **下降**: 减少 {abs(enterprise_change)} 个Enterprise客户，需要关注客户流失\n"
        else:
            report += f"- ➡️ **稳定**: Enterprise客户数量保持稳定\n"
        
        # 整体趋势分析
        total_change = analysis2['total_accounts'] - analysis1['total_accounts']
        report += f"""

## 📈 整体业务趋势分析

### 规模变化趋势
"""
        
        if total_change > 0:
            growth_rate = (total_change / analysis1['total_accounts']) * 100
            report += f"- 📈 **业务增长**: 总账号数增加 {total_change} 个，增长率 {growth_rate:.1f}%\n"
            
            # 分析增长的主要来源
            max_growth_level = max(support_changes[:-1], key=lambda x: x[2] - x[1])  # 排除Other
            if max_growth_level[2] - max_growth_level[1] > 0:
                report += f"- 🎯 **主要增长来源**: {max_growth_level[3]} {max_growth_level[0]} 级别贡献最大\n"
                
        elif total_change < 0:
            decline_rate = (abs(total_change) / analysis1['total_accounts']) * 100
            report += f"- 📉 **业务收缩**: 总账号数减少 {abs(total_change)} 个，下降率 {decline_rate:.1f}%\n"
            
            # 分析下降的主要原因
            max_decline_level = min(support_changes[:-1], key=lambda x: x[2] - x[1])  # 排除Other
            if max_decline_level[2] - max_decline_level[1] < 0:
                report += f"- ⚠️ **主要下降来源**: {max_decline_level[3]} {max_decline_level[0]} 级别下降最多\n"
        else:
            report += f"- ➡️ **业务稳定**: 总账号数保持不变\n"
        
        return report
        
    except Exception as e:
        return f"比较客户 {customer} 整体业务变化失败: {str(e)}"

@mcp.tool()
def analyze_partner_business_segments(
    customer: str = Field(description="客户名称 (如: customer1, customer2)"),
    date: str = Field(description="分析日期 (格式: 0731)")
) -> str:
    """分析指定客户的业务细分情况，通过账号标签和命名模式识别业务线"""
    
    try:
        # 加载指定日期的所有账号数据
        accounts = load_accounts_data(customer, date)
        analysis = analyze_all_accounts(accounts)
        
        # 分析业务细分
        report = f"""# 🏗️ {customer} 业务细分分析报告 ({date})

## 📊 业务线识别 (基于账号标签)
"""
        
        # 标签分析
        tag_analysis = {}
        tagged_accounts = 0
        
        for account in accounts:
            if account.tags:
                tagged_accounts += 1
                # 分割标签（可能有多个标签用分号或逗号分隔）
                tags = [tag.strip() for tag in account.tags.replace(';', ',').split(',') if tag.strip()]
                for tag in tags:
                    if tag not in tag_analysis:
                        tag_analysis[tag] = {
                            'total': 0,
                            'enterprise': 0,
                            'business': 0,
                            'developer': 0,
                            'basic': 0,
                            'payer': 0,
                            'linked': 0
                        }
                    
                    tag_analysis[tag]['total'] += 1
                    if account.is_enterprise():
                        tag_analysis[tag]['enterprise'] += 1
                    elif account.is_business():
                        tag_analysis[tag]['business'] += 1
                    elif account.is_developer():
                        tag_analysis[tag]['developer'] += 1
                    elif account.is_basic():
                        tag_analysis[tag]['basic'] += 1
                    
                    if account.is_payer():
                        tag_analysis[tag]['payer'] += 1
                    elif account.is_linked():
                        tag_analysis[tag]['linked'] += 1
        
        if tag_analysis:
            # 按账号数量排序显示业务线
            sorted_tags = sorted(tag_analysis.items(), key=lambda x: x[1]['total'], reverse=True)
            
            for i, (tag, stats) in enumerate(sorted_tags[:10], 1):  # 显示前10个业务线
                percentage = stats['total'] / analysis['total_accounts'] * 100
                report += f"""
### {i}. 🏷️ **{tag}** ({stats['total']} 个账号, {percentage:.1f}%)
- 支持级别分布: Enterprise({stats['enterprise']}) | Business({stats['business']}) | Developer({stats['developer']}) | Basic({stats['basic']})
- 账号类型分布: Payer({stats['payer']}) | Linked({stats['linked']})
"""
                
                # 业务线特征分析
                if stats['enterprise'] > stats['total'] * 0.5:
                    report += "- 💎 **高价值业务线**: Enterprise客户占主导\n"
                elif stats['developer'] > stats['total'] * 0.5:
                    report += "- 🚀 **创新业务线**: Developer客户为主，具有技术创新特征\n"
                elif stats['payer'] > stats['linked']:
                    report += "- 🏢 **独立业务线**: Payer账号较多，业务相对独立\n"
                else:
                    report += "- 🔗 **集成业务线**: Linked账号较多，业务高度集成\n"
        else:
            report += "- ❌ **无标签数据**: 当前没有账号使用标签，无法进行业务线分析\n"
        
        # 业务成熟度分析
        report += f"""

## 📈 业务成熟度评估

### 标签使用情况
- 有标签账号: {tagged_accounts} 个 ({tagged_accounts/analysis['total_accounts']*100:.1f}%)
- 无标签账号: {analysis['total_accounts'] - tagged_accounts} 个

### 管理规范化程度
"""
        
        if tagged_accounts / analysis['total_accounts'] > 0.8:
            report += "- 🏆 **高度规范化**: 标签使用率超过80%，管理非常规范\n"
        elif tagged_accounts / analysis['total_accounts'] > 0.5:
            report += "- 💼 **中度规范化**: 标签使用率超过50%，管理较为规范\n"
        elif tagged_accounts / analysis['total_accounts'] > 0.2:
            report += "- 📱 **初步规范化**: 标签使用率超过20%，开始建立管理规范\n"
        else:
            report += "- ⚠️ **规范化不足**: 标签使用率较低，建议加强账号管理规范\n"
        
        # 业务多样性分析
        unique_tags = len(tag_analysis)
        if unique_tags > 0:
            diversity_ratio = unique_tags / analysis['total_accounts']
            if diversity_ratio > 0.3:
                report += "- 🌈 **高业务多样性**: 业务线丰富，涵盖多个领域\n"
            elif diversity_ratio > 0.1:
                report += "- 🔄 **中等业务多样性**: 有一定的业务多样性\n"
            else:
                report += "- 🎯 **专注型业务**: 业务相对集中，专注特定领域\n"
        
        return report
        
    except Exception as e:
        return f"分析客户 {customer} 业务细分情况失败: {str(e)}"

@mcp.prompt("overall-business-analysis")
def overall_business_analysis_prompt() -> str:
    """Overall业务分析模板"""
    return """# Partner Overall业务分析模板

## 分析目标
全面分析指定partner的整体业务情况，不局限于Enterprise级别，了解完整的业务图景和发展趋势。

## 分析维度

### 1. 整体规模分析
- 使用 `analyze_partner_overall_business(customer, date)` 获取整体业务概览
- 分析所有支持级别的账号分布
- 评估业务规模和客户结构

### 2. 支持级别分析
- **Enterprise客户**: 高价值客户，重点关注
- **Business客户**: 中等价值，具有增长潜力
- **Developer客户**: 技术创新型，未来价值
- **Basic客户**: 基础客户，规模效应

### 3. 业务变化趋势
- 使用 `compare_partner_overall_changes(customer, date1, date2)` 分析变化
- 识别增长最快的支持级别
- 分析业务发展方向和策略调整

### 4. 业务细分分析
- 使用 `analyze_partner_business_segments(customer, date)` 识别业务线
- 通过账号标签分析业务多样性
- 评估管理规范化程度

## 分析流程

### 第一步: 基础数据收集
```
customer = "目标客户"
latest_date = "最新日期"
previous_date = "对比日期"

# 获取整体业务概览
overall_analysis = analyze_partner_overall_business(customer, latest_date)
```

### 第二步: 变化趋势分析
```
# 分析业务变化趋势
change_analysis = compare_partner_overall_changes(customer, previous_date, latest_date)
```

### 第三步: 业务细分分析
```
# 分析业务线和细分市场
segment_analysis = analyze_partner_business_segments(customer, latest_date)
```

## 关键分析指标

### 业务价值指标
- **高价值客户占比**: Enterprise账号 / 总账号数
- **成长性指标**: Developer + Business账号增长率
- **规模指标**: 总账号数和Payer/Linked比例

### 业务健康度指标
- **多样性指数**: 不同支持级别的分布均衡度
- **管理成熟度**: 标签使用率和命名规范程度
- **增长稳定性**: 各级别账号的变化趋势

## 输出格式

### 1. 执行摘要
- 业务规模和结构特征
- 主要发现和关键趋势
- 战略建议和行动计划

### 2. 详细分析报告
- 各支持级别详细分析
- 业务线识别和特征
- 变化趋势和驱动因素

### 3. 业务优化建议
- 基于数据的改进建议
- 业务发展机会识别
- 管理效率提升方案

### 4. 可视化图表
- 支持级别分布饼图
- 业务变化趋势图
- 市场地位对比图

## 应用场景

### 业务发展规划
- 评估当前业务结构合理性
- 识别增长机会和潜在风险
- 制定差异化发展策略

### 客户关系管理
- 优化客户分层管理策略
- 提升高价值客户服务质量
- 挖掘潜在客户升级机会

### 业务运营优化
- 识别业务线发展机会
- 优化资源配置和管理效率
- 制定针对性的业务策略

## 质量检查清单
- [ ] 数据完整性和准确性
- [ ] 分析逻辑的合理性
- [ ] 结论的客观性和可操作性
- [ ] 建议的具体性和可执行性
- [ ] 图表的清晰性和易读性

## 后续行动
- 定期更新分析报告
- 跟踪关键指标变化
- 实施改进措施
- 评估效果和调整策略
"""

@mcp.resource("customer-data://{customer}")
def get_customer_data_resource(customer: str) -> str:
    """获取特定客户的基本信息资源"""
    try:
        dates = get_available_dates(customer)
        if not dates:
            return f"客户 {customer} 没有可用数据"
        
        latest_date = dates[-1]
        accounts = load_enterprise_accounts_data(customer, latest_date)  # 使用Enterprise专用函数
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
        accounts = load_enterprise_accounts_data(customer, date)  # 使用Enterprise专用函数
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
        accounts = load_enterprise_accounts_data(customer, latest_date)  # 使用Enterprise专用函数
        analysis = analyze_enterprise_accounts(accounts)
        
        # 如果有多个日期，计算变化趋势
        trend_info = ""
        if len(dates) >= 2:
            prev_date = dates[-2]
            prev_accounts = load_enterprise_accounts_data(customer, prev_date)  # 使用Enterprise专用函数
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
# 手动指定需要对比的客户列表
customers = ["customer1", "customer2", "customer3"]

# 为每个客户收集基础数据
for customer in customers:
    dates = get_available_dates_tool(customer)
    latest_summary = compare_payer_changes(customer, dates[-2], dates[-1])
    customer_data = get_customer_data_resource(customer)
```

### 2. 横向对比分析
- 手动收集各客户的基础数据进行对比
- 分析各客户的账号管理模式差异

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
    print("🚀 启动 Account Analyzer MCP服务器 (深度分析增强版)...")
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
    print("   📋 Tools: Enterprise分析 + Overall业务分析 + 深度业务洞察工具")
    print("   📦 Resources: 按客户分组的数据资源")
    print("   📝 Prompts: 分析和报告模板")
    print()
    print("🆕 新增深度业务洞察功能:")
    print("   🏢 analyze_payer_detailed_distribution: Payer账号深度分布分析")
    print("   🏭 analyze_industry_insights: 行业特征和业务模式推断")
    print("   🎯 analyze_comprehensive_business_insights: 综合业务洞察分析")
    print()
    print("🌐 Overall业务分析功能:")
    print("   🌐 analyze_partner_overall_business: 整体业务分析")
    print("   🔄 compare_partner_overall_changes: 业务变化对比")
    print("   🏗️ analyze_partner_business_segments: 业务细分分析")
    print()
    print("📊 分析能力:")
    print("   • Payer负载分布和管理效率分析")
    print("   • 基于关键词的行业特征智能识别")
    print("   • 账号命名模式和规范化程度评估")
    print("   • 多维度业务成熟度评分")
    print("   • 战略建议和监控指标推荐")
    print()
    
    mcp.run()

if __name__ == "__main__":
    main()
