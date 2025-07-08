@echo off
REM GiftManager Docker Setup Script for Windows
echo Setting up GiftManager Docker environment...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running. Please start Docker and try again.
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file with your configuration before running the application.
)

REM Create necessary directories
echo Creating required directories...
if not exist data mkdir data
if not exist static mkdir static
if not exist media mkdir media

REM Build and start the application
echo Building Docker image...
docker-compose build

echo Starting the application...
docker-compose up -d

echo Waiting for the application to start...
timeout /t 10 /nobreak >nul

REM Check if the application is running
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo Failed to start the application. Check logs with: docker-compose logs
    exit /b 1
) else (
    echo.
    echo ✅ GiftManager is running successfully!
    echo 🌐 Access the application at: http://localhost:8000
    echo 👤 Default admin credentials: admin/admin123
    echo 📋 View logs with: docker-compose logs -f
    echo 🛑 Stop the application with: docker-compose down
)
