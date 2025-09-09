@echo off
REM BTC虚拟货币数据获取系统 - 快速启动脚本
echo.
echo ================================
echo BTC虚拟货币数据获取系统
echo 快速启动
echo ================================
echo.

REM 激活虚拟环境
call .venv\Scripts\activate.bat

echo 选择运行模式:
echo 1. 运行主程序 (配置文件币种)
echo 2. 运行全币种测试
echo 3. 生成详细报告
echo 4. 运行完整测试
echo.

set /p choice=请选择 (1-4): 

if "%choice%"=="1" (
    echo.
    echo 🚀 启动主程序...
    python main.py
) else if "%choice%"=="2" (
    echo.
    echo 🚀 启动全币种测试...
    python main_full_tokens.py
) else if "%choice%"=="3" (
    echo.
    echo 🚀 生成详细报告...
    python detailed_token_report.py
) else if "%choice%"=="4" (
    echo.
    echo 🚀 运行完整测试...
    python test_all_tokens.py
) else (
    echo ❌ 无效选择
)

echo.
pause
