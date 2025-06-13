# Superset 数据库快速初始化脚本 (PowerShell)
Write-Host "===== Superset 数据库快速初始化 =====" -ForegroundColor Green
Write-Host ""

# 设置编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 切换到 Superset 目录
$supersetPath = "D:\workspace\superset-github\superset"
Set-Location $supersetPath

# 检查虚拟环境
if (-not (Test-Path ".venv\Scripts\activate.bat")) {
    Write-Host "错误: 虚拟环境不存在！" -ForegroundColor Red
    Write-Host "请先创建虚拟环境: python -m venv .venv" -ForegroundColor Yellow
    Read-Host "按回车键继续..."
    exit 1
}

# 设置环境变量
$env:SUPERSET_CONFIG_PATH = "D:\workspace\superset-github\superset\superset_config.py"

Write-Host "激活虚拟环境..." -ForegroundColor Cyan
& ".venv\Scripts\activate.bat"

Write-Host ""
Write-Host "1. 升级数据库架构..." -ForegroundColor Cyan
try {
    & superset db upgrade
    if ($LASTEXITCODE -ne 0) {
        throw "数据库升级失败"
    }
    Write-Host "✓ 数据库升级成功" -ForegroundColor Green
}
catch {
    Write-Host "✗ 数据库升级失败: $_" -ForegroundColor Red
    Read-Host "按回车键继续..."
    exit 1
}

Write-Host ""
Write-Host "2. 创建管理员用户..." -ForegroundColor Cyan
Write-Host "默认用户名: admin" -ForegroundColor Yellow
Write-Host "默认密码: admin123" -ForegroundColor Yellow
try {
    & superset fab create-admin --username admin --firstname Admin --lastname User --email admin@superset.com --password admin123
    if ($LASTEXITCODE -ne 0) {
        throw "创建管理员用户失败"
    }
    Write-Host "✓ 管理员用户创建成功" -ForegroundColor Green
}
catch {
    Write-Host "✗ 创建管理员用户失败: $_" -ForegroundColor Red
    Read-Host "按回车键继续..."
    exit 1
}

Write-Host ""
Write-Host "3. 初始化 Superset..." -ForegroundColor Cyan
try {
    & superset init
    if ($LASTEXITCODE -ne 0) {
        throw "Superset 初始化失败"
    }
    Write-Host "✓ Superset 初始化成功" -ForegroundColor Green
}
catch {
    Write-Host "✗ Superset 初始化失败: $_" -ForegroundColor Red
    Read-Host "按回车键继续..."
    exit 1
}

Write-Host ""
Write-Host "===== 初始化完成! =====" -ForegroundColor Green
Write-Host ""
Write-Host "现在您可以:" -ForegroundColor Cyan
Write-Host "1. 在 VS Code 中按 F5 启动调试" -ForegroundColor White
Write-Host "2. 或运行: superset run -p 8088 --with-threads --reload --debugger" -ForegroundColor White
Write-Host "3. 访问 http://localhost:8088" -ForegroundColor White
Write-Host "4. 登录信息: admin / admin123" -ForegroundColor Yellow
Write-Host ""

Read-Host "按回车键退出..." 