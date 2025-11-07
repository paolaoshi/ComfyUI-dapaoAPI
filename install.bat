@echo off
chcp 65001 >nul
echo ==========================================
echo Seedream 4.0 API 节点安装脚本
echo ==========================================
echo.

echo [1/2] 正在安装 Python 依赖...
pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [2/2] 安装完成！
    echo.
    echo ==========================================
    echo 安装成功！
    echo ==========================================
    echo.
    echo 接下来的步骤：
    echo 1. 编辑 config.json 文件，填入你的 API Key 和 Endpoint ID
    echo 2. 重启 ComfyUI
    echo 3. 在节点菜单中找到 "SeedreamAPI" 类别
    echo.
    echo 详细使用说明请查看：使用指南.md
    echo.
) else (
    echo.
    echo ==========================================
    echo 安装失败！
    echo ==========================================
    echo.
    echo 请检查网络连接或手动安装依赖：
    echo pip install -r requirements.txt
    echo.
)

pause


