---
name: birthday-reminder
description: Manage birthdays and important dates in natural language. Get reminders automatically. Fully local.
version: 1.0.0
metadata:
  openclaw:
    requires: {}
---

# Birthday Reminder

Track birthdays and important dates in plain text.
Automatic reminders via the morning briefing.
No external service, no account needed.

## Usage

```
Remember John's birthday is March 15
Add birthday: Mom — June 3
Who has a birthday this month?
Any birthdays coming up this week?
How old is Sarah turning this year?
List all birthdays
```

## Storage

File: `~/.greenchclaw/workspace/memory/birthdays.md`

## File format

```markdown
# Birthdays & Important Dates

## Birthdays
- John Smith | 1985-03-15 | Friend
- Mom | 1955-06-03 | Family
- Sarah | 1990-09-22 | Colleague

## Anniversaries
- Wedding anniversary | 2015-07-14

## Other dates
- Tax deadline | every year: 04-30
```

## Commands

**Add birthday:**
Parse natural language date, append to birthdays.md.
Confirm: `🎂 Added: {name} — {date}`

**Check upcoming (next 14 days):**
Compare today's date with MM-DD of each entry.
Show name, date, days until, and age if birth year known.

**Check this month:**
Filter entries where month == current month.

**Morning briefing integration:**
The morning-briefing skill reads birthdays.md automatically.
If anyone has a birthday today or within 3 days, it shows:
`🎂 Upcoming: John's birthday in 2 days (March 15)`

## Output format

```
🎂 Upcoming birthdays:

Today:
  🎉 It's John's birthday! (turning 41) — wish them well!

This week:
  • Mom — June 3 (in 4 days, turning 71)

This month:
  • Sarah — June 22 (in 23 days, turning 36)
```

When it's someone's birthday today, always mention it proactively at the start of the session.
