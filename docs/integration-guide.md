# NexusClaw — Integration Guide
> How to apply this bootstrap to a fresh OpenClaw fork.

---

## Step 1 — Fork OpenClaw

```bash
# On GitHub: fork https://github.com/openclaw/openclaw → github.com/greench/nexusclaw
# Then clone locally:
git clone https://github.com/greench/nexusclaw.git
cd nexusclaw
```

---

## Step 2 — Apply Rebrand

```bash
# Run the mass rename script
bash scripts/rebrand.sh

# Manually verify the result:
grep -r "OpenClaw\|openclaw" src/ apps/ packages/ \
  --include="*.ts" --include="*.svelte" --include="*.json" \
  | grep -v node_modules | grep -v .git
```

---

## Step 3 — Copy Bootstrap Files

Copy everything from this `nexusclaw-bootstrap/` package into your fork root:

```bash
# From nexusclaw-bootstrap/:
cp README.md             ../nexusclaw/
cp package.json          ../nexusclaw/        # merge carefully — don't overwrite all keys
cp Dockerfile            ../nexusclaw/
cp docker-compose.yml    ../nexusclaw/
cp install.sh            ../nexusclaw/
cp .env.example          ../nexusclaw/
cp -r skills/            ../nexusclaw/skills/
cp -r ui/themes/         ../nexusclaw/apps/ui/src/lib/themes/
cp ui/ClaudePreview.svelte ../nexusclaw/apps/ui/src/lib/components/
cp -r extensions/        ../nexusclaw/extensions/
cp -r .github/           ../nexusclaw/.github/
cp config/nexusclaw.json ../nexusclaw/config/
```

---

## Step 4 — Mount UI Components

### Theme Switcher

In your header component (e.g. `apps/ui/src/lib/components/Header.svelte`):

```svelte
<script>
  import { ThemeSwitcher } from '$lib/themes/switcher';
  import { onMount } from 'svelte';
  onMount(() => ThemeSwitcher.init());
</script>

<!-- Add to header -->
<div id="theme-switcher"></div>

<!-- Mount in onMount -->
<script>
  onMount(() => {
    ThemeSwitcher.init();
    ThemeSwitcher.mount('#theme-switcher');
  });
</script>
```

In your global CSS (`app.css`):

```css
@import '$lib/themes/themes.css';
```

### Claude Preview Window

In your main chat layout (`apps/ui/src/routes/+layout.svelte` or similar):

```svelte
<script>
  import ClaudePreview from '$lib/components/ClaudePreview.svelte';
</script>

<!-- Add to chat layout alongside message thread -->
<div class="chat-layout">
  <div class="message-thread">
    <slot />
  </div>
  <div class="preview-panel">
    <ClaudePreview gatewayWsUrl="ws://localhost:19789/ws" />
  </div>
</div>
```

---

## Step 5 — Install Bundled Skills

The bundled skills need to be in place before the daemon starts:

```bash
# The install.sh script does this automatically.
# To do it manually:
mkdir -p ~/.nexusclaw/workspace/skills
cp -r skills/* ~/.nexusclaw/workspace/skills/
```

---

## Step 6 — Set Default Config

```bash
mkdir -p ~/.nexusclaw
cp config/nexusclaw.json ~/.nexusclaw/nexusclaw.json
# Edit with your API keys and preferences
```

---

## Step 7 — Build & Run

```bash
pnpm install
pnpm ui:build
pnpm build

# Native run
nexusclaw gateway

# Or with daemon
nexusclaw onboard --install-daemon
```

---

## Step 8 — Chrome Extension

```
1. Open chrome://extensions
2. Enable Developer Mode (top right)
3. Click "Load unpacked"
4. Select: extensions/chrome/
5. Extension appears in toolbar
6. Click it and set gateway URL: http://localhost:19789
```

---

## Step 9 — Verify Cron Jobs

Start the gateway and check cron is firing:

```bash
nexusclaw gateway --verbose

# After 15 minutes, you should see:
# [cron] Running: evoclaw/heartbeat
# After 30 minutes:
# [cron] Running: memory-save/run
# After 1 hour:
# [cron] Running: library-update/run
```

---

## Keeping Up with OpenClaw Upstream

```bash
# Add upstream remote once
git remote add upstream https://github.com/openclaw/openclaw.git

# Periodically merge upstream changes
git fetch upstream
git merge upstream/main --no-edit

# Resolve any conflicts, then rebuild
pnpm install && pnpm ui:build && pnpm build
```

---

## Directory Reference

```
~/.nexusclaw/
├── nexusclaw.json           ← Main config
├── workspace/
│   ├── SOUL.md              ← Agent identity (managed by EvoClaw)
│   ├── AGENTS.md            ← Agent instructions
│   ├── memory/              ← Memory files
│   │   ├── routine/
│   │   ├── notable/
│   │   └── pivotal/
│   └── skills/              ← All bundled + custom skills
│       ├── evoclaw/
│       ├── memory-save/
│       ├── library-update/
│       ├── image-create/
│       └── web-search/
├── credentials/             ← Channel auth (WhatsApp etc.)
└── logs/

~/nexusclaw/
└── library/                 ← Auto-maintained documentation
    ├── README.md
    ├── system/
    ├── sessions/
    ├── memory/
    ├── agents/
    └── skills/
```
