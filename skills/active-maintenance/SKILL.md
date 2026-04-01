---
name: active-maintenance
description: Automated system health monitoring and memory metabolism for your agent. Keeps your installation clean, fast, and healthy. No API key needed.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - df
        - free
---

# Active Maintenance

Keeps your agent installation healthy automatically.
Monitors system resources, cleans old memory files, and reports on agent health.
Fully local — no external service.

## Usage

```
Run maintenance
Check system health
How is the agent doing?
Clean up old memory files
How much disk space is left?
Agent health report
```

## Health checks

### 1. Disk space
`df -h ~/.greenchclaw/` — warn if <10% free, critical if <5%

### 2. Memory usage
`free -h` — report available RAM

### 3. Memory file size
Check total size of `~/.greenchclaw/workspace/memory/`
Warn if >500MB. Suggest pruning sessions older than 90 days.

### 4. Skills inventory
List all installed skills and their last-used date.
Flag skills that haven't been used in 30+ days.

### 5. Log file size
Check `~/.greenchclaw/workspace/` for oversized log files (>50MB).

### 6. Audit trail integrity
Verify the audit log chain if agent-audit-trail is installed.

### 7. Gateway status
Check if the gateway process is running and responsive.

## Maintenance tasks

**Prune old sessions (auto, safe):**
Archive session memory files older than 90 days to `memory/archive/`
Never delete — only archive.

**Compress audit logs:**
If audit.log >10MB, archive to `audit/archive/YYYY-MM.log.gz`

**Clean temp files:**
Remove any `*.tmp` files in the workspace older than 24 hours.

**Update skills index:**
Regenerate `~/.greenchclaw/workspace/skills-index.md` listing all skills + descriptions.

## Health report format

```
🔧 Agent Health Report — April 1, 2026 08:30
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💾 Disk:      47 GB free (82%) ✅
🧠 RAM:       8.2 GB free ✅
📁 Memory:    124 MB (workspace) ✅
📋 Skills:    54 installed, all healthy ✅
📊 Audit log: 2.3 MB, chain valid ✅
🌐 Gateway:   Running on :50420 ✅

⚠️  Warnings:
  • 12 session files older than 90 days (consider archiving)
  • skill "bluebubbles" not used in 45 days

✅ No critical issues found.
Last maintenance: 2026-03-31 23:00
```

## Schedule

Recommended: run via cron every 24 hours.
Add to config:
```json
{
  "schedule": "0 3 * * *",
  "skill": "active-maintenance/run",
  "description": "Nightly system health check and cleanup"
}
```
