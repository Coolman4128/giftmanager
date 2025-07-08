#!/bin/bash

# GiftManager Docker Setup Script
echo "Setting up GiftManager Docker environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before running the application."
fi

# Create necessary directories
echo "Creating required directories..."
mkdir -p data static media

# Set proper permissions
chmod 755 data static media

# Build and start the application
echo "Building Docker image..."
docker-compose build

echo "Starting the application..."
docker-compose up -d

echo "Waiting for the application to start..."
sleep 10

# Check if the application is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ GiftManager is running successfully!"
    echo "🌐 Access the application at: http://localhost:8000"
    echo "👤 Default admin credentials: admin/admin123"
    echo "📋 View logs with: docker-compose logs -f"
    echo "🛑 Stop the application with: docker-compose down"
else
    echo "❌ Failed to start the application. Check logs with: docker-compose logs"
    exit 1
fi
