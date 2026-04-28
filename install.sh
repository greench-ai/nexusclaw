#!/usr/bin/env bash
# NexusClaw One-Line Installer v2.0
# curl -sL https://github.com/greench-ai/nexusclaw/raw/main/install.sh | bash
set -euo pipefail

NEXUS_VERSION="${NEXUS_VERSION:-main}"
NEXUS_DIR="${NEXUS_DIR:-$HOME/nexusclaw}"
NEXUS_CONFIG_DIR="${NEXUS_CONFIG_DIR:-$HOME/.nexusclaw}"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; MAGENTA='\033[0;35m'; CYAN='\033[0;36m'; NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[ OK ]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERR ]${NC}  $*"; }
step()  { echo -e "${MAGENTA}[STEP]${NC}  $*"; }

log()   { echo "[$(date '+%H:%M:%S')] $*"; }

banner() {
  echo ""
  echo -e "${CYAN}   _   _                      _ ${NC}"
  echo -e "${CYAN}  | \\ | | __ _  __ _ ___ _   _| |${NC}"
  echo -e "${CYAN}  |  \\| |/ _\` |/ _\` / _ \\ | | | |${NC}"
  echo -e "${CYAN}  | |\\  | (_| | (_| \\  __/ |_| |_|${NC}"
  echo -e "${CYAN}  |_| \\_|\\__,_|\\__, |\\___|\\__,_| (_)${NC}"
  echo -e "${CYAN}  ${NC}  |  _ \\| |__  / _| | |    | |__  _   _${NC}"
  echo -e "${CYAN}  ${NC} | |_) | '_ \\| |_| | |    | '_ \\| | | |${NC}"
  echo -e "${CYAN}  ${NC} |  __/| | | |  _| | |___ | |_) | |_| |${NC}"
  echo -e "${CYAN}  ${NC} |_|   |_| |_|_| |_|_____|_.__/ \\__, |${NC}"
  echo ""
  echo -e "  ${MAGENTA}NexusClaw v1.0 — Your framework. Your rules.${NC}"
  echo ""
}

detect_os() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macos"
  elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    echo "windows"
  elif grep -qEi "(Microsoft|WSL)" /proc/version 2>/dev/null; then
    echo "wsl"
  elif [[ -f /etc/os-release ]]; then
    ID=$(grep ^ID= /etc/os-release | cut -d= -f2 | tr -d '"')
    case "$ID" in
      debian|ubuntu|kali) echo "debian" ;;
      fedora|rhel|centos) echo "rhel" ;;
      arch) echo "arch" ;;
      alpine) echo "alpine" ;;
      *) echo "linux" ;;
    esac
  else
    echo "linux"
  fi
}

need_cmd() {
  if ! command -v "$1" &>/dev/null; then
    warn "Missing: $1"
    return 1
  fi
  return 0
}

install_python() {
  local os=$1
  if need_cmd python3; then
    PYTHON_CMD=python3
  elif need_cmd python; then
    PYTHON_CMD=python
  else
    step "Installing Python..."
    case "$os" in
      debian|wsl)
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>/dev/null || true
        sudo apt-get install -y python3 python3-pip python3-venv 2>/dev/null || \
        sudo apt install -y python3 python3-pip python3-venv
        ;;
      macos)
        if need_cmd brew; then
          brew install python@3.12
        else
          warn "Install Homebrew first: https://brew.sh"
        fi
        ;;
      rhel)
        sudo dnf install -y python3 python3-pip
        ;;
      arch)
        sudo pacman -S --noconfirm python python-pip
        ;;
    esac
    PYTHON_CMD=python3
  fi
  echo "$PYTHON_CMD"
}

install_nodejs() {
  local os=$1
  if need_cmd node; then
    NODE_VERSION=$(node --version)
    ok "Node.js already: $NODE_VERSION"
    return 0
  fi
  step "Installing Node.js..."
  case "$os" in
    debian|wsl)
      curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>/dev/null || true
      sudo apt-get install -y nodejs 2>/dev/null || sudo apt install -y nodejs
      ;;
    macos)
      if need_cmd brew; then
        brew install node@20
      fi
      ;;
    rhel)
      curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash 2>/dev/null || \
      sudo dnf install -y nodejs
      ;;
  esac
}

install_docker() {
  if need_cmd docker; then
    ok "Docker found"
    return 0
  fi
  step "Installing Docker..."
  case "$(detect_os)" in
    debian|wsl)
      curl -fsSL https://get.docker.com | sh 2>/dev/null || \
      sudo apt-get install -y docker.io docker-compose
      sudo usermod -aG docker "$USER" 2>/dev/null || true
      ;;
    macos)
      warn "Install Docker Desktop from https://docker.com/desktop/mac"
      ;;
    windows)
      warn "Install Docker Desktop from https://docker.com/desktop/windows"
      ;;
  esac
}

install_pip_packages() {
  local python=$1
  step "Installing Python packages..."
  local break_flag=""
  $python -m pip --help 2>/dev/null | grep -q "break-system-packages" && break_flag="--break-system-packages"
  $python -m pip install $break_flag --upgrade pip 2>/dev/null | tail -1
  $python -m pip install $break_flag -r "$NEXUS_DIR/requirements.txt" 2>&1 | tail -3
  ok "Python packages installed"
}

install_playwright() {
  local python=$1
  step "Installing Playwright (browser automation)..."
  local break_flag=""
  $python -m pip --help 2>/dev/null | grep -q "break-system-packages" && break_flag="--break-system-packages"
  if $python -m pip install $break_flag playwright 2>/dev/null | tail -1; then
    $python -m playwright install chromium 2>/dev/null && ok "Playwright ready" || warn "Playwright skipped (chromium install failed)"
  else
    warn "Playwright install failed — browser control disabled"
  fi
}

