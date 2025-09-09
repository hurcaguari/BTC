# Git推送问题解决方案指南

## 🚨 问题描述
```
fatal: unable to access 'https://github.com/hurcaguari/BTC.git/': 
Failed to connect to github.com port 443 after 21042 ms: Could not connect to server
```

## 🔍 问题诊断结果
- ❌ HTTPS连接超时 (端口443)
- ❌ SSH连接超时 (端口22)  
- ❌ ping github.com 100%丢包
- ✅ Git仓库状态正常

## 💡 解决方案

### 方案1: 网络代理配置 (如果您使用代理)
```bash
# 设置HTTP代理 (替换为您的代理地址和端口)
git config --global http.proxy http://proxy-server:port
git config --global https.proxy https://proxy-server:port

# 或者仅为GitHub设置代理
git config --global http.https://github.com.proxy http://proxy-server:port
```

### 方案2: 使用GitHub镜像 (推荐)
```bash
# 使用国内镜像加速
git remote set-url origin https://github.com.cnpmjs.org/hurcaguari/BTC.git
# 或者
git remote set-url origin https://hub.fastgit.org/hurcaguari/BTC.git
```

### 方案3: 修改hosts文件
将以下内容添加到 `C:\Windows\System32\drivers\etc\hosts`:
```
140.82.113.4 github.com
140.82.112.6 api.github.com
199.232.69.194 github.global.ssl.fastly.net
```

### 方案4: 更换DNS
将DNS服务器设置为：
- 主DNS: 8.8.8.8
- 备DNS: 8.8.4.4

### 方案5: 使用移动热点或更换网络
如果是网络环境问题，可以尝试：
- 使用手机热点
- 更换网络环境
- 等待网络恢复

## 🛠 已应用的Git配置优化
```bash
# 增加缓冲区大小
git config --global http.postBuffer 524288000

# 禁用低速限制
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999
```

## 🔧 手动推送命令
网络恢复后使用：
```bash
# 强制推送 (如果需要)
git push -f origin main

# 正常推送
git push -u origin main
```

## 📋 备用方案 - 手动上传
如果网络问题持续存在：
1. 将项目文件打包为ZIP
2. 登录GitHub网页版
3. 在仓库中选择"Upload files"
4. 上传并提交

## ✅ 验证命令
网络恢复后执行以下命令验证：
```bash
# 测试网络连接
ping github.com

# 测试Git连接
git ls-remote origin

# 推送代码
git push -u origin main
```

---
**注意**: 网络问题通常是暂时性的，建议稍后重试或更换网络环境。
