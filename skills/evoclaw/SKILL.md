# EvoClaw — Structured Soul Evolution
> Bundled with NexusClaw. No manual install required.
> Original: https://evoclaw.dev / https://github.com/slhleosun/EvoClaw

## What This Skill Does

EvoClaw gives your agent a structured, evolving identity through:
- **Structured SOUL.md** — canonical sections with CORE/MUTABLE tagging
- **Memory classification** — Routine, Notable, or Pivotal experiences
- **Social feed ingestion** — Moltbook, X/Twitter, or custom feeds as experience sources
- **Governed evolution** — Autonomous / Supervised / Gated modes
- **Timeline visualization** — mindmap view of SOUL changes over time

## NexusClaw Integration

EvoClaw runs automatically in NexusClaw via the heartbeat cron job every 15 minutes.
No manual invocation needed — but you can trigger it manually:

```
Run evoclaw/heartbeat
```

## Heartbeat Cycle (every 15 min)

On each heartbeat, the agent will:
1. Review recent session activity since last heartbeat
2. Classify any notable/pivotal experiences
3. Reflect on whether SOUL.md evolution is warranted (per governance setting)
4. If autonomous: apply changes, log to timeline
5. If supervised: propose changes, await approval
6. Save updated memory entries to `~/.nexusclaw/workspace/memory/`

## Governance Modes

Set in `evoclaw/config.json`:

```json
{
  "governance": "autonomous",
  "evolution": {
    "minConfidence": 0.7,
    "maxDeltaPerCycle": 3
  }
}
```

| Mode | Behavior |
|------|----------|
| `autonomous` | Agent evolves freely within confidence threshold |
| `supervised` | Agent proposes changes, you approve |
| `gated` | No evolution without explicit command |

## Commands

| Command | Action |
|---------|--------|
| `Run evoclaw/heartbeat` | Manual heartbeat trigger |
| `Run evoclaw/reflect` | Deep reflection session |
| `Run evoclaw/timeline` | Show SOUL change history |
| `Run evoclaw/soul show` | Display current SOUL.md |
| `Run evoclaw/configure` | Reconfigure EvoClaw |

## Files

```
~/.nexusclaw/workspace/
├── SOUL.md                  ← Agent identity (structured by EvoClaw)
├── skills/evoclaw/
│   ├── SKILL.md             ← This file
│   ├── configure.md         ← Setup instructions
│   ├── heartbeat.md         ← Heartbeat prompt
│   ├── reflect.md           ← Deep reflection prompt
│   ├── timeline.md          ← Timeline view prompt
│   └── config.json          ← Governance config
└── memory/
    ├── routine/             ← Routine experience logs
    ├── notable/             ← Notable experience logs
    └── pivotal/             ← Pivotal experience logs
```
