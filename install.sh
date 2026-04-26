#!/bin/bash
# NexusClaw One-Line Installer
# curl -sL https://raw.githubusercontent.com/greench-ai/nexusclaw/main/install.sh | bash
set -e

NEXUS_DIR="${NEXUS_DIR:-$HOME/nexusclaw}"

echo "⚡ NexusClaw Installer"
echo "====================="
echo "Installing to: $NEXUS_DIR"

# 1. Clone or update
if [ -d "$NEXUS_DIR/.git" ]; then
    echo "📦 Updating..."
    cd "$NEXUS_DIR" && git pull origin main
else
    echo "📦 Cloning..."
    git clone https://github.com/greench-ai/nexusclaw.git "$NEXUS_DIR"
    cd "$NEXUS_DIR"
fi

# 2. Install dependencies (use --break-system-packages for Debian-based systems)
echo "🐍 Installing dependencies..."
BREAK_FLAG=""
pip3 install --help 2>/dev/null | grep -q "break-system-packages" && BREAK_FLAG="--break-system-packages"

pip3 install $BREAK_FLAG fastapi uvicorn python-multipart pydantic aiohttp python-jose[cryptography] passlib bcrypt psutil 2>/dev/null || \
pip3 install fastapi uvicorn python-multipart pydantic aiohttp python-jose[cryptography] passlib bcrypt psutil

# 3. Playwright (optional)
pip3 install $BREAK_FLAG playwright 2>/dev/null && python3 -m playwright install chromium 2>/dev/null && echo "🌐 Playwright ready" || echo "🌐 Playwright skipped"

# 4. Start services
echo "🚀 Starting..."
cd "$NEXUS_DIR"

start_if_needed() {
    local port=$1
    local cmd=$2
    if ! curl -s http://localhost:$port/health &>/dev/null; then
        nohup python3 $cmd > /tmp/nexusclaw_${port}.log 2>&1 &
        sleep 2
        if curl -s http://localhost:$port/health &>/dev/null; then
            echo "   ✅ http://localhost:$port"
        else
            echo "   ❌ Port $port failed — tail /tmp/nexusclaw_${port}.log"
        fi
    else
        echo "   ✅ Port $port already running"
    fi
}

start_if_needed 8080 "apps/api/main.py"
start_if_needed 19789 "apps/web/server.py"

echo ""
echo "====================="
echo "🌐 OpenRoom: http://localhost:19789"
echo "🔗 API:       http://localhost:8080"
echo "📖 Docs:     https://github.com/greench-ai/nexusclaw"
echo ""
echo "Update: cd $NEXUS_DIR && git pull"
