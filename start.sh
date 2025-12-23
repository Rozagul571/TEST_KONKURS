#!/bin/bash

echo "🚀 Starting Konkurs Bot System..."

# Create logs directory if not exists
mkdir -p logs

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Creating from .env.example..."
    cp .env.example .env
    echo "⚠️ Please update .env file with your values!"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Start Redis if not running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "🔴 Redis is not running. Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Check Django database migrations
echo "🗄️ Checking database migrations..."
python manage.py migrate

# Start FastAPI
echo "🚀 Starting FastAPI server..."
uvicorn fastapi_app.main:app --host 0.0.0.0 --port 8001 --reload