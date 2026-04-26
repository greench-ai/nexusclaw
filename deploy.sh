#!/bin/bash
# NexusClaw Deployment Script
set -e

echo "🚀 Deploying NexusClaw..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install from https://docker.com"
    exit 1
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found."
    exit 1
fi

# Pull latest
echo "📦 Pulling latest changes..."
git pull origin main

# Build and start
echo "🔨 Building containers..."
docker compose build

echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "✅ NexusClaw deployed!"
echo "   API:      http://localhost:8080"
echo "   Web UI:   http://localhost:51234"
echo "   Health:   http://localhost:8080/health"
echo ""
echo "   Telegram: Start a chat with @YourBot"
echo "   Discord:  Add bot to your server"
echo ""
echo "To watch logs: docker compose logs -f"
