#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# NexusClaw Installer  |  curl -fsSL https://raw.githubusercontent.com/greench-ai/nexusclaw/main/install.sh | bash
# ─────────────────────────────────────────────────────────────────────────────
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

log()  { echo -e "${CYAN}[NexusClaw]${RESET} $*"; }
ok()   { echo -e "${GREEN}✓${RESET} $*"; }
warn() { echo -e "${YELLOW}⚠${RESET} $*"; }
die()  { echo -e "${RED}✗${RESET} $*" >&2; exit 1; }

echo ""
echo -e "${BOLD}⚡ NexusClaw${RESET} — Direct provider AI chat. No LiteLLM."
echo -e "  OpenClaw-style onboarding, self-hosted, private."
echo ""

# ── Detect OS ──────────────────────────────────────────────────────────────
OS="$(uname -s)"
if [[ "$OS" == "Linux" && -f "/proc/version" && "$(cat /proc/version 2>/dev/null)" == *"Microsoft"* ]]; then
  OS="WSL"
elif [[ "$OS" == "Darwin" ]]; then
  OS="macOS"
fi
log "Detected: $OS"

# ── Check Docker ───────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  die "Docker is not installed. Install from https://docker.com/get-started"
fi
docker info &>/dev/null || die "Docker is not running. Start Docker and try again."
ok "Docker is available"

# ── Check Docker Compose ──────────────────────────────────────────────────
if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null; then
  die "Docker Compose is not installed."
fi
COMPOSE="$(command -v docker-compose 2>/dev/null && echo docker-compose || echo "docker compose")"
ok "Docker Compose: $COMPOSE"

# ── Create nexusclaw dir ──────────────────────────────────────────────────
NEXUS_DIR="$HOME/nexusclaw"
if [[ -d "$NEXUS_DIR" ]]; then
  warn "NexusClaw directory already exists at $NEXUS_DIR"
else
  log "Cloning NexusClaw..."
  git clone https://github.com/greench-ai/nexusclaw.git "$NEXUS_DIR"
  ok "Cloned to $NEXUS_DIR"
fi

cd "$NEXUS_DIR"

# ── Build Docker image ────────────────────────────────────────────────────
log "Building Docker image..."
docker build -f Dockerfile.app -t nexusclaw:latest . 2>&1 | tail -3
ok "Docker image built"

# ── Start Qdrant (required for RAG) ─────────────────────────────────────
log "Starting Qdrant vector database..."
docker run -d \
  --name nexusclaw-qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v "$HOME/nexusclaw-qdrant:/root/qdrant/storage" \
  --restart unless-stopped \
  qdrant/qdrant:latest 2>/dev/null || \
  docker start nexusclaw-qdrant 2>/dev/null || true
ok "Qdrant running at localhost:6333"

# ── Start NexusClaw API server ──────────────────────────────────────────────
log "Starting NexusClaw..."
docker run -d \
  --name nexusclaw \
  -p 14300:8000 \
  -v "$HOME/.nexusclaw:/root/.nexusclaw" \
  --restart unless-stopped \
  --add-host=host.docker.internal:host-gateway \
  nexusclaw:latest 2>/dev/null || \
  docker start nexusclaw 2>/dev/null || true
ok "NexusClaw API running at localhost:14300"

# Wait for server
sleep 5
if curl -sf http://localhost:14300/health &>/dev/null; then
  ok "NexusClaw is running at http://localhost:14300"
else
  warn "Server may need a moment — check http://localhost:14300"
fi

# Verify Qdrant
if curl -sf http://localhost:6333/readyz &>/dev/null; then
  ok "Qdrant ready at localhost:6333"
else
  warn "Qdrant may need a moment — it's optional for basic chat"
fi

# ── Onboarding ────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}─────────────────────────────────────────────${RESET}"
echo -e "${BOLD}⚡ NexusClaw Onboarding${RESET}"
echo -e "${BOLD}─────────────────────────────────────────────${RESET}"
echo ""
echo "Before chatting, configure your AI provider."
echo ""
echo "Run the interactive setup wizard:"
echo -e "  ${GREEN}nexusclaw onboard${RESET}"
echo ""
echo "Or open in your browser:"
echo -e "  ${GREEN}http://localhost:14300/setup${RESET}"
echo ""
echo "Already have a config? Run:"
echo -e "  ${GREEN}nexusclaw status${RESET}"
echo ""
