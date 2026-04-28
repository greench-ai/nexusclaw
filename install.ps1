# NexusClaw Windows Installer v1.0
# Run: irm https://github.com/greench-ai/nexusclaw/raw/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$GREEN  = "`e[32m"
$YELLOW = "`e[33m"
$BLUE   = "`e[34m"
$RED    = "`e[31m"
$NC     = "`e[0m"

$NEXUS_DIR    = "$HOME\nexusclaw"
$NEXUS_CONFIG = "$HOME\.nexusclaw"

function Write-Info($msg)  { Write-Host "${BLUE}[INFO]${NC}  $msg" }
function Write-Ok($msg)   { Write-Host "${GREEN}[ OK ]${NC}  $msg" }
function Write-Warn($msg) { Write-Host "${YELLOW}[WARN]${NC} $msg" }
function Write-Step($msg) { Write-Host "${BLUE}[STEP]${NC} $msg" }
function Write-Err($msg)   { Write-Host "${RED}[ ERR]${NC}  $msg" }

Write-Host ""
Write-Host "${GREEN}   _   _                      _ ${NC}" -NoNewline
Write-Host "       _   _                 "
Write-Host "${GREEN}  | \ | | __ _  __ _ ___ _   _| |${NC}  ${GREEN}| |__  _   _${NC}"
Write-Host "${GREEN}  |  \| |/ _\` |/ _\` / _ \ | | | |${NC}  ${GREEN}| '_ \| | | |${NC}"
Write-Host "${GREEN}  | |\  | (_| | (_| \  __/ |_| | |${NC}  ${GREEN}| |_) | |_| |${NC}"
Write-Host "${GREEN}  |_| \_|\__,_|\__, |\___|\__,_|_|${NC}  ${GREEN}|_.__/ \__, |${NC}"
Write-Host "${GREEN}  ${NC}  |  _ \| |__  / _| | |    | |__  _   _"
Write-Host "${GREEN}  ${NC}  | |_) | '_ \| |_| | |    | '_ \| | | |"
Write-Host "${GREEN}  ${NC}  |  __/| | | |  _| | |___ | |_) | |_| |"
Write-Host "${GREEN}  ${NC}  |_|   |_| |_|_| |_|_____|_.__/ \__, |"
Write-Host ""
Write-Host "  ${GREEN}NexusClaw v1.0 — Your framework. Your rules.${NC}"
Write-Host ""

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Warn "Run as Administrator for best results (Docker, services)"
}

# Install Python
Write-Step "Checking Python..."
$pythonCmd = $null
foreach ($cmd in @("python3", "python", "py")) {
    try {
        $result = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            Write-Ok "Found: $result"
            break
        }
    } catch {}
}
if (-not $pythonCmd) {
    Write-Step "Installing Python..."
    Write-Info "Download from: https://www.python.org/downloads/"
    Write-Info "Or run: winget install Python.Python.3.12"
    $pythonCmd = "python"
}

# Clone or update
Write-Step "Cloning NexusClaw..."
if (Test-Path "$NEXUS_DIR\.git") {
    Push-Location $NEXUS_DIR
    git pull origin main 2>$null
    Pop-Location
    Write-Ok "Updated: $NEXUS_DIR"
} else {
    git clone https://github.com/greench-ai/nexusclaw.git $NEXUS_DIR 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Git clone failed. Download manually from GitHub."
        exit 1
    }
    Write-Ok "Cloned: $NEXUS_DIR"
}

# Install Python packages
Write-Step "Installing Python packages..."
& $pythonCmd -m pip install --upgrade pip 2>$null | Out-Null
$breakFlag = ""
& $pythonCmd -m pip install --help 2>$null | Select-String -Pattern "break-system-packages" -Quiet
if ($LASTEXITCODE -eq 0) { $breakFlag = "--break-system-packages" }
& $pythonCmd -m pip install $breakFlag -r "$NEXUS_DIR\requirements.txt" 2>$null | Select-Object -Last 3

# Create config
Write-Step "Creating config..."
New-Item -ItemType Directory -Force -Path $NEXUS_CONFIG | Out-Null
$configPath = "$NEXUS_CONFIG\config.json"
if (-not (Test-Path $configPath)) {
    @{
        version = "1.0.0"
        api = @{ host = "0.0.0.0"; port = 8080; secret = "change-me-in-setup" }
        web = @{ host = "0.0.0.0"; port = 19789 }
        providers = @{
            openai = @{ api_key = "" }
            anthropic = @{ api_key = "" }
            openrouter = @{ api_key = "" }
            perplexity = @{ api_key = "" }
            ollama = @{ url = "http://localhost:11434" }
        }
        memory = @{
            vector_db = "qdrant"
            qdrant_url = "http://localhost:6333"
        }
        evoclaw = @{ enabled = $true; heartbeat_interval = 300 }
        soul = @{ template = "assistant" }
    } | ConvertTo-Json -Depth 5 | Set-Content $configPath
    Write-Ok "Config: $configPath"
}

# Install Docker (optional)
Write-Step "Docker..."
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Ok "Docker found"
    Write-Info "Run: docker-compose up -d"
} else {
    Write-Warn "Docker not found. Install from: https://docker.com/desktop/windows"
}

Write-Host ""
Write-Host "${GREEN}═══════════════════════════════════════════════════════${NC}"
Write-Host "  ${GREEN}✅ Done!${NC}"
Write-Host ""
Write-Host "  🌐 Web UI:    ${GREEN}http://localhost:19789${NC}"
Write-Host "  🔗 API:       ${GREEN}http://localhost:8080${NC}"
Write-Host ""
Write-Host "  📁 Install:   $NEXUS_DIR"
Write-Host "  ⚙️  Config:   $NEXUS_CONFIG\config.json"
Write-Host ""
Write-Host "  ${YELLOW}Start manually:${NC}"
Write-Host "  py \$NEXUS_DIR\apps\api\main.py"
Write-Host "  py \$NEXUS_DIR\apps\web\server.py"
Write-Host "${GREEN}═══════════════════════════════════════════════════════${NC}"
