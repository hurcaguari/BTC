# BTC 虚拟货币数据获取系统

## 📋 项目简介
一个功能完整的Python虚拟货币市场数据获取系统，支持多种主流加密货币的价格、供应量和算力数据获取，具备智能缓存和配置管理功能。

## 🚀 支持的功能
- ✅ **多币种支持**: BTC, ETH, BNB, KAS, SOL, AVAX, MATIC, LTC, DOGE, ARB, OP (共11种)
- ✅ **数据类型**: 美元/人民币价格、流通供应量、网络算力
- ✅ **智能缓存**: SQLite数据库缓存，可配置缓存时间
- ✅ **配置管理**: YAML配置文件，支持注释
- ✅ **多数据源**: CoinGecko, Blockchain.info, Etherscan, Kaspa等API
- ✅ **错误处理**: 完善的异常处理和重试机制
- ✅ **性能优化**: 请求延迟控制，避免API限制

## 📁 项目结构
```
BTC/
├── main.py                     # 主程序（配置文件中的币种）
├── main_full_tokens.py         # 完整币种测试程序
├── test_all_tokens.py          # 所有支持币种测试
├── detailed_token_report.py    # 详细数据报告
├── requirements.txt            # 完整依赖文件
├── requirements-core.txt       # 核心依赖文件
├── install_dependencies.bat    # Windows安装脚本
├── install_dependencies.ps1    # PowerShell安装脚本
├── Config/
│   └── config.yaml            # YAML配置文件
├── Lib/
│   ├── etherscan_api.py       # 核心API类
│   ├── simple_yaml.py         # 简单YAML解析器
│   └── __init__.py
└── cache/
    └── token_cache.db         # SQLite缓存数据库
```

## 🛠 安装和使用

### 方法1: 使用安装脚本（推荐）
```bash
# Windows PowerShell
.\install_dependencies.ps1

# 或者使用批处理
.\install_dependencies.bat
```

### 方法2: 手动安装
```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements-core.txt

# 4. 运行程序
python main.py
```

## 📦 依赖要求
- **Python**: 3.8+ (推荐3.11+)
- **核心依赖**:
  - `requests` >= 2.31.0 (HTTP请求)
  - `PyYAML` >= 6.0.1 (YAML配置解析)  
  - `urllib3[secure]` >= 2.0.0 (安全HTTP连接)

## ⚙️ 配置说明

### API密钥配置
在 `Config/config.yaml` 中配置API密钥：
```yaml
api_keys:
  etherscan: "YOUR_ETHERSCAN_API_KEY"
```

### 缓存设置
```yaml
cache:
  enabled: true           # 启用缓存
  duration_minutes: 5     # 缓存时间（分钟）
  database: "cache/token_cache.db"
```

### 币种选择
```yaml
tokens:
  - BTC   # 比特币
  - ETH   # 以太坊
  - KAS   # Kaspa
  # ... 更多币种
```

## 🎯 使用示例

### 基础用法
```python
from Lib.etherscan_api import EtherscanAPI

# 初始化API
api = EtherscanAPI()

# 获取BTC数据
btc_info = api.get_token_info('BTC')
print(f"BTC价格: ${btc_info['usd_price']}")
```

### 运行不同的测试程序
```bash
# 运行配置文件中的币种
python main.py

# 测试所有支持的币种
python main_full_tokens.py

# 生成详细报告
python detailed_token_report.py

# 运行完整测试套件
python test_all_tokens.py
```

## 📊 支持的币种类型

### POW币种（有算力数据）
- **BTC**: 比特币 - 完整支持价格、供应量、算力
- **KAS**: Kaspa - 完整支持价格、供应量、算力

### POS/其他币种（无算力数据）
- **ETH**: 以太坊 - 价格、供应量
- **BNB**: 币安币 - 价格、供应量  
- **SOL**: Solana - 价格、供应量
- **AVAX**: Avalanche - 价格、供应量
- **MATIC**: Polygon - 价格、供应量
- **LTC**: 莱特币 - 价格、供应量
- **DOGE**: 狗狗币 - 价格、供应量
- **ARB**: Arbitrum - 价格、供应量
- **OP**: Optimism - 价格、供应量

## 🔧 高级功能

### 缓存管理
```python
# 查看缓存状态
cache_stats = api.get_cache_stats()
print(f"缓存条目: {cache_stats['total_cache_entries']}")

# 清理过期缓存
api._cleanup_expired_cache()
```

### 批量数据获取
系统支持批量获取多个币种数据，自动处理请求频率限制。

### 错误处理
- 自动重试机制
- API限制检测
- 网络异常处理
- 数据格式验证

## 🚨 注意事项
1. **API限制**: 免费API有请求频率限制，建议启用缓存
2. **网络环境**: 部分API可能需要稳定的网络连接
3. **API密钥**: Etherscan API密钥建议申请正式版本
4. **数据准确性**: 价格数据仅供参考，投资请谨慎

## 📈 性能表现
- **首次获取**: 平均4-6秒/币种（API调用）
- **缓存命中**: 0.00秒/币种（瞬时响应）
- **内存占用**: < 50MB
- **缓存效率**: 100%命中率（缓存期内）

## 🔄 更新日志
- **v1.0.0** (2025-09-09): 初始版本发布
  - 支持11种主流加密货币
  - SQLite缓存系统
  - YAML配置管理
  - 完整的错误处理

## 📞 支持与反馈
如有问题或建议，请通过以下方式联系：
- 创建Issue报告问题
- 提交Pull Request贡献代码
- 查看项目文档获取更多信息

---
**免责声明**: 本系统提供的数据仅供学习和研究使用，不构成投资建议。投资有风险，决策需谨慎。
