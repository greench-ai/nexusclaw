#!/usr/bin/env bash
# NexusClaw — Rebrand Script
# Run from the root of your openclaw fork after cloning.
# Performs all string replacements to rename openclaw → nexusclaw.

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${CYAN}[rebrand]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# ── Sanity check ──────────────────────────────────────────────────────────────
if [ ! -f "package.json" ]; then
  fail "Run this from the root of your openclaw fork."
fi

if ! grep -q '"openclaw"' package.json 2>/dev/null; then
  fail "This doesn't look like an OpenClaw fork (no 'openclaw' in package.json)."
fi

log "Starting OpenClaw → NexusClaw rebrand..."
log "Creating backup branch..."
git checkout -b pre-rebrand-backup 2>/dev/null || true
git checkout - 2>/dev/null || true

# ── Directories to process ───────────────────────────────────────────────────
DIRS="src apps packages scripts"
EXTS="ts tsx js jsx svelte html json sh md yaml yml toml"

build_ext_pattern() {
  local pattern=""
  for ext in $EXTS; do
    [ -n "$pattern" ] && pattern="$pattern,"
    pattern="${pattern}*.${ext}"
  done
  echo "$pattern"
}

INCLUDE_PATTERN=$(build_ext_pattern)

do_replace() {
  local from="$1"
  local to="$2"
  log "Replacing: '$from' → '$to'"
  for dir in $DIRS; do
    [ -d "$dir" ] || continue
    find "$dir" -type f \( \
      -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
      -o -name "*.svelte" -o -name "*.html" -o -name "*.json" \
      -o -name "*.sh" -o -name "*.md" -o -name "*.yaml" \
      -o -name "*.yml" -o -name "*.toml" \
    \) ! -path "*/node_modules/*" ! -path "*/.git/*" \
    | xargs sed -i "s|${from}|${to}|g" 2>/dev/null || true
  done
}

# ── String replacements (order matters) ──────────────────────────────────────
do_replace "OpenClaw"     "NexusClaw"
do_replace "openclaw"     "nexusclaw"
do_replace "OPENCLAW"     "NEXUSCLAW"
do_replace "open-claw"    "nexus-claw"
do_replace "openclaw\.ai" "nexusclaw.local"

# ── Config paths ──────────────────────────────────────────────────────────────
do_replace '\.openclaw/'  '.nexusclaw/'
do_replace '"\.openclaw"' '".nexusclaw"'

# ── Rename files ──────────────────────────────────────────────────────────────
log "Renaming files..."

[ -f "openclaw.mjs" ]         && git mv openclaw.mjs nexusclaw.mjs && ok "openclaw.mjs → nexusclaw.mjs"
[ -f "openclaw.podman.env" ]  && git mv openclaw.podman.env nexusclaw.podman.env && ok "openclaw.podman.env → nexusclaw.podman.env"

# ── Root files ────────────────────────────────────────────────────────────────
log "Patching root files..."
[ -f "package.json" ]   && sed -i 's/"openclaw"/"nexusclaw"/g; s|openclaw/openclaw|greench/nexusclaw|g' package.json
[ -f "pyproject.toml" ] && sed -i 's/openclaw/nexusclaw/g' pyproject.toml

# ── Verify ────────────────────────────────────────────────────────────────────
log "Verifying..."
REMAINING=$(grep -r "OpenClaw\|openclaw\|OPENCLAW" \
  src/ apps/ packages/ scripts/ \
  --include="*.ts" --include="*.js" --include="*.svelte" \
  --include="*.html" --include="*.json" --include="*.sh" \
  2>/dev/null | grep -v node_modules | grep -v ".git" | wc -l || echo 0)

echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  Rebrand complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
if [ "$REMAINING" -gt 0 ]; then
  echo -e "${RED}  Warning: $REMAINING references to 'openclaw' still remain.${NC}"
  echo "  Run this to find them:"
  echo "  grep -r 'OpenClaw\\|openclaw' src/ apps/ packages/ --include='*.ts'"
else
  ok "No remaining openclaw references found."
fi
echo ""
echo "Next step: copy bootstrap files — see docs/integration-guide.md"
