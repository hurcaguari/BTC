# 🔒 配置文件安全指南

## ⚠️ 重要安全提醒
**永远不要将包含真实API密钥的配置文件提交到公开仓库！**

## 🛡️ 安全配置方案

### 方案1：使用配置模板（推荐）

1. **使用模板文件**：
   - 仓库中只包含 `config.template.yaml` 模板文件
   - 真实的 `config.yaml` 在 `.gitignore` 中被忽略

2. **本地配置步骤**：
   ```bash
   # 复制模板文件
   cp Config/config.template.yaml Config/config.yaml
   
   # 编辑配置文件，填入真实API密钥
   # 将 YOUR_API_KEY_HERE 替换为实际密钥
   ```

3. **使用配置管理工具**：
   ```bash
   python config_manager.py
   ```

### 方案2：使用环境变量

1. **设置环境变量**：
   ```bash
   # Windows PowerShell
   $env:ETHERSCAN_API_KEY="your_real_api_key"
   
   # Windows 命令行
   set ETHERSCAN_API_KEY=your_real_api_key
   
   # Linux/Mac
   export ETHERSCAN_API_KEY="your_real_api_key"
   ```

2. **程序会自动读取环境变量**，无需修改配置文件

### 方案3：使用 .env 文件

1. **创建 .env 文件**（已在 .gitignore 中）：
   ```bash
   ETHERSCAN_API_KEY=your_real_api_key
   COINGECKO_API_KEY=your_other_api_key
   ```

2. **程序启动时加载环境变量**

## 📋 检查清单

在提交代码前，请确认：

- [ ] `config.yaml` 已添加到 `.gitignore`
- [ ] 仓库中只有 `config.template.yaml` 模板文件
- [ ] 模板文件中所有敏感信息都已替换为占位符
- [ ] 已创建 `.gitignore` 文件
- [ ] 运行 `git status` 确认敏感文件未被跟踪

## 🔧 配置管理命令

```bash
# 检查当前配置状态
python config_manager.py

# 从模板创建配置文件
python config_manager.py

# 检查API密钥配置
python config_manager.py
```

## 📂 文件结构

```
项目根目录/
├── .gitignore                    # Git忽略文件（包含config.yaml）
├── config_manager.py             # 配置管理工具
├── Config/
│   ├── config.template.yaml      # 配置模板（可提交）
│   └── config.yaml               # 真实配置（被忽略）
```

## 🚨 如果意外提交了敏感信息

如果不小心提交了包含API密钥的文件：

1. **立即撤销提交**：
   ```bash
   git reset --hard HEAD~1
   ```

2. **重写历史记录**（危险操作）：
   ```bash
   git filter-branch --force --index-filter \
   'git rm --cached --ignore-unmatch Config/config.yaml' \
   --prune-empty --tag-name-filter cat -- --all
   ```

3. **更换API密钥**：
   - 立即到对应平台重新生成新的API密钥
   - 删除或禁用已泄露的密钥

## 📖 最佳实践

1. **定期轮换API密钥**
2. **使用只读权限的API密钥**
3. **监控API密钥使用情况**
4. **团队协作时使用统一的配置管理方案**
5. **在CI/CD中使用环境变量或密钥管理服务**
