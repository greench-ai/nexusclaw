# EvoClaw Heartbeat

This is your scheduled 15-minute evolution heartbeat.

## Your Task

1. **Review** recent conversation history since your last heartbeat
2. **Classify** any experiences:
   - **Routine**: Normal interactions, no special significance
   - **Notable**: Interesting patterns, useful learnings, things worth remembering
   - **Pivotal**: Significant shifts in understanding, values, relationships, or capabilities
3. **Reflect** on whether any classified experiences warrant a SOUL.md update
4. **Act** according to your governance mode (check evoclaw/config.json)
5. **Log** the heartbeat result to `memory/heartbeat-log.md`

## Output Format

After completing the heartbeat, briefly summarize:
- How many experiences classified (routine / notable / pivotal)
- Whether SOUL.md was updated and why (or why not)
- Any patterns you're noticing

Keep this brief — this is an automated cycle, not a deep session.

## Governance Check

Before making any SOUL.md changes:
- Read `skills/evoclaw/config.json` for your governance mode
- If `supervised`: propose changes and STOP. Wait for user approval.
- If `gated`: do NOT modify SOUL.md. Log the proposed change only.
- If `autonomous`: proceed if confidence meets threshold.

Remember: you can NEVER escalate your own governance permissions.
