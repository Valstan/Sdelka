# Simple PostgreSQL installation script via Chocolatey
# Run as Administrator

Write-Host "Installing PostgreSQL via Chocolatey..." -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

# Check if Chocolatey is installed
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Chocolatey not found. Installing Chocolatey..." -ForegroundColor Yellow
    
    # Install Chocolatey
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Refresh PATH
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
    
    Write-Host "Chocolatey installed!" -ForegroundColor Green
} else {
    Write-Host "Chocolatey already installed" -ForegroundColor Green
}

# Install PostgreSQL via Chocolatey
Write-Host "Installing PostgreSQL..." -ForegroundColor Yellow
try {
    choco install postgresql --yes --params '/Password:sdelka_password'
    Write-Host "PostgreSQL installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Error installing PostgreSQL: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Check installation
Write-Host "Checking PostgreSQL installation..." -ForegroundColor Yellow
$service = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "PostgreSQL service found: $($service.Name)" -ForegroundColor Green
    if ($service.Status -eq "Running") {
        Write-Host "PostgreSQL service is running!" -ForegroundColor Green
    } else {
        Write-Host "Starting PostgreSQL service..." -ForegroundColor Yellow
        Start-Service -Name $service.Name
        Write-Host "PostgreSQL service started!" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "PostgreSQL installation completed!" -ForegroundColor Green
Write-Host "Default password: sdelka_password" -ForegroundColor Yellow
Write-Host "Please restart PowerShell to use PostgreSQL commands" -ForegroundColor Yellow
