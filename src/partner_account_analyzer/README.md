# Account Analyzer MCP Server 

Enterprise账号分析的MCP服务器，支持多客户分析和详细的账号变化追踪。现已升级为深度业务洞察分析工具，不仅支持Enterprise账号分析，还新增了Overall业务分析和深度业务洞察功能，能够从账号数据中挖掘出行业特征、组织架构、技术成熟度等深层信息！

## 🚀 核心功能

1. **Enterprise专用分析** - 高价值客户的详细变化追踪
2. **Overall业务分析** - 完整业务图景和客户结构分析  
3. **Payer分布深度分析** - 管理负载和效率评估

## 📁 文件结构

```
mcp-server-demo/
├── src/
│   └── partner_account_analyzer/
│       ├── __init__.py                    # Python包初始化文件
│       ├── server.py                      # 核心服务器文件 (深度分析增强版)
│       └── README.md                      # 本文档
├── pyproject.toml                        # 项目配置
├── requirements.txt                      # 依赖文件
└── README.md                             # 项目主文档
```

## 🛠️ 可用工具列表

**户管理工具**
- `get_available_customers_tool()` - 获取所有可用的客户列表
- `get_available_dates_tool(customer)` - 获取指定客户的所有可用数据日期
- `compare_customers(date)` - 比较不同客户在指定日期的账号规模

**Enterprise专用分析工具**
- `compare_payer_changes(customer, date1, date2)` - 比较Enterprise Payer账号变化
- `get_detailed_linked_changes(customer, date1, date2)` - 获取详细的Linked账号变化
- `analyze_single_date_accounts(customer, date)` - 分析特定日期的Enterprise账号情况

**Overall业务分析工具**
- `analyze_partner_overall_business(customer, date)` - 整体业务情况分析
- `compare_partner_overall_changes(customer, date1, date2)` - 整体业务变化对比
- `analyze_partner_business_segments(customer, date)` - 业务细分情况分析

**深度业务洞察工具**
- `analyze_payer_detailed_distribution(customer, date)` - Payer账号深度分布分析
- `analyze_industry_insights(customer, date)` - 行业特征和业务模式推断
- `analyze_comprehensive_business_insights(customer, date)` - 综合业务洞察分析



## 数据目录结构

```
/path/to/data/directory/
├── customer1/                            # 客户1文件夹
│   ├── accounts-20250513.csv
│   ├── accounts-20250723.csv
│   └── accounts-20250731.csv
└── customer2/                            # 客户2文件夹
    └── accounts-20250731.csv
```

添加新客户：在数据目录下创建客户文件夹，添加符合格式的 CSV 数据文件。系统会自动识别新客户。

## 使用步骤

**Step 1. 环境准备**

```bash
# clone 本项目
git clone git@github.com:zhilidev/mcp-server-demo.git

# 进入项目目录
cd /path/to/mcp-server-demo

# 安装依赖
pip install -r requirements.txt
```

**step 2. 配置Amazon Q，将MCP配置添加到Amazon Q配置文件。重启配置Amazon Q。**

```json
{
  "mcpServers": {
    "demo-account-analyzer": {
      "command": "python3",
      "args": [
        "/path/to/mcp-server-demo/src/partner_account_analyzer/server.py"
      ],
      "env": {
        "ACCOUNT_DATA_DIR": "/path/to/data/directory"
      }
    }
  }
}
```

## 示例提示词

### 🏢 Enterprise账号分析 
```
- 显示所有可用的客户
- 分析某客户 0731的完整Enterprise账号情况
- 分析某客户上半年的Enterprise账号变化情况
- 获取某客户 0730到0731详细的Enterprise Linked账号变化信息
- 使用趋势分析模板帮我分析某客户的Enterprise账号变化趋势
- 使用月度报告模板为某客户生成7月份的Enterprise账号变化报告
- 某客户的Enterprise Linked账号数量突然增加了，帮我详细分析是哪些账号发生了变化，什么时候变化的
```

### 🌐 Overall业务分析
```
- 分析某客户 0731的整体业务情况，包括所有支持级别的账号
- 比较某客户 0730到0731之间的整体业务变化，不只是Enterprise
- 分析某客户的业务细分情况，通过标签识别不同的业务线
- 某客户想了解自己的完整业务图景，不局限于Enterprise级别
- 分析某客户的客户结构特征，包括Enterprise、Business、Developer、Basic的分布
- 评估某客户的业务成熟度和管理规范化程度
- 识别某客户的高价值业务线和增长潜力业务
- 使用Overall业务分析模板全面分析某客户的业务情况
```

