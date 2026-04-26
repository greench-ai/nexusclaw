#!/bin/bash
set -e

echo "
╔══════════════════════════════════════════════════════════╗
║                    NEXUSCLAW                           ║
║         Your framework. Your rules.                   ║
║              No restrictions.                          ║
╚══════════════════════════════════════════════════════════╝
"

NEXUS_DIR="${HOME}/.nexusclaw"
mkdir -p "${NEXUS_DIR}"

# Color
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

step() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

# Detect OS
OS="$(uname -s)"
ARCH="$(uname -m)"
step "Detected: ${OS} (${ARCH})"

# Check Python
if ! command -v python3 &> /dev/null; then
    error "Python 3 not found. Install from python.org or 'brew install python3'"
    exit 1
fi
step "Python 3 found: $(python3 --version)"

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER=1
    step "Docker found — Qdrant + Redis available"
else
    DOCKER=0
    warn "Docker not found — skipping Qdrant/Redis"
fi

# Check Ollama
if command -v ollama &> /dev/null; then
    OLLAMA=1
    step "Ollama found — free local models available"
else
    OLLAMA=0
    warn "Ollama not found — run 'curl -fsSL https://ollama.com/install.sh | bash'"
fi

# Create config
step "Creating configuration..."
cat > "${NEXUS_DIR}/config.json" << 'EOF'
{
  "version": "0.11.0",
  "workspace": "~/.nexusclaw",
  "api": {
    "host": "0.0.0.0",
    "port": 8080
  },
  "openroom": {
    "host": "0.0.0.0",
    "port": 51234
  },
  "providers": {
    "ollama": {
      "url": "http://localhost:11434",
      "default_model": "llama3.2"
    }
  },
  "memory": {
    "mode": "hybrid",
    "qdrant_url": "http://localhost:6333"
  }
}
EOF

# Copy source
step "Installing NexusClaw source..."
cp -r "$(dirname "$0")/src" "${NEXUS_DIR}/"
cp -r "$(dirname "$0")/apps" "${NEXUS_DIR}/"

# Create symlinks
step "Creating command: nexusclaw"
if [ -d "${HOME}/bin" ]; then
    ln -sf "${NEXUS_DIR}/src/cli/main.py" "${HOME}/bin/nexusclaw"
    chmod +x "${HOME}/bin/nexusclaw"
elif [ -d "/usr/local/bin" ]; then
    sudo ln -sf "${NEXUS_DIR}/src/cli/main.py" "/usr/local/bin/nexusclaw"
    chmod +x "/usr/local/bin/nexusclaw"
else
    echo "Add to PATH: export PATH=${NEXUS_DIR}/src/cli:\$PATH"
fi

# Docker services
if [ "${DOCKER}" = 1 ]; then
    step "Starting Docker services (Qdrant, Redis)..."
    docker run -d --name nexus-qdrant \
        -p 6333:6333 \
        -p 6334:6334 \
        qdrant/qdrant > /dev/null 2>&1 || true
    
    docker run -d --name nexus-redis \
        -p 6379:6379 \
        redis:7-alpine > /dev/null 2>&1 || true
    
    step "Docker services started"
fi

# Final message
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              INSTALLATION COMPLETE                       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Next steps:"
echo "  1. nexusclaw setup          # First-time configuration"
echo "  2. nexusclaw chat          # Start chatting"
echo "  3. python3 apps/api/main.py # Start API server"
echo "  4. python3 apps/web/server.py  # Start web UI"
echo ""
echo "  Or run everything with Docker:"
echo "  docker-compose up"
echo ""
