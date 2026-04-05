# NetLedger Self-Hosted Installer for Windows
# Run in PowerShell as Administrator:
#   irm https://netl.2max.tech/install.ps1 | iex

$ErrorActionPreference = "Stop"
$InstallDir = "C:\NetLedger"
$RepoUrl = "https://github.com/2maxtech/NetLedger.git"

Write-Host ""
Write-Host "========================================" -ForegroundColor DarkYellow
Write-Host "       NetLedger Installer" -ForegroundColor DarkYellow
Write-Host "    ISP Billing & MikroTik Manager" -ForegroundColor DarkYellow
Write-Host "           by 2max Tech" -ForegroundColor DarkYellow
Write-Host "========================================" -ForegroundColor DarkYellow
Write-Host ""

# Check Docker
Write-Host "[1/5] Checking Docker..." -ForegroundColor Green
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "  Docker Desktop is required." -ForegroundColor Red
    Write-Host "  Download: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host "  Install Docker Desktop, restart, then run this script again." -ForegroundColor Yellow
    exit 1
}
Write-Host "  Docker found" -ForegroundColor Green

# Check Git
Write-Host "[2/5] Checking Git..." -ForegroundColor Green
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "  Installing Git..." -ForegroundColor Yellow
    winget install --id Git.Git -e --silent 2>$null
    $env:PATH += ";C:\Program Files\Git\bin"
}
Write-Host "  Git found" -ForegroundColor Green

# Clone
Write-Host "[3/5] Downloading NetLedger..." -ForegroundColor Green
if (Test-Path "$InstallDir\.git") {
    Set-Location $InstallDir
    git pull --quiet
    Write-Host "  Updated" -ForegroundColor Green
} else {
    if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
    git clone --quiet --depth 1 $RepoUrl $InstallDir
    Set-Location $InstallDir
    Write-Host "  Downloaded" -ForegroundColor Green
}

# Config
Write-Host "[4/5] Configuring..." -ForegroundColor Green
if (-not (Test-Path "$InstallDir\.env")) {
    $DbPass = -join ((48..57) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    $SecretKey = -join ((48..57) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
    @"
POSTGRES_USER=netledger
POSTGRES_PASSWORD=$DbPass
POSTGRES_DB=netledger
DATABASE_URL=postgresql+asyncpg://netledger:${DbPass}@db:5432/netledger
REDIS_URL=redis://redis:6379/0
SECRET_KEY=$SecretKey
MIKROTIK_URL=http://192.168.88.1
MIKROTIK_USER=admin
MIKROTIK_PASSWORD=
"@ | Out-File -FilePath "$InstallDir\.env" -Encoding UTF8
    Write-Host "  Config created" -ForegroundColor Green
} else {
    Write-Host "  Config exists" -ForegroundColor Green
}

# Build and start
Write-Host "[5/5] Building and starting (this may take a few minutes)..." -ForegroundColor Green
Set-Location $InstallDir
docker compose build --quiet 2>$null
docker compose up -d 2>$null
Start-Sleep -Seconds 5
docker compose exec -T backend alembic upgrade head 2>$null

# Create admin
docker compose exec -T backend python3 -c @"
import asyncio
from app.core.database import async_session
from app.models.user import User, UserRole
from app.core.security import hash_password
from sqlalchemy import select

async def seed():
    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == 'admin'))
        if result.scalar_one_or_none():
            return
        admin = User(username='admin', email='admin@localhost', password_hash=hash_password('admin123'), role=UserRole.admin, is_active=True)
        db.add(admin)
        await db.commit()

asyncio.run(seed())
"@ 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  NetLedger installed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Open: http://localhost" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Login:" -ForegroundColor White
Write-Host "    Username: admin" -ForegroundColor Yellow
Write-Host "    Password: admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Change your password after first login!" -ForegroundColor DarkYellow
Write-Host ""
