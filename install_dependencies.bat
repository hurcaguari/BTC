@echo off
REM BTC虚拟货币数据获取系统 - 依赖安装脚本
REM 适用于Windows PowerShell/CMD
echo.
echo ================================
echo BTC虚拟货币数据获取系统
echo 依赖安装脚本
echo ================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python环境检测成功
python --version

REM 检查是否存在虚拟环境
if not exist ".venv" (
    echo.
    echo 📦 创建虚拟环境...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
)

echo.
echo 🔧 激活虚拟环境并安装依赖...
call .venv\Scripts\activate.bat

REM 升级pip
echo 📦 升级pip...
python -m pip install --upgrade pip

REM 安装核心依赖
echo 📦 安装核心依赖...
pip install -r requirements-core.txt

if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo.
echo ✅ 依赖安装完成！
echo.
echo 📋 已安装的包:
pip list
echo.
echo 🚀 现在可以运行以下命令启动系统:
echo    .venv\Scripts\activate.bat
echo    python main.py
echo.
pause
