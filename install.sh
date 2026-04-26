#!/bin/bash
# NexusClaw One-Line Installer
# curl -s https://raw.githubusercontent.com/greench-ai/nexusclaw/main/install.sh | bash
set -e

NEXUS_DIR="${NEXUS_DIR:-$HOME/nexusclaw}"
echo "⚡ NexusClaw Installer"
echo "====================="
echo "Installing to: $NEXUS_DIR"

# 1. Clone or pull
if [ -d "$NEXUS_DIR/.git" ]; then
    echo "📦 Updating existing installation..."
    cd "$NEXUS_DIR" && git pull origin main
else
    echo "📦 Cloning NexusClaw..."
    git clone https://github.com/greench-ai/nexusclaw.git "$NEXUS_DIR"
    cd "$NEXUS_DIR"
fi

# 2. Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install fastapi uvicorn python-multipart pydantic aiohttp python-jose[cryptography] passlib bcrypt psutil --quiet

# 3. Install Playwright (optional, for browser automation)
echo "🌐 Installing Playwright (optional)..."
pip3 install playwright --quiet 2>/dev/null || true
python3 -m playwright install chromium 2>/dev/null || true

# 4. Check Docker
if command -v docker &> /dev/null; then
    echo "🐳 Docker found"
else
    echo "⚠️  Docker not found. Install from https://docker.com"
fi

# 5. Check Ollama
if command -v ollama &> /dev/null; then
    echo "🤖 Ollama found"
    OLLAMA_MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('models',[])))" 2>/dev/null || echo "0")
    echo "   Models installed: $OLLAMA_MODELS"
    if [ "$OLLAMA_MODELS" = "0" ]; then
        echo "   Run: ollama pull llama3.2"
    fi
else
    echo "⚠️  Ollama not found. Install from https://ollama.com"
    echo "   Then: ollama pull llama3.2"
fi

# 6. Start services
echo "🚀 Starting services..."
cd "$NEXUS_DIR"

# Start API in background
if ! curl -s http://localhost:8080/health &>/dev/null; then
    nohup python3 apps/api/main.py > /tmp/nexusclaw_api.log 2>&1 &
    echo "   API started on port 8080"
else
    echo "   API already running on port 8080"
fi

# Start OpenRoom in background
if ! curl -s http://localhost:19789/health &>/dev/null; then
    nohup python3 apps/web/server.py > /tmp/nexusclaw_openroom.log 2>&1 &
    echo "   OpenRoom started on port 19789"
else
    echo "   OpenRoom already running on port 19789"
fi

sleep 2

# 7. Verify
echo ""
echo "====================="
if curl -s http://localhost:8080/health &>/dev/null; then
    echo "✅ API:        http://localhost:8080"
else
    echo "❌ API failed to start. Check /tmp/nexusclaw_api.log"
fi
if curl -s http://localhost:19789/health &>/dev/null; then
    echo "✅ OpenRoom:   http://localhost:19789"
else
    echo "❌ OpenRoom failed to start. Check /tmp/nexusclaw_openroom.log"
fi
echo ""
echo "📖 Docs: https://github.com/greench-ai/nexusclaw"
echo "💬 Start chatting at http://localhost:19789"
echo ""
echo "To update later: cd $NEXUS_DIR && git pull"
