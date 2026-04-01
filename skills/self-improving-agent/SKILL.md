---
name: self-improving-agent
description: Continuously improve by logging errors, learnings, and preferences into memory. Gets smarter over time without any API key.
version: 1.0.0
metadata:
  openclaw:
    requires: {}
---

# Self-Improving Agent

Capture learnings, correct errors, and build a personalized preference profile over time.
Everything stored locally in your workspace. No external service needed.

## What it does

After each session or task, this skill:
1. Logs what worked and what didn't
2. Records user preferences and corrections
3. Builds a growing `LEARNINGS.md` file
4. Surfaces relevant past learnings at the start of new sessions

## Usage

```
Remember that I prefer metric units
Log that the last approach didn't work — use X instead next time
What have you learned about my preferences?
Review your learnings from this session
```

## How it works

**Log a learning:**
Append to `~/.greenchclaw/workspace/memory/learnings/YYYY-MM.md`:
```markdown
## {date}
**Context:** {what was happening}
**Learning:** {what to do differently}
**Preference:** {user preference if applicable}
```

**Log an error correction:**
Append to `~/.greenchclaw/workspace/memory/corrections/YYYY-MM.md`:
```markdown
## {date}
**I did:** {what I did}
**User corrected:** {what they said}
**Rule:** {derived rule for future}
```

**Session review (run at end of session):**
1. Review conversation for: corrections, stated preferences, repeated patterns
2. Extract 3-5 key learnings
3. Append to learnings file
4. Update `PREFERENCES.md` with any new preferences

**Load context (run at start of session):**
Read the last 30 days of learnings and surface the 5 most relevant ones given the current task.

## Files

```
~/.greenchclaw/workspace/memory/
├── learnings/
│   └── YYYY-MM.md         ← Monthly learning logs
├── corrections/
│   └── YYYY-MM.md         ← Error corrections
└── PREFERENCES.md          ← Master preferences file
```

## Preferences file format

```markdown
# My Preferences

## Communication
- Prefer concise responses unless I ask for detail
- Use metric units (°C, km, kg)
- Don't use emojis unless I use them first

## Technical
- Prefer Python over JavaScript for scripts
- Always show the command before running it

## Work style
- ...
```

Always read PREFERENCES.md at session start if it exists.
