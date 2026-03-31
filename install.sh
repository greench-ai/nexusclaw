#!/usr/bin/env bash
# NexusClaw — Native Install Script
# Usage: curl -sSL https://raw.githubusercontent.com/greench-ai/nexusclaw/main/install.sh | bash
# Or:    bash install.sh [--daemon] [--docker]

set -euo pipefail

# ─── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Config ─────────────────────────────────────────────────────────────────────
APP_NAME="NexusClaw"
BIN_NAME="nexusclaw"
REPO="greench-ai/nexusclaw"
CONFIG_DIR="$HOME/.nexusclaw"
WORKSPACE_DIR="$CONFIG_DIR/workspace"
SKILLS_DIR="$WORKSPACE_DIR/skills"
LIBRARY_DIR="$HOME/nexusclaw/library"
MIN_NODE_VERSION=22

# ─── Args ───────────────────────────────────────────────────────────────────────
INSTALL_DAEMON=false
USE_DOCKER=false
for arg in "$@"; do
  case $arg in
    --daemon) INSTALL_DAEMON=true ;;
    --docker) USE_DOCKER=true ;;
  esac
done

# ─── Helpers ────────────────────────────────────────────────────────────────────
log()  { echo -e "${CYAN}[NexusClaw]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
banner() {
  echo -e "${BOLD}${CYAN}"
  echo "  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗ ██████╗██╗      █████╗ ██╗    ██╗"
  echo "  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝██╔════╝██║     ██╔══██╗██║    ██║"
  echo "  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗██║     ██║     ███████║██║ █╗ ██║"
  echo "  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║██║     ██║     ██╔══██║██║███╗██║"
  echo "  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║╚██████╗███████╗██║  ██║╚███╔███╔╝"
  echo "  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝ "
  echo -e "${NC}"
  echo -e "  ${BOLD}Personal AI Gateway — Built on OpenClaw${NC}"
  echo ""
}

# ─── Checks ─────────────────────────────────────────────────────────────────────
check_node() {
  if ! command -v node &>/dev/null; then
    fail "Node.js not found. Install Node $MIN_NODE_VERSION+ from https://nodejs.org"
  fi
  local version
  version=$(node -e "process.stdout.write(process.versions.node.split('.')[0])")
  if [ "$version" -lt "$MIN_NODE_VERSION" ]; then
    fail "Node $version found, but $MIN_NODE_VERSION+ is required."
  fi
  ok "Node.js $version"
}

check_pnpm() {
  if ! command -v pnpm &>/dev/null; then
    log "Installing pnpm..."
    npm install -g pnpm
  fi
  ok "pnpm $(pnpm --version)"
}

check_git() {
  if ! command -v git &>/dev/null; then
    fail "git not found. Please install git."
  fi
  ok "git $(git --version | awk '{print $3}')"
}

check_docker() {
  if ! command -v docker &>/dev/null; then
    fail "Docker not found. Install Docker first: https://docs.docker.com/get-docker/"
  fi
  ok "Docker $(docker --version | awk '{print $3}' | tr -d ',')"
}

# ─── Install ────────────────────────────────────────────────────────────────────
install_native() {
  log "Installing $APP_NAME (native)..."

  # Clone if not already in the repo
  if [ ! -f "package.json" ]; then
    log "Cloning $APP_NAME..."
    git clone --depth=1 "https://github.com/$REPO.git" nexusclaw
    cd nexusclaw
  fi

  log "Installing dependencies..."
  pnpm install

  log "Building UI..."
  pnpm ui:build

  log "Building $APP_NAME..."
  pnpm build

  log "Installing globally..."
  npm install -g .

  ok "$APP_NAME installed → $(which $BIN_NAME)"
}

install_docker() {
  log "Starting $APP_NAME via Docker..."
  if [ ! -f "docker-compose.yml" ]; then
    log "Downloading docker-compose.yml..."
    curl -sSL "https://raw.githubusercontent.com/$REPO/main/docker-compose.yml" -o docker-compose.yml
    curl -sSL "https://raw.githubusercontent.com/$REPO/main/.env.example" -o .env
    warn "Review .env before continuing."
    read -rp "Press Enter to continue..."
  fi
  docker compose up -d
  ok "NexusClaw running via Docker. WebUI at http://localhost:19789"
}

# ─── Setup Dirs ────────────────────────────────────────────────────────────────
setup_dirs() {
  mkdir -p "$CONFIG_DIR" "$WORKSPACE_DIR" "$SKILLS_DIR" "$LIBRARY_DIR"
  ok "Config dir: $CONFIG_DIR"
  ok "Library dir: $LIBRARY_DIR"
}

# ─── Default Config ─────────────────────────────────────────────────────────────
write_default_config() {
  local config_file="$CONFIG_DIR/nexusclaw.json"
  if [ -f "$config_file" ]; then
    warn "Config already exists at $config_file — skipping."
    return
  fi

  cat > "$config_file" <<'EOF'
{
  "agent": {
    "model": "anthropic/claude-opus-4-6",
    "workspace": "~/.nexusclaw/workspace"
  },
  "gateway": {
    "port": 19789,
    "bind": "loopback"
  },
  "cron": [
    {
      "schedule": "*/15 * * * *",
      "skill": "evoclaw/heartbeat",
      "description": "EvoClaw soul evolution heartbeat"
    },
    {
      "schedule": "*/30 * * * *",
      "skill": "memory-save/run",
      "description": "Memory consolidation — saves session context"
    },
    {
      "schedule": "0 * * * *",
      "skill": "library-update/run",
      "description": "Library documentation update"
    }
  ],
  "ui": {
    "theme": "aurora",
    "claudePreview": true,
    "chromeExtension": true
  }
}
EOF
  ok "Default config written to $config_file"
}

# ─── Copy Bundled Skills ────────────────────────────────────────────────────────
install_skills() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local src_skills="$script_dir/skills"

  if [ -d "$src_skills" ]; then
    log "Installing bundled skills..."
    for skill_dir in "$src_skills"/*/; do
      skill_name=$(basename "$skill_dir")
      dest="$SKILLS_DIR/$skill_name"
      if [ ! -d "$dest" ]; then
        cp -r "$skill_dir" "$dest"
        ok "Skill installed: $skill_name"
      else
        warn "Skill already exists: $skill_name — skipping"
      fi
    done
  else
    warn "Skills source dir not found — skipping bundled skill install"
  fi
}

# ─── Systemd Daemon ─────────────────────────────────────────────────────────────
install_systemd() {
  if [ "$(uname -s)" != "Linux" ]; then
    warn "Systemd daemon install only supported on Linux."
    return
  fi
  if ! command -v systemctl &>/dev/null; then
    warn "systemctl not found — skipping daemon install."
    return
  fi

  local service_file="$HOME/.config/systemd/user/nexusclaw-gateway.service"
  mkdir -p "$(dirname "$service_file")"

  cat > "$service_file" <<EOF
[Unit]
Description=NexusClaw Gateway
After=network.target

[Service]
Type=simple
ExecStart=$(which nexusclaw) gateway --port 19789
Restart=always
RestartSec=5
Environment=HOME=$HOME
WorkingDirectory=$HOME

[Install]
WantedBy=default.target
EOF

  systemctl --user daemon-reload
  systemctl --user enable nexusclaw-gateway
  systemctl --user start nexusclaw-gateway
  ok "NexusClaw Gateway daemon installed and started (systemd user service)"
  ok "Control with: systemctl --user [start|stop|restart|status] nexusclaw-gateway"
}

# ─── Main ───────────────────────────────────────────────────────────────────────
main() {
  banner
  log "Starting $APP_NAME installation..."

  if $USE_DOCKER; then
    check_docker
    setup_dirs
    write_default_config
    install_docker
  else
    check_node
    check_pnpm
    check_git
    install_native
    setup_dirs
    write_default_config
    install_skills

    if $INSTALL_DAEMON; then
      install_systemd
    fi
  fi

  echo ""
  echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}  NexusClaw installed successfully! 🦞${NC}"
  echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
  echo ""
  echo -e "  Start:        ${CYAN}nexusclaw gateway${NC}"
  echo -e "  Onboard:      ${CYAN}nexusclaw onboard --install-daemon${NC}"
  echo -e "  WebUI:        ${CYAN}http://localhost:19789${NC}"
  echo -e "  Config:       ${CYAN}~/.nexusclaw/nexusclaw.json${NC}"
  echo -e "  Library:      ${CYAN}~/nexusclaw/library/${NC}"
  echo ""
}

main "$@"
