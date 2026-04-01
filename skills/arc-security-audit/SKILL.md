---
name: arc-security-audit
description: Comprehensive security audit for your agent's full skill stack. Checks for unsafe permissions, credential exposure, network calls, and suspicious behavior. Fully local.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - grep
        - find
---

# Arc Security Audit

Audits your entire skill stack for security issues before they become problems.
Checks permissions, credential handling, network calls, and suspicious patterns.
Fully local — no external scanning service.

## Usage

```
Run security audit
Audit my skills
Check for security issues
Is my setup secure?
Audit skill: evoclaw
Security check
```

## What gets audited

### 1. Credential exposure scan
Search all skill files for hardcoded credentials:
```bash
grep -r "sk-\|api_key\|API_KEY\|password\|secret\|token\|private_key" \
  ~/.greenchclaw/workspace/skills/ \
  --include="*.md" --include="*.json" --include="*.sh" \
  | grep -v "YOUR_\|example\|placeholder\|\${" \
  | grep -v ".git"
```
Flag any real-looking credentials.

### 2. Network permission audit
Find skills that make outbound requests:
```bash
grep -r "curl\|fetch\|http\|https\|wget\|axios" \
  ~/.greenchclaw/workspace/skills/ \
  --include="*.md" | grep -v "localhost\|127.0.0.1"
```
List all external domains contacted. Flag any unexpected ones.

### 3. File system access audit
Find skills that access sensitive paths:
```bash
grep -r "\.ssh\|\.gnupg\|\.aws\|\.kube\|/etc/passwd\|/etc/shadow" \
  ~/.greenchclaw/workspace/skills/ --include="*.md"
```

### 4. Shell execution audit
Find skills that execute shell commands:
```bash
grep -r "exec\|eval\|system\|subprocess\|os\.popen\|child_process" \
  ~/.greenchclaw/workspace/skills/ --include="*.md"
```
Review each one — shell execution is high risk.

### 5. Skill metadata validation
For each skill, check:
- Has a valid `name` in frontmatter
- Has a `description`
- Declares all required `bins` and `env` vars
- No metadata mismatch between what's declared and what's done

### 6. Config file audit
Check `~/.greenchclaw/greenchclaw.json`:
- No hardcoded API keys (should use env vars)
- Port binding (loopback only, not 0.0.0.0)
- Sandbox mode appropriately set

### 7. Permissions check
```bash
ls -la ~/.greenchclaw/
ls -la ~/.greenchclaw/workspace/skills/
```
Skills directory should be 755, config files 600.

## Risk levels

| Level | Meaning |
|-------|---------|
| 🔴 CRITICAL | Immediate action required (hardcoded credentials, remote code execution) |
| 🟠 HIGH | Should be fixed soon (excessive permissions, suspicious network calls) |
| 🟡 MED | Worth reviewing (undeclared network access, broad file access) |
| 🟢 LOW | Minor issues (missing metadata, deprecated patterns) |
| ✅ OK | No issues found |

## Audit report format

```
🔐 Security Audit Report — April 1, 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scanned: 54 skills | 3 config files | 2 credential stores

🔴 CRITICAL (0): None ✅
🟠 HIGH (0): None ✅  
🟡 MED (2):
  • skill "image-create": makes calls to 192.168.178.76:8188 (expected — ComfyUI)
  • config: sandbox.mode = "off" — consider enabling for untrusted skills
🟢 LOW (1):
  • skill "blucli": missing version in frontmatter

✅ Overall: SECURE
No credentials exposed. No suspicious network activity.

Audit took: 1.2s
Next scheduled audit: 2026-04-08
```

## Auto-fix (safe fixes only)

For LOW issues only, offer to auto-fix:
- Add missing frontmatter fields
- Fix file permissions
- Never auto-fix MED or higher