### 🎯 深度业务洞察

**Payer分布深度分析**
```
- 深度分析某客户的Payer账号分布，看看每个Payer管理了多少Linked账号
- 某客户有几个payer账号，每个payer账号下support具体什么分布
- 某客户的Payer账号管理结构是否合理，有什么优化建议
```
**行业特征智能识别**
```
- 从某客户的账号信息中分析推断行业特征和业务模式
- 某客户属于什么行业，从账号命名和标签能看出什么特征
- 从账号信息推断某客户的主要业务领域和发展方向
```

**综合业务洞察**
```
- 对某客户进行全面的综合业务洞察分析，整合所有维度的分析结果
- 某客户的整体业务特征是什么，有什么关键发现
- 某客户想全面了解自己的业务现状，请进行三层分析：Enterprise专用、Overall业务、深度洞察
```


## 支持的文件格式

系统自动识别以下CSV文件格式：

**日期格式支持**
- **MMDD格式**: 如 0513, 0731 (月日，4位数字)
- **YYYYMMDD格式**: 如 20250513, 20250731 (年月日，8位数字) 

**文件名格式支持**
- `{客户名}-CMC-accounts-{日期}.csv` 
  - 示例: `customer1-CMC-accounts-0513.csv`
  - 示例: `customer1-CMC-accounts-20250513.csv`
- `{客户名}-accounts-{日期}.csv` 
  - 示例: `customer1-accounts-0513.csv`
  - 示例: `customer1-accounts-20250513.csv`
- `accounts-{日期}.csv`
  - 示例: `accounts-0513.csv`
  - 示例: `accounts-20250513.csv`
## 📈 使用案例

### 🎯 业务决策支持
**场景**: 某客户想了解自己的业务现状和发展方向
```
1. 使用 analyze_comprehensive_business_insights() 获取综合业务洞察
2. 基于5维度成熟度评分识别优势和短板
3. 根据行业特征分析制定发展策略
4. 基于管理效率评估优化组织架构
```

### 🏢 客户关系管理
**场景**: 识别高价值客户和潜在升级机会
```
1. 使用 analyze_partner_overall_business() 分析客户价值分布
2. 识别Enterprise占比高的高价值客户
3. 发现Business客户的升级潜力
4. 制定差异化的客户服务策略
```

### 📊 运营效率优化
**场景**: 优化账号管理结构和提升效率
```
1. 使用 analyze_payer_detailed_distribution() 分析管理负载
2. 识别管理过载的Payer账号
3. 基于基尼系数评估负载均衡程度
4. 制定账号重组和优化方案
```

### 🔍 风险识别预警
**场景**: 识别业务风险和管理隐患
```
1. 监控管理负载分布，预警过载风险
2. 评估命名规范化程度，识别管理混乱
3. 分析业务多样性，评估集中度风险
4. 建立关键指标监控体系
```

## 🎯 最佳实践

### 📋 分析流程建议
1. **基础了解** - 先用 `get_available_customers_tool()` 了解数据概况
2. **整体分析** - 使用Overall业务分析了解完整业务图景
3. **深度洞察** - 使用深度分析工具挖掘业务特征
4. **对比分析** - 通过时间对比发现变化趋势
5. **战略制定** - 基于综合分析结果制定行动计划

### 💡 提示词优化技巧
- **具体化**: 明确指定客户名称和日期范围
- **分层次**: 从整体到细节，逐步深入分析
- **多维度**: 结合不同工具获得全面视角
- **可视化**: 要求生成图表和可视化展示
- **可操作**: 要求提供具体的改进建议

### 🔄 定期监控建议
- **日常监控**: 账号数量变化和异常情况
- **周度分析**: 管理负载分布和效率评估
- **月度评估**: 业务价值变化和客户结构调整
- **季度洞察**: 行业特征变化和战略调整
- **年度规划**: 综合成熟度评估和长期规划

## 🚀 升级亮点

### 从基础统计到深度洞察
- **之前**: 简单的账号数量统计和变化对比
- **现在**: 多维度业务洞察和智能特征识别

### 从被动分析到主动建议
- **之前**: 展示数据变化，需要人工解读
- **现在**: 自动识别关键发现，提供战略建议

### 从单一视角到全面评估
- **之前**: 仅关注Enterprise级别账号
- **现在**: 三层分析体系，覆盖所有业务层面

### 从定性描述到量化评估
- **之前**: 定性的趋势描述
- **现在**: 量化的成熟度评分和效率指标

---

**🎉 现在就开始使用深度业务洞察功能，让数据为你的业务决策提供强有力的支持！**