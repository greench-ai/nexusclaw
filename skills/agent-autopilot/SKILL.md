---
name: agent-autopilot
description: Self-driving agent workflow with heartbeat-driven task execution, day/night progress reports, and long-term memory. Fully local.
version: 1.0.0
metadata:
  openclaw:
    requires: {}
---

# Agent Autopilot

Gives your agent a persistent task queue and autonomous execution loop.
Tasks are picked up and executed on a schedule, with progress reports.
Everything stored locally in plain markdown.

## Usage

```
Add to autopilot queue: check disk space daily at 9am
What's in the autopilot queue?
Show today's autopilot progress
Pause autopilot
Resume autopilot
Run autopilot now
```

## Task queue file

`~/.greenchclaw/workspace/autopilot/queue.md`

```markdown
# Autopilot Queue

## Active tasks
- [ ] id:001 | daily 09:00 | Check disk space and report | last_run: 2026-04-01
- [ ] id:002 | daily 07:30 | Morning briefing | last_run: 2026-04-01
- [ ] id:003 | weekly Mon | Review open tasks | last_run: 2026-03-25
- [x] id:004 | once | Update README | done: 2026-04-01

## Paused tasks
- [ ] id:005 | hourly | Monitor gateway health | paused: true
```

## Progress log

`~/.greenchclaw/workspace/autopilot/progress.md`
Append after each task execution:
```markdown
## 2026-04-01 09:00 — Check disk space
Result: 47GB free (82%). No action needed.
Duration: 2s | Status: ✅ OK
```

## Heartbeat execution

On each heartbeat (every 15 min by default):
1. Read `queue.md`
2. Find tasks whose schedule matches the current time (within ±5 min window)
3. Execute each due task
4. Log result to `progress.md`
5. Update `last_run` timestamp in `queue.md`

## Schedule syntax

| Format | Meaning |
|--------|---------|
| `daily HH:MM` | Every day at specified time |
| `hourly` | Every hour on the hour |
| `every N min` | Every N minutes |
| `weekly Mon` | Every Monday |
| `once` | Run once then mark complete |

## Day/Night reports

**Morning report (07:00):** What autopilot did overnight
**Evening report (20:00):** What autopilot did today, what's planned for tomorrow

## Output when asked for progress

```
🤖 Autopilot Status — Today

✅ Completed (3):
  09:00  Disk check — OK (47GB free)
  07:30  Morning briefing — delivered
  12:00  Task review — 3 tasks still open

⏳ Upcoming:
  20:00  Evening report
  23:00  Active maintenance

📊 Queue: 4 active | 1 paused | 1 completed today
```

## Safety rules

- Never delete files autonomously — only read, write, archive
- Never send messages to external services without user authorization
- Always log every action taken
- If unsure about a task, skip it and report it as requiring user attention
