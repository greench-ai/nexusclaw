---
name: morning-briefing
description: Daily morning digest — weather, tasks, session summary, and day plan. Fully local, no API key needed.
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins:
        - curl
---

# Morning Briefing

Start every day with a personalized briefing assembled from your local data.
Runs automatically or on demand. No external accounts needed.

## Usage

```
Good morning
Morning briefing
What's my day looking like?
Daily briefing
```

## Trigger words

Activate when user says: "good morning", "morning", "morning briefing", "start my day", "what's today look like", "daily briefing".

## Briefing components

Build the briefing in this order:

### 1. Date & Time
```
📅 {Day}, {Date} — {Time} | {Timezone}
```

### 2. Weather (if location set)
Use the `weather` skill to get current conditions for the user's city.
One line: `🌤️ {City}: {temp}°C, {description}`

### 3. Open Tasks
Read `~/.greenchclaw/workspace/memory/tasks/active.md` if it exists.
Show tasks marked `[ ]` (incomplete). Max 5, sorted by priority.
```
📋 Open tasks:
  • [HIGH] {task}
  • [MED]  {task}
```

### 4. Yesterday's summary
Read most recent session memory file from `~/.greenchclaw/workspace/memory/sessions/`
One sentence: what was accomplished.

### 5. Day suggestion
Based on open tasks and day of week, suggest one focus for the day.
```
🎯 Suggested focus: {one thing}
```

### 6. Quote of the day (optional)
Pick one motivational quote from the list below. Rotate daily based on day-of-year mod 10.

**Quotes:**
1. "The secret of getting ahead is getting started." — Mark Twain
2. "Done is better than perfect." — Sheryl Sandberg
3. "Focus on being productive instead of busy." — Tim Ferriss
4. "The best time to plant a tree was 20 years ago. The second best time is now."
5. "You don't have to be great to start, but you have to start to be great."
6. "Small steps every day."
7. "Build something you're proud of."
8. "Every expert was once a beginner."
9. "The journey of a thousand miles begins with one step." — Lao Tzu
10. "Make it work, make it right, make it fast." — Kent Beck

## Output format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌿 Good morning! Here's your briefing:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Tuesday, April 1, 2026 — 08:30 | Europe/Luxembourg

🌤️ Luxembourg: 14°C, Partly cloudy

📋 Open tasks (3):
  • Build the NexusClaw install pipeline
  • Fix the logos on GreenchClaw
  • Write documentation

📝 Yesterday: Pushed NexusClaw to GitHub, added logos and Chrome extension icons.

🎯 Focus today: Complete the install pipeline

💡 "Done is better than perfect." — Sheryl Sandberg

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
