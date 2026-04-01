---
name: todo-tracker
description: Manage tasks, to-dos, and projects with priorities and deadlines. Fully local markdown files, no API needed.
version: 1.0.0
metadata:
  openclaw:
    requires: {}
---

# Todo Tracker

Manage your tasks in plain Markdown files stored locally.
No external service, no account, no API key.

## Usage

```
Add task: Fix the login bug [HIGH]
What are my open tasks?
Mark "Fix login bug" as done
Show completed tasks from this week
Add reminder: Call client tomorrow at 3pm
What's due today?
```

## Task file location

All tasks stored in: `~/.greenchclaw/workspace/memory/tasks/`

```
tasks/
├── active.md      ← All open tasks
├── done.md        ← Completed tasks (append-only)
└── projects/
    └── {name}.md  ← Per-project task lists
```

## Task format

```markdown
- [ ] [HIGH] Fix the login bug — due: 2026-04-05 — added: 2026-04-01
- [ ] [MED]  Write documentation — due: none — added: 2026-04-01
- [x] [LOW]  Update README — done: 2026-04-01
```

Priority levels: `[HIGH]`, `[MED]`, `[LOW]`, `[SOMEDAY]`

## Commands

**Add task:**
Append to `active.md`:
`- [ ] [{PRIORITY}] {task} — due: {due_date or "none"} — added: {today}`

**Complete task:**
1. Find task in `active.md`, change `[ ]` to `[x]`
2. Move line to `done.md` with `— done: {today}`

**List tasks:**
Read `active.md`, filter by `[ ]`, sort by priority (HIGH first).

**Due today:**
Filter tasks where `due: {today's date}`.

**Overdue:**
Filter tasks where due date < today and status is `[ ]`.

## Output format

```
📋 Your tasks:

🔴 HIGH
  • Fix the login bug (due: Apr 5)

🟡 MED
  • Write documentation
  • Review pull requests (due: Apr 3)

🟢 LOW
  • Update README

📊 3 open | 12 completed this week
```

When adding a task, confirm: `✅ Added: "{task}" [{priority}]`
When completing, confirm: `✅ Marked done: "{task}"`
