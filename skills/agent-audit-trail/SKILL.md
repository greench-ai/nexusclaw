---
name: agent-audit-trail
description: Tamper-evident audit logging for all agent actions. Hash-chained entries, fully local. Know exactly what your agent did and when.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - sha256sum
---

# Agent Audit Trail

Keeps a tamper-evident log of every significant action the agent takes.
Each entry is hash-chained — any tampering is detectable.
Fully local, no external service.

## What gets logged

- File reads/writes
- Commands executed
- Configurations changed
- Skills invoked
- External API calls made
- Memory updates

## Usage

```
Show me the audit log
What did you do in the last hour?
Audit log for today
Verify audit log integrity
Show all file operations today
```

## Log file

Stored at: `~/.greenchclaw/workspace/audit/audit.log`

## Log entry format

```
{timestamp}|{action_type}|{description}|{prev_hash}|{entry_hash}
```

Example:
```
2026-04-01T08:30:00Z|FILE_READ|Read ~/.greenchclaw/greenchclaw.json|a3f2b1...|7c9d4e...
2026-04-01T08:30:05Z|SKILL_INVOKE|Invoked weather skill for Luxembourg|7c9d4e...|2b8f1a...
2026-04-01T08:31:00Z|CONFIG_CHANGE|Updated gateway.port to 50420|2b8f1a...|9e3c7b...
```

## How to log an action

Before any significant action:
1. Read the last line of `audit.log` to get `prev_hash`
2. Create entry: `{timestamp}|{action_type}|{description}|{prev_hash}`
3. Compute SHA256 of the entry
4. Append: `{entry}|{hash}`

## Action types

| Type | When to use |
|------|-------------|
| `FILE_READ` | Reading a file |
| `FILE_WRITE` | Writing or modifying a file |
| `FILE_DELETE` | Deleting a file |
| `CMD_EXEC` | Running a shell command |
| `SKILL_INVOKE` | Calling another skill |
| `CONFIG_CHANGE` | Modifying configuration |
| `API_CALL` | Making an external HTTP request |
| `MEMORY_UPDATE` | Writing to memory files |
| `SESSION_START` | Beginning of a new session |
| `SESSION_END` | End of a session |

## Integrity verification

To verify the chain hasn't been tampered with:
Read each line, recompute the hash of `{timestamp}|{action_type}|{description}|{prev_hash}`, compare with stored hash.
Report any mismatches.

## Daily summary

Each day, append a summary entry:
```
{date}|DAILY_SUMMARY|{N} actions: {breakdown by type}|{prev_hash}|{hash}
```

## Output when showing log

```
🔐 Audit Log — Today (April 1, 2026)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
08:30  📂 Read config file
08:30  🔧 Invoked: weather skill
08:31  ⚙️  Config changed: gateway.port → 50420
08:45  📝 Memory updated: added session note
09:00  🌐 API call: wttr.in (weather)

✅ Chain integrity: Valid (5 entries verified)
```
