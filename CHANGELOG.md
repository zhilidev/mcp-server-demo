# 更新日志

## 2025-08-01 - 文件格式支持增强

### 新增功能
- ✨ **支持 YYYYMMDD 日期格式**: 现在支持 `accounts-20250513.csv` 格式的文件
- ✨ **智能日期处理**: 自动识别和转换 MMDD 和 YYYYMMDD 两种日期格式
- ✨ **扩展文件名支持**: 新增 `{客户名}-accounts-{日期}.csv` 格式支持

### 支持的文件格式

#### 日期格式
- **MMDD格式**: 0513, 0731 (月日，4位数字)
- **YYYYMMDD格式**: 20250513, 20250731 (年月日，8位数字) - **新增**

#### 文件名格式
1. `{客户名}-CMC-accounts-{日期}.csv`
   - `customer1-CMC-accounts-0513.csv`
   - `customer1-CMC-accounts-20250513.csv`

2. `{客户名}-accounts-{日期}.csv` - **新增**
   - `customer1-accounts-0513.csv`
   - `customer1-accounts-20250513.csv`

3. `accounts-{日期}.csv`
   - `accounts-0513.csv`
   - `accounts-20250513.csv` - **新增**

4. `CMC-accounts-{日期}.csv`
   - `CMC-accounts-0513.csv`
   - `CMC-accounts-20250513.csv`

### 技术实现

#### 新增函数
- `normalize_date_format(date_str)`: 标准化日期格式为 MMDD
- `expand_date_format(date_str)`: 生成可能的日期格式列表

#### 修改的函数
- `get_available_dates()`: 更新正则表达式模式，支持新的文件格式
- `load_accounts_data()`: 增强文件查找逻辑，支持多种日期格式

#### 正则表达式更新
```python
patterns = [
    re.compile(rf'{re.escape(customer)}-CMC-accounts-(\d{{4}})\.csv'),
    re.compile(rf'{re.escape(customer)}-CMC-accounts-(\d{{8}})\.csv'),
    re.compile(rf'{re.escape(customer)}-accounts-(\d{{4}})\.csv'),      # 新增
    re.compile(rf'{re.escape(customer)}-accounts-(\d{{8}})\.csv'),      # 新增
    re.compile(r'accounts-(\d{4})\.csv'),
    re.compile(r'accounts-(\d{8})\.csv'),                               # 新增
    re.compile(r'CMC-accounts-(\d{4})\.csv'),
    re.compile(r'CMC-accounts-(\d{8})\.csv'),                           # 新增
]
```

### 向后兼容性
- ✅ 完全向后兼容现有的 MMDD 格式文件
- ✅ 支持混合使用不同格式的文件
- ✅ 用户查询时可以使用任一格式的日期

### 使用示例

#### 查询示例
```
# 以下查询都能正确工作：
- 显示客户 customer1 的 0513 数据
- 显示客户 customer1 的 20250513 数据
- 分析客户 customer1 从 0513 到 0731 的变化
- 分析客户 customer1 从 20250513 到 20250731 的变化
```

#### 文件组织示例
```
/data/directory/
├── customer1/
│   ├── customer1-accounts-0513.csv      # MMDD 格式
│   ├── accounts-20250731.csv            # YYYYMMDD 格式
│   └── CMC-accounts-0612.csv            # 混合使用
└── customer2/
    └── accounts-20250513.csv            # 新格式
```

### 测试验证
- ✅ 日期格式转换函数测试通过
- ✅ 文件名生成逻辑测试通过
- ✅ 实际文件读取功能验证通过
- ✅ 向后兼容性验证通过
