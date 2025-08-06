# Case Analyzer MCP Server 

工单分析的MCP服务器，支持多维度工单统计分析和深度业务洞察。专门用于分析技术支持工单的分布情况、服务使用模式和客户支持需求。

## 🚀 核心功能

1. **Category分析** - 按工单类别统计分布情况
2. **Payer账户分析** - 分析每个付费账户的工单情况和技术支持分布
3. **Service服务分析** - 结合Resolver和Type分析各服务的工单分布
4. **General Guidance统计** - 专门统计General Guidance类型的工单
5. **综合分析报告** - 提供全维度的工单分析洞察

## 📁 文件结构

```
mcp-server-demo/
├── src/
│   └── partner_case_analyzer/
│       ├── __init__.py                    # Python包初始化文件
│       ├── server.py                      # 核心服务器文件
│       └── README.md                      # 本文档
├── pyproject.toml                        # 项目配置
├── requirements.txt                      # 依赖文件
└── README.md                             # 项目主文档
```

## 🛠️ 可用工具列表

**工单统计分析工具**
- `get_available_months_tool(data_dir)` - 获取数据目录下所有可用的月份
- `analyze_cases_by_category(data_dir, month="")` - 按Category (C)列统计工单数量和分布
- `analyze_cases_by_payer(data_dir, month="")` - 按Account PayerId统计每个payer的工单数量和技术支持分布
- `analyze_cases_by_service(data_dir, month="")` - 结合Resolver和Type (T)列分析各个service的工单数量
- `analyze_general_guidance_cases(data_dir, month="")` - 统计Item (I)为General Guidance的工单数量
- `get_comprehensive_case_analysis(data_dir, month="")` - 获取综合工单分析报告

**月份参数说明**
- `month` 参数支持以下格式：
  - `""` (空字符串): 分析所有月份的工单
  - `"202507"`: 分析2025年7月的工单
  - `"2025-07"`: 分析2025年7月的工单（带连字符格式）

## 数据目录结构

```
/path/to/case-data/
├── cases-202507.csv                      # 2025年7月工单数据
├── cases-202508.csv                      # 2025年8月工单数据
└── cases-202509.csv                      # 2025年9月工单数据
```

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

**Step 2. 配置AI助手，将MCP配置添加到AI助手配置文件。重启配置AI助手。**

```json
{
  "mcpServers": {
    "demo-case-analyzer": {
      "command": "python3",
      "args": [
        "/path/to/mcp-server-demo/src/partner_case_analyzer/server.py"
      ],
      "env": {
        "CASE_DATA_DIR": "/path/to/case/data",
        "CUSTOMER_MAPPING_FILE": "/path/to/customer/mapping.xlsx" -- 包含payer, 客户 两列
      }
    }
  }
}
```

## 示例提示词

### 📊 基础工单分析
```
- 分析该目录下所有月份的工单按类别分布情况
- 分析2025年7月的工单按类别分布情况
- 统计各个付费账户开工单的数量和技术支持分布
- 分析2025年7月各个服务的工单数量分布
- 统计2025年7月General Guidance类型的工单有多少个
- 生成2025年7月的综合工单分析报告
```

### 🎯 深度业务洞察
```
- 哪个付费账户在2025年7月开的工单最多，主要是什么类型的问题
- 2025年7月哪些服务的工单数量最多，反映了什么业务特征
- 2025年7月Technical Support和非Technical Support的工单分布如何
- 2025年7月General Guidance工单主要集中在哪些服务上
- 从2025年7月的工单分布看客户的技术成熟度如何
```

### 📈 趋势和模式分析
```
- 比较所有月份和2025年7月的工单数量变化
- 分析2025年7月工单严重程度分布，识别关键问题
- 从2025年7月工单状态分布看处理效率如何
- 识别2025年7月高频问题和服务，制定优化策略
- 分析2025年7月客户支持需求模式和特征
```

## 支持的文件格式

系统自动识别以下CSV文件格式：

**文件名格式支持**
- `cases-YYYYMM.csv` - 标准月度工单文件
  - 示例: `cases-202507.csv` (2025年7月)
  - 示例: `cases-202508.csv` (2025年8月)

**必需的CSV列字段**
- `Case ID` - 工单唯一标识
- `Category (C)` - 工单类别 (如: Technical support, Account and billing support)
- `Account PayerId` - 付费账户ID
- `Type (T)` - 工单类型 (如: 具体的服务名称)
- `Item (I)` - 工单项目 (如: General Guidance, Database Issue等)
- `Resolver` - 解决服务 (如: Simple Storage Service (S3), EC2等)
- `Subject` - 工单主题
- `Status` - 工单状态 (如: Resolved, Pending等)
- `Severity` - 严重程度 (如: Normal, High, Low等)


**🎉 现在就开始使用工单分析功能，让数据为你的客户支持决策提供强有力的支持！**
