#!/bin/bash

# DSBDA Quick Start Script
# This script helps you set up and run the application

set -e

echo "🚀 DSBDA Data Analysis Assistant - Quick Start"
echo "=============================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Desktop."
    exit 1
fi

echo "✅ Docker found!"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and change SECRET_KEY to a secure random string!"
    echo "   You can generate one using: openssl rand -hex 32"
    echo ""
    read -p "Press Enter after you've updated the SECRET_KEY..."
fi

# Ensure Gemini API key is set
if ! grep -q "^GEMINI_API_KEY=" .env || grep -q "^GEMINI_API_KEY=$" .env; then
    echo "❌ GEMINI_API_KEY is missing in .env"
    echo "   Add your Gemini API key and run this script again."
    exit 1
fi

# Ask user for deployment type
echo "Choose deployment type:"
echo "1) Docker (Recommended - All services in containers)"
echo "2) Local Development (Backend + Frontend on host)"
read -p "Enter choice (1 or 2): " deployment_type

if [ "$deployment_type" = "1" ]; then
    echo ""
    echo "🐳 Starting Docker Compose..."
    docker-compose up --build
    
elif [ "$deployment_type" = "2" ]; then
    echo ""
    echo "🔧 Setting up local development environment..."
    
    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        echo "❌ PostgreSQL is not installed. Please install PostgreSQL 15+"
        exit 1
    fi
    
    # Setup backend
    echo ""
    echo "📦 Setting up Python backend..."
    cd backend
    
    if [ ! -d "venv" ]; then
        python -m venv venv
        echo "✅ Virtual environment created"
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✅ Backend dependencies installed"
    
    # Create uploads directory
    mkdir -p uploads
    
    cd ..
    
    # Setup frontend
    echo ""
    echo "📦 Setting up React frontend..."
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        npm install
        echo "✅ Frontend dependencies installed"
    fi
    
    cd ..
    
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "To start the application:"
    echo "1. Terminal 1 (Backend):"
    echo "   cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000"
    echo ""
    echo "2. Terminal 2 (Frontend):"
    echo "   cd frontend && npm run dev"
    echo ""
    echo "3. Open http://localhost:5173 in your browser"
    
else
    echo "Invalid choice. Please run the script again."
    exit 1
fi
