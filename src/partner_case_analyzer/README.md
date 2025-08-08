# Case Analyzer MCP Server 

工单分析的MCP服务器，支持多维度工单统计分析和深度业务洞察。专门用于分析技术支持工单的分布情况、服务使用模式和客户支持需求。

## 核心功能

1. **Category分析** - 按工单类别统计分布情况
2. **Payer账户分析** - 分析每个付费账户的工单情况和技术支持分布
3. **Service服务分析** - 结合Resolver和Type分析各服务的工单分布
4. **General Guidance统计** - 专门统计General Guidance类型的工单

## 前提

**1. Case数据**：目录结构推荐如下
```
/path/to/case-data/
├── cases-202507.csv                      # 2025年7月工单数据
├── cases-202508.csv                      # 2025年8月工单数据
└── cases-202509.csv                      # 2025年9月工单数据
```
**2. Payer和客户mapping关系**：Excel文件，要求包含**payer**, **客户**两列

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

**Step 2. 配置Amazon Q，将MCP配置添加到Amazon Q配置文件。重启配置Amazon Q。**

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
        "CUSTOMER_MAPPING_FILE": "/path/to/customer/mapping.xlsx" 
      }
    }
  }
}
```
- CASE_DATA_DIR：默认导出的case csv文件即可
- CUSTOMER_MAPPING_FILE：需要包含**payer**, **客户**两列

## 示例提示词

```
- 7月的工单按Payer进行统计，返回所有payer，表格优化对齐
- 7月的工单按类别分布情况
- 7月的工单按服务统计
- 7月General Guidance类型的工单有多少个
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


**Backup prompt：**
```
需求：
1. 环境变量
  - CASE_DATA_DIR：传入case csv文件所在的目录，目录中每个csv文件记录某一个月的工单信息。
  - CUSTOMER_MAPPING_FILE：提供了payer和客户名字对应关系，支持csv和xlsx格式
2. 能够按月 按Category (C)列统计工单数量
3. 能够按月 按Account PayerId统计每个payer开工单的数量，以及每个payer下多少个Category (C)是technical support和非technical support的。并且：a/以表格输出，表格输出时尽量保持列对齐，包含如下列输出表格包含以下列：编号 | 客户名称 | 账户ID | 总工单数 | 技术工单数 | 非技术工单数 | 技术占比，b/表格中列出所有payer，c/如果客户通过CUSTOMER_MAPPING_FILE提供了payer和客户名字对应关系时，就把客户名字显示到生成的结果表格中。
4. 结合Resolver和Type (T)列分析各个service的工单数量
5. Item (I)为General Guidance的数量有多少个
```