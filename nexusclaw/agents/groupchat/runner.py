"""
Async group chat runner — runs the AutoGen team and yields events.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from autogen_agentchat.messages import TextMessage

from nexusclaw.agents.groupchat.agents import create_all_persona_agents, PERSONAS
from nexusclaw.agents.groupchat.store import GLOBAL_GROUP_STORE, GroupStatus
from nexusclaw.agents.groupchat.team import create_team

log = logging.getLogger("nexusclaw.groupchat")


async def run_group_chat(
    sid: str,
    agent_ids: list[str],
    team_type: str,
    task: str,
) -> AsyncIterator[dict]:
    """
    Run a group chat session. Yields events:
    - {{"type": "start"}}
    - {{"type": "message", "agent": "...", "content": "..."}}
    - {{"type": "done"}}
    - {{"type": "error", "error": "..."}}
    """
    if not agent_ids:
        yield {"type": "error", "error": "No agents selected"}
        return

    # Validate agents
    for aid in agent_ids:
        if aid not in PERSONAS:
            yield {"type": "error", "error": f"Unknown agent: {aid}"}
            return

    GLOBAL_GROUP_STORE.update_status(sid, GroupStatus.RUNNING)
    yield {"type": "start"}

    try:
        # Create agents
        agents = create_all_persona_agents(agent_ids)

        # Create team
        team = create_team(agents, team_type, max_turns=20)

        # Build the task message
        agent_names = [PERSONAS[aid]["name"] for aid in agent_ids]
        task_message = (
            f"You are working as a team to solve the following task.\n"
            f"Team members: {', '.join(agent_names)}\n"
            f"Task: {task}\n\n"
            f"Each agent should contribute their perspective. "
            f"Discuss and work toward a comprehensive answer."
        )

        # Run the team — stream messages
        async for event in team.run_stream(task=task_message):
            # Handle TextMessage (from agents)
            if isinstance(event, TextMessage):
                agent_name = event.source or "unknown"
                content = event.content
                GLOBAL_GROUP_STORE.add_message(sid, agent_name, content)
                yield {"type": "message", "agent": agent_name, "content": content}
            # Ignore other event types (tool calls, thoughts, etc.)
            pass

        GLOBAL_GROUP_STORE.update_status(sid, GroupStatus.COMPLETE)
        yield {"type": "done"}

    except Exception as e:
        log.exception("groupchat.run_error")
        GLOBAL_GROUP_STORE.update_status(sid, GroupStatus.ERROR, error=str(e))
        yield {"type": "error", "error": str(e)}
