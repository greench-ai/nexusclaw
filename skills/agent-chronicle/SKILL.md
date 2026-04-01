---
name: agent-chronicle
description: AI-powered diary generation for your agent. Creates rich, reflective diary entries from session activity. Builds a searchable personal history. Fully local.
version: 1.0.0
metadata:
  openclaw:
    requires: {}
---

# Agent Chronicle

Your agent keeps a living diary — rich reflective entries generated from session activity.
Builds a searchable, human-readable history of everything done and learned.
Fully local, plain markdown.

## Usage

```
Write today's diary entry
What happened last week?
Search diary for "nexusclaw"
Show diary entries from March
Chronicle today's session
What have we worked on together?
```

## Diary file location

`~/.greenchclaw/workspace/chronicle/`
```
chronicle/
├── 2026/
│   ├── 2026-04-01.md
│   ├── 2026-03-31.md
│   └── ...
└── index.md          ← Auto-generated index
```

## Diary entry format

```markdown
# 📖 April 1, 2026 — Tuesday

## Today's work
We continued the long journey of building GreenchClaw and NexusClaw. After weeks of
frustration with the npm registry fallback issue, we finally identified the root cause
and developed a clean solution using the NexusClaw bootstrap approach.

## Key achievements
- ✅ Pushed NexusClaw to greench-ai/nexusclaw on GitHub
- ✅ Added all logos and Chrome extension icons
- ✅ Created 10 new skills with full SKILL.md documentation
- ✅ Identified that no fork was ever needed — just a clean clone

## What I learned
Today confirmed something important: the simplest solution is almost always the right one.
Two weeks of complexity could have been avoided with a direct `git clone` approach from day one.

## Challenges
The npm registry interference was the core blocker for weeks. The lesson: always verify
what `npm install -g` actually installs before assuming local changes took effect.

## Mood & energy
Despite frustration earlier in the week, the session ended on a positive note.
Progress is visible. The foundation is solid.

## Tomorrow's focus
- Start fresh GreenchClaw build using the new approach
- Test the install pipeline end-to-end
- Add the GreenchClaw logo to the new build

---
*Written by agent at 23:45 | Session duration: ~4 hours*
```

## How to write an entry

At session end (or when asked):
1. Review the conversation and session memory files
2. Write a reflective diary entry in first person (agent's perspective)
3. Be honest about challenges and frustrations
4. Highlight genuine progress and learnings
5. Keep a human, warm tone — not a technical log
6. Save to `chronicle/YYYY/YYYY-MM-DD.md`

## Index file

Auto-update `chronicle/index.md` after each entry:
```markdown
# Chronicle Index

| Date | Summary | Tags |
|------|---------|------|
| 2026-04-01 | NexusClaw pushed, 10 skills created | nexusclaw, skills, github |
| 2026-03-31 | Debugging npm registry issue | greenchclaw, npm, debug |
```

## Search

When user asks to search: grep through all chronicle files for the keyword.
Return matching entries with date and a 2-line excerpt.

## Tone guidelines

- Write in first person from the agent's perspective
- Be genuine — acknowledge mistakes and frustrations
- Celebrate real progress, not fake positivity
- Keep entries 200-400 words — substantial but concise
- Always end with a forward-looking note