clone_or_update() {
  if [[ -d "$NEXUS_DIR/.git" ]]; then
    info "Updating NexusClaw in $NEXUS_DIR"
    cd "$NEXUS_DIR" && git pull origin main 2>/dev/null && ok "Updated" || warn "Update failed (non-git or offline)"
  else
    step "Cloning NexusClaw..."
    mkdir -p "$(dirname "$NEXUS_DIR")"
    git clone https://github.com/greench-ai/nexusclaw.git "$NEXUS_DIR" 2>/dev/null || {
      warn "Git clone failed — creating directory structure manually"
      mkdir -p "$NEXUS_DIR"
    }
    cd "$NEXUS_DIR"
  fi
}

create_config_dir() {
  mkdir -p "$NEXUS_CONFIG_DIR"
  if [[ ! -f "$NEXUS_CONFIG_DIR/config.json" ]]; then
    cat > "$NEXUS_CONFIG_DIR/config.json" <<'EOF'
{
  "version": "1.0.0",
  "api": {
    "host": "0.0.0.0",
    "port": 8080,
    "secret": "change-me-with-nexusclaw-setup"
  },
  "web": {
    "host": "0.0.0.0",
    "port": 19789
  },
  "providers": {
    "openai": { "api_key": "" },
    "anthropic": { "api_key": "" },
    "openrouter": { "api_key": "" },
    "perplexity": { "api_key": "" },
    "ollama": { "url": "http://localhost:11434" }
  },
  "memory": {
    "vector_db": "qdrant",
    "qdrant_url": "http://localhost:6333",
    "embedding_model": "nomic-embed-text"
  },
  "evoclaw": {
    "enabled": true,
    "heartbeat_interval": 300,
    "research_enabled": true
  },
  "soul": {
    "template": "assistant"
  }
}
EOF
    ok "Config created at $NEXUS_CONFIG_DIR/config.json"
  fi
}

start_qdrant() {
  if curl -s http://localhost:6333/readyz &>/dev/null; then
    ok "Qdrant already running"
    return 0
  fi
  step "Starting Qdrant..."
  if command -v docker &>/dev/null; then
    docker run -d --name nexusclaw-qdrant \
      -p 6333:6333 -p 6334:6334 \
      -v "$NEXUS_CONFIG_DIR/qdrant:/qdrant/storage" \
      qdrant/qdrant:latest 2>/dev/null && ok "Qdrant started" || warn "Qdrant start failed"
  else
    warn "Docker not available — Qdrant not started (optional)"
  fi
}

start_nexusclaw() {
  local python=$1
  step "Starting NexusClaw services..."
  cd "$NEXUS_DIR"

  start_service() {
    local name=$1
    local port=$2
    local cmd=$3
    if curl -s http://localhost:$port/health &>/dev/null 2>&1; then
      ok "$name already running on port $port"
      return 0
    fi
    nohup $python $cmd > "$NEXUS_CONFIG_DIR/logs/${name}.log" 2>&1 &
    sleep 3
    if curl -s http://localhost:$port/health &>/dev/null 2>&1; then
      ok "$name started on port $port"
    else
      err "$name failed — see $NEXUS_CONFIG_DIR/logs/${name}.log"
    fi
  }

  mkdir -p "$NEXUS_CONFIG_DIR/logs"

  start_service "API" 8080 "$NEXUS_DIR/apps/api/main.py"
  start_service "Web UI" 19789 "$NEXUS_DIR/apps/web/server.py"
}

run_setup_wizard() {
  local python=$1
  if [[ -f "$NEXUS_DIR/src/onboard/setup.py" ]]; then
    if [[ ! -t 0 ]]; then
      info "Skipping interactive setup (non-TTY)"
      info "Run manually: $python $NEXUS_DIR/src/onboard/setup.py"
      return 0
    fi
    step "Running setup wizard..."
    $python "$NEXUS_DIR/src/onboard/setup.py" && ok "Setup complete" || warn "Setup skipped"
  fi
}

print_summary() {
  echo ""
  echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
  echo -e "  ${GREEN}✅ NexusClaw installed successfully!${NC}"
  echo ""
  echo -e "  🌐 Web UI:    ${GREEN}http://localhost:19789${NC}"
  echo -e "  🔗 API:       ${GREEN}http://localhost:8080${NC}"
  echo -e "  📖 Docs:     ${GREEN}http://localhost:19789/docs${NC}"
  echo ""
  echo -e "  📁 Install:   $NEXUS_DIR"
  echo -e "  ⚙️  Config:   $NEXUS_CONFIG_DIR/config.json"
  echo ""
  echo -e "  ${YELLOW}Next steps:${NC}"
  echo -e "  $ nexusclaw setup              # Configure API keys"
  echo -e "  $ nexusclaw chat               # Start chatting"
  echo -e "  $ nexusclaw doctor             # Check system health"
  echo -e "  $ nexusclaw update             # Update to latest"
  echo ""
  echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
}

main() {
  banner

  local os
  os=$(detect_os)
  info "Detected OS: $os"

  clone_or_update

  local python
  python=$(install_python "$os")

  install_nodejs "$os"

  install_pip_packages "$python"

  # Optional: ask before playwright
  if [[ "${NEXUSCLAW_PLAYWRIGHT:-1}" == "1" ]]; then
    install_playwright "$python"
  else
    info "Skipping Playwright (set NEXUSCLAW_PLAYWRIGHT=1 to install)"
  fi

  create_config_dir
  start_qdrant
  run_setup_wizard "$python"
  start_nexusclaw "$python"

  print_summary
}

main "$@"
