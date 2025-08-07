# Account Analyzer MCP Server 

Enterprise账号分析的MCP服务器，支持多客户分析和详细的账号变化追踪。现已升级为深度业务洞察分析工具，不仅支持Enterprise账号分析，还新增了Overall业务分析和深度业务洞察功能，能够从账号数据中挖掘出行业特征、组织架构、技术成熟度等深层信息！

## 核心功能

1. **Enterprise专用分析** - 高价值客户的详细变化追踪
2. **Overall业务分析** - 完整业务图景和客户结构分析  
3. **Payer分布深度分析** - 管理负载和效率评估


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
- 分析某客户的客户结构特征，包括Enterprise、Business、Developer、Basic的分布
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