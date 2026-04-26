# library-update — Living Documentation System
> Runs automatically every hour via NexusClaw cron.
> Maintains ~/nexusclaw/library/ as a self-updating knowledge base.

## What This Skill Does

Keeps a structured, always-current documentation library of:
- System configuration and state
- Skills installed and their status
- Session activity logs
- Agent capabilities and learned behaviors
- Cron job history and health

## Automatic Trigger

Every hour via cron:
```json
{ "schedule": "0 * * * *", "skill": "library-update/run" }
```

## Manual Trigger

```
Run library-update/run
```

## Library Structure

```
~/nexusclaw/library/
├── README.md                    ← Auto-generated index
├── system/
│   ├── config.md                ← Current gateway config summary
│   ├── skills.md                ← Installed skills + status
│   ├── cron-history.md          ← Cron job run history
│   └── health.md                ← Last health check
├── sessions/
│   ├── index.md                 ← Session log index
│   └── YYYY-MM-DD/              ← Daily session folders
├── memory/
│   ├── facts/                   ← Persistent fact store
│   ├── tasks/                   ← Task tracking
│   └── sessions/                ← Session summaries
├── agents/
│   ├── SOUL.md                  ← Copy of current SOUL.md
│   └── evolution-log.md         ← EvoClaw timeline summary
└── skills/
    └── [skill-name]/            ← Per-skill activity logs
```

## Update Process

When triggered, the agent will:

1. **Check** which library files are stale (not updated in >1h)
2. **Update** `system/config.md` with current gateway state
3. **Update** `system/skills.md` — list all skills, last-run time, status
4. **Append** to `system/cron-history.md` — log this run
5. **Sync** `agents/SOUL.md` if EvoClaw has made changes
6. **Regenerate** `README.md` index with timestamps
7. **Prune** old session logs (>30 days, configurable)

## Config

Set in `skills/library-update/config.json`:

```json
{
  "libraryPath": "~/nexusclaw/library",
  "sessionRetentionDays": 30,
  "pruneEnabled": true,
  "verbosity": "normal"
}
```

## Notes

- This skill is additive — it never deletes content unless pruning is enabled
- All generated files are plain Markdown — readable without NexusClaw
- The library is designed to be committed to a private git repo for version history
