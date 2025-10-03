# Direct PostgreSQL installation script
# Downloads and installs PostgreSQL 17

Write-Host "Installing PostgreSQL directly..." -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

# Download PostgreSQL installer
$postgresUrl = "https://get.enterprisedb.com/postgresql/postgresql-17.4-1-windows-x64.exe"
$installerPath = "$env:TEMP\postgresql-installer.exe"

Write-Host "Downloading PostgreSQL installer..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $postgresUrl -OutFile $installerPath
    Write-Host "Download completed!" -ForegroundColor Green
} catch {
    Write-Host "Error downloading PostgreSQL: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Install PostgreSQL silently
Write-Host "Installing PostgreSQL..." -ForegroundColor Yellow
try {
    $installArgs = @(
        "--mode", "unattended",
        "--superpassword", "sdelka_password",
        "--servicename", "postgresql",
        "--serviceaccount", "postgres",
        "--servicepassword", "sdelka_password",
        "--serverport", "5432",
        "--unattendedmodeui", "none",
        "--debuglevel", "2"
    )
    
    Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait
    Write-Host "PostgreSQL installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Error installing PostgreSQL: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Clean up installer
Remove-Item $installerPath -Force

# Add PostgreSQL to PATH
$postgresPath = "C:\Program Files\PostgreSQL\17\bin"
if (Test-Path $postgresPath) {
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    if ($currentPath -notlike "*$postgresPath*") {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$postgresPath", "Machine")
        Write-Host "Added PostgreSQL to system PATH" -ForegroundColor Green
    }
}

# Start PostgreSQL service
Write-Host "Starting PostgreSQL service..." -ForegroundColor Yellow
try {
    Start-Service -Name "postgresql"
    Write-Host "PostgreSQL service started!" -ForegroundColor Green
} catch {
    Write-Host "Error starting PostgreSQL service: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "PostgreSQL installation completed!" -ForegroundColor Green
Write-Host "Default password: sdelka_password" -ForegroundColor Yellow
Write-Host "Service name: postgresql" -ForegroundColor Yellow
Write-Host "Port: 5432" -ForegroundColor Yellow
