# PostgreSQL setup using Docker
# This is the simplest way to get PostgreSQL running

Write-Host "Setting up PostgreSQL using Docker..." -ForegroundColor Green

# Check if Docker is installed
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is not installed. Installing Docker Desktop..." -ForegroundColor Yellow
    
    # Install Docker Desktop via Chocolatey
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        choco install docker-desktop --yes
        Write-Host "Docker Desktop installed! Please restart your computer and run this script again." -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop" -ForegroundColor Red
        exit 1
    }
}

# Start PostgreSQL container
Write-Host "Starting PostgreSQL container..." -ForegroundColor Yellow
try {
    # Stop and remove existing container if it exists
    docker stop sdelka-postgres 2>$null
    docker rm sdelka-postgres 2>$null
    
    # Start new PostgreSQL container
    docker run -d `
        --name sdelka-postgres `
        -e POSTGRES_DB=sdelka_v4 `
        -e POSTGRES_USER=sdelka_user `
        -e POSTGRES_PASSWORD=sdelka_password `
        -p 5432:5432 `
        postgres:17
    
    Write-Host "PostgreSQL container started successfully!" -ForegroundColor Green
    Write-Host "Database: sdelka_v4" -ForegroundColor Yellow
    Write-Host "User: sdelka_user" -ForegroundColor Yellow
    Write-Host "Password: sdelka_password" -ForegroundColor Yellow
    Write-Host "Port: 5432" -ForegroundColor Yellow
    
} catch {
    Write-Host "Error starting PostgreSQL container: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Wait for PostgreSQL to be ready
Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test connection
Write-Host "Testing PostgreSQL connection..." -ForegroundColor Yellow
try {
    docker exec sdelka-postgres psql -U sdelka_user -d sdelka_v4 -c "SELECT version();"
    Write-Host "PostgreSQL is ready!" -ForegroundColor Green
} catch {
    Write-Host "PostgreSQL is starting up, please wait a moment..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "PostgreSQL setup completed!" -ForegroundColor Green
Write-Host "You can now use PostgreSQL with your Flutter application." -ForegroundColor Yellow
