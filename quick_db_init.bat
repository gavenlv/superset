@echo off
chcp 65001 > nul
echo ===== Superset Database Quick Initialization =====
echo.

REM 切换到 Superset 目录
cd /d "D:\workspace\superset-github\superset"

REM 检查虚拟环境
if not exist ".venv\Scripts\activate.bat" (
    echo Error: Virtual environment does not exist!
    echo Please create virtual environment first: python -m venv .venv
    pause
    exit /b 1
)

REM 设置环境变量
set SUPERSET_CONFIG_PATH=D:\workspace\superset-github\superset\superset_config.py

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo 1. Upgrading database schema...
superset db upgrade
if errorlevel 1 (
    echo Database upgrade failed!
    pause
    exit /b 1
)

echo.
echo 2. Creating admin user...
echo Default username: admin
echo Default password: admin123
superset fab create-admin --username admin --firstname Admin --lastname User --email admin@superset.com --password admin123
if errorlevel 1 (
    echo Failed to create admin user!
    pause
    exit /b 1
)

echo.
echo 3. Initializing Superset...
superset init
if errorlevel 1 (
    echo Superset initialization failed!
    pause
    exit /b 1
)

echo.
echo ===== Initialization Complete! =====
echo.
echo Now you can:
echo 1. Press F5 in VS Code to start debugging
echo 2. Or run: superset run -p 8088 --with-threads --reload --debugger
echo 3. Visit http://localhost:8088
echo 4. Login: admin / admin123
echo.

pause 