# Superset Database Initialization Script (PowerShell)
Write-Host "===== Superset Database Initialization =====" -ForegroundColor Green
Write-Host ""

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Change to Superset directory
$supersetPath = "D:\workspace\superset-github\superset"
Set-Location $supersetPath

# Check virtual environment
if (-not (Test-Path ".venv\Scripts\activate.bat")) {
    Write-Host "Error: Virtual environment does not exist!" -ForegroundColor Red
    Write-Host "Please create virtual environment first: python -m venv .venv" -ForegroundColor Yellow
    Read-Host "Press Enter to continue..."
    exit 1
}

# Set environment variable
$env:SUPERSET_CONFIG_PATH = "D:\workspace\superset-github\superset\superset_config.py"

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".venv\Scripts\activate.bat"

Write-Host ""
Write-Host "1. Upgrading database schema..." -ForegroundColor Cyan
try {
    & superset db upgrade
    if ($LASTEXITCODE -ne 0) {
        throw "Database upgrade failed"
    }
    Write-Host "✓ Database upgrade successful" -ForegroundColor Green
}
catch {
    Write-Host "✗ Database upgrade failed: $_" -ForegroundColor Red
    Read-Host "Press Enter to continue..."
    exit 1
}

Write-Host ""
Write-Host "2. Creating admin user..." -ForegroundColor Cyan
Write-Host "Default username: admin" -ForegroundColor Yellow
Write-Host "Default password: admin123" -ForegroundColor Yellow
try {
    & superset fab create-admin --username admin --firstname Admin --lastname User --email admin@superset.com --password admin123
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create admin user"
    }
    Write-Host "✓ Admin user created successfully" -ForegroundColor Green
}
catch {
    Write-Host "✗ Failed to create admin user: $_" -ForegroundColor Red
    Read-Host "Press Enter to continue..."
    exit 1
}

Write-Host ""
Write-Host "3. Initializing Superset..." -ForegroundColor Cyan
try {
    & superset init
    if ($LASTEXITCODE -ne 0) {
        throw "Superset initialization failed"
    }
    Write-Host "✓ Superset initialization successful" -ForegroundColor Green
}
catch {
    Write-Host "✗ Superset initialization failed: $_" -ForegroundColor Red
    Read-Host "Press Enter to continue..."
    exit 1
}

Write-Host ""
Write-Host "===== Initialization Complete! =====" -ForegroundColor Green
Write-Host ""
Write-Host "Now you can:" -ForegroundColor Cyan
Write-Host "1. Press F5 in VS Code to start debugging" -ForegroundColor White
Write-Host "2. Or run: superset run -p 8088 --with-threads --reload --debugger" -ForegroundColor White
Write-Host "3. Visit http://localhost:8088" -ForegroundColor White
Write-Host "4. Login: admin / admin123" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to exit..." 