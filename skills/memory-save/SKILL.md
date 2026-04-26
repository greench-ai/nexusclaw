# memory-save — Session Memory Consolidation
> Runs automatically every 30 minutes via NexusClaw cron.

## What This Skill Does

Saves and consolidates the current session's context into persistent memory files.
Prevents context loss between sessions and builds a long-term knowledge base.

## Automatic Trigger

Every 30 minutes via cron:
```json
{ "schedule": "*/30 * * * *", "skill": "memory-save/run" }
```

## Manual Trigger

```
Run memory-save/run
```

## What Gets Saved

| Category | Content | Location |
|----------|---------|----------|
| Session summary | Compressed summary of conversation so far | `memory/sessions/YYYY-MM-DD-HH.md` |
| Key facts | Entities, decisions, preferences mentioned | `memory/facts/` |
| Tasks | Pending/completed tasks mentioned | `memory/tasks/` |
| Code/files | References to files or code discussed | `memory/artifacts/` |

## Save Process

When triggered, you will:

1. **Summarize** the current session since the last save point
   - Keep it dense — facts over narrative
   - Max 500 words
2. **Extract** any new facts, decisions, or entities worth remembering long-term
3. **Write** session summary to `memory/sessions/[timestamp].md`
4. **Append** key facts to `memory/facts/index.md`
5. **Update** task list in `memory/tasks/active.md` if tasks were discussed
6. **Log** the save event: `memory/save-log.md`

## Memory File Format

```markdown
# Session Memory — 2025-01-15 14:30

## Summary
[Dense summary of conversation]

## Key Facts
- [fact 1]
- [fact 2]

## Decisions Made
- [decision 1]

## Open Tasks
- [ ] [task 1]
```

## Notes

- Be concise. These files accumulate. Dense > verbose.
- Never save sensitive credentials or API keys.
- If nothing significant happened since last save, log a one-liner and exit.
