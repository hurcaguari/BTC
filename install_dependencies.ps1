# BTC虚拟货币数据获取系统 - PowerShell依赖安装脚本
# 适用于Windows PowerShell 5.1+

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "BTC虚拟货币数据获取系统" -ForegroundColor Yellow
Write-Host "PowerShell 依赖安装脚本" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python是否可用
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python环境检测成功" -ForegroundColor Green
    Write-Host "Python版本: $pythonVersion" -ForegroundColor White
}
catch {
    Write-Host "❌ 错误: 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查是否存在虚拟环境
if (!(Test-Path ".venv")) {
    Write-Host ""
    Write-Host "📦 创建虚拟环境..." -ForegroundColor Blue
    try {
        python -m venv .venv
        Write-Host "✅ 虚拟环境创建成功" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ 虚拟环境创建失败" -ForegroundColor Red
        Read-Host "按任意键退出"
        exit 1
    }
}
else {
    Write-Host "✅ 虚拟环境已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "🔧 在虚拟环境中安装依赖..." -ForegroundColor Blue

# 定义虚拟环境中的Python路径
$venvPython = ".\.venv\Scripts\python.exe"

# 升级pip
Write-Host "📦 升级pip..." -ForegroundColor Yellow
try {
    & $venvPython -m pip install --upgrade pip
    Write-Host "✅ pip升级成功" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  pip升级失败，继续安装..." -ForegroundColor Yellow
}

# 安装核心依赖
Write-Host "📦 安装核心依赖..." -ForegroundColor Yellow
try {
    & $venvPython -m pip install -r requirements-core.txt
    Write-Host "✅ 依赖安装完成！" -ForegroundColor Green
}
catch {
    Write-Host "❌ 依赖安装失败" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

Write-Host ""
Write-Host "📋 已安装的包:" -ForegroundColor Cyan
& $venvPython -m pip list

Write-Host ""
Write-Host "🚀 系统安装完成！现在可以运行以下命令:" -ForegroundColor Green
Write-Host "   激活虚拟环境: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "   运行主程序: python main.py" -ForegroundColor White
Write-Host "   运行全币种测试: python main_full_tokens.py" -ForegroundColor White
Write-Host "   运行详细报告: python detailed_token_report.py" -ForegroundColor White
Write-Host ""

# 测试系统是否正常工作
Write-Host "🧪 测试系统..." -ForegroundColor Blue
try {
    & $venvPython -c "from Lib.etherscan_api import EtherscanAPI; print('✅ 系统测试通过')"
    Write-Host "✅ 系统运行正常！" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  系统测试失败，但依赖已安装" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "按任意键退出"
