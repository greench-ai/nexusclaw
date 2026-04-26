#!/bin/bash
# NexusClaw One-Line Installer
# Usage:
#   curl -sL https://raw.githubusercontent.com/greench-ai/nexusclaw/main/install.sh | bash
#   # or with GitHub token (for private repos):
#   curl -sL https://raw.githubusercontent.com/greench-ai/nexusclaw/main/install.sh | GITHUB_TOKEN=ghp_xxx bash
#
# Or copy-paste this whole script and run it.

set -e

NEXUS_DIR="${NEXUS_DIR:-$HOME/nexusclaw}"
GITHUB_TOKEN="${GITHUB_TOKEN:-${GITHUB_TOKEN_ENV:-}}"
REPO="greench-ai/nexusclaw"
INSTALL_SCRIPT_URL="https://raw.githubusercontent.com/$REPO/main/install.sh"

echo "⚡ NexusClaw Installer"
echo "====================="
echo "Installing to: $NEXUS_DIR"

# 1. Download repo
if [ -d "$NEXUS_DIR/.git" ]; then
    echo "📦 Updating existing installation..."
    cd "$NEXUS_DIR" && git pull origin main 2>/dev/null || echo "   Git pull failed, using existing files"
else
    echo "📦 Downloading NexusClaw..."
    
    # Try git clone first (works for public repos)
    if git clone "https://github.com/$REPO.git" "$NEXUS_DIR" 2>/dev/null; then
        echo "   Cloned via git"
    elif [ -n "$GITHUB_TOKEN" ]; then
        # Fallback: use GitHub API to download zip
        echo "   Using GitHub token..."
        ZIP_URL="https://$GITHUB_TOKEN@api.github.com/repos/$REPO/zipball/main"
        curl -sL "$ZIP_URL" -o /tmp/nexusclaw.zip
        mkdir -p "$NEXUS_DIR"
        unzip -q /tmp/nexusclaw.zip -d /tmp/nexusclaw_extract
        mv /tmp/nexusclaw_extract/*/!(.git) "$NEXUS_DIR/" 2>/dev/null || mv /tmp/nexusclaw_extract/* "$NEXUS_DIR/"
        rm -rf /tmp/nexusclaw.zip /tmp/nexusclaw_extract
    else
        echo "❌ Private repo. Set GITHUB_TOKEN environment variable:"
        echo "   curl ... | GITHUB_TOKEN=your_token bash"
        exit 1
    fi
    cd "$NEXUS_DIR"
fi

# 2. Install dependencies
echo "🐍 Installing Python dependencies..."
pip3 install fastapi uvicorn python-multipart pydantic aiohttp python-jose[cryptography] passlib bcrypt psutil playwright --quiet 2>/dev/null || \
pip3 install fastapi uvicorn python-multipart pydantic aiohttp python-jose[cryptography] passlib bcrypt psutil

# 3. Playwright (optional)
python3 -m playwright install chromium 2>/dev/null && echo "🌐 Playwright installed" || echo "🌐 Playwright skipped (optional)"

# 4. Check Ollama
if command -v ollama &> /dev/null; then
    OLLAMA_MODELS=$(curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('models',[])))" 2>/dev/null || echo "0")
    echo "🤖 Ollama: $OLLAMA_MODELS models installed"
else
    echo "⚠️  Ollama not found. Install from https://ollama.com"
fi

# 5. Start services
echo "🚀 Starting services..."
cd "$NEXUS_DIR"

# API
if ! curl -s http://localhost:8080/health &>/dev/null; then
    nohup python3 apps/api/main.py > /tmp/nexusclaw_api.log 2>&1 &
    sleep 2
    if curl -s http://localhost:8080/health &>/dev/null; then
        echo "   ✅ API: http://localhost:8080"
    else
        echo "   ❌ API failed. Check: tail /tmp/nexusclaw_api.log"
    fi
else
    echo "   ✅ API already running"
fi

# OpenRoom
if ! curl -s http://localhost:19789/health &>/dev/null; then
    nohup python3 apps/web/server.py > /tmp/nexusclaw_openroom.log 2>&1 &
    sleep 2
    if curl -s http://localhost:19789/health &>/dev/null; then
        echo "   ✅ OpenRoom: http://localhost:19789"
    else
        echo "   ❌ OpenRoom failed. Check: tail /tmp/nexusclaw_openroom.log"
    fi
else
    echo "   ✅ OpenRoom already running"
fi

echo ""
echo "====================="
echo "📖 Docs: https://github.com/$REPO"
echo ""
echo "To update: cd $NEXUS_DIR && git pull"
echo "To uninstall: rm -rf $NEXUS_DIR"
