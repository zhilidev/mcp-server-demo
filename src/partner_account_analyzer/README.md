# Account Analyzer MCP Server

Enterprise账号分析的MCP服务器，支持多客户分析和详细的账号变化追踪。通过这个服务器，你可以轻松管理和分析Enterprise账号变化情况，无论是单日数据还是多日对比分析！

## 文件结构

```
mcp-server-demo/
├── src/
│   └── partner_account_analyzer/
│       ├── __init__.py                    # Python包初始化文件
│       ├── server.py                      # 核心服务器文件
│       └── README.md 
├── pyproject.toml                        # 项目配置
├── requirements.txt                      # 依赖文件
└── README.md
```

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

- 显示所有可用的客户
- 分析某客户 0731的完整账号情况
- 分析某客户上半年的账号变化情况
- 获取某客户  0730到0731详细的Linked账号变化信息
- 使用趋势分析模板帮我分析某客户的账号变化趋势
- 使用月度报告模板为某客户生成7月份的账号变化报告
- 某客户的Linked账号数量突然增加了，帮我详细分析是哪些账号发生了变化，什么时候变化的

## 支持的文件格式

系统自动识别以下CSV文件格式：

### 日期格式支持
- **MMDD格式**: 如 0513, 0731 (月日，4位数字)
- **YYYYMMDD格式**: 如 20250513, 20250731 (年月日，8位数字) 

### 文件名格式支持
- `{客户名}-CMC-accounts-{日期}.csv` 
  - 示例: `customer1-CMC-accounts-0513.csv`
  - 示例: `customer1-CMC-accounts-20250513.csv`
- `{客户名}-accounts-{日期}.csv` 
  - 示例: `customer1-accounts-0513.csv`
  - 示例: `customer1-accounts-20250513.csv`
- `accounts-{日期}.csv`
  - 示例: `accounts-0513.csv`
  - 示例: `accounts-20250513.csv`
- `CMC-accounts-{日期}.csv`
  - 示例: `CMC-accounts-0513.csv`
  - 示例: `CMC-accounts-20250513.csv`