"""
AutoGen team factory — round_robin or selector group chat.
"""

from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat


def create_team(
    agents: list,
    team_type: str = "round_robin",
    max_turns: int = 15,
) -> RoundRobinGroupChat | SelectorGroupChat:
    """
    Create an AutoGen group chat team.

    Args:
        agents: list of AssistantAgent instances
        team_type: "round_robin" (fixed turns) or "selector" (LLM picks next speaker)
        max_turns: max total messages before termination

    Returns:
        Configured group chat team
    """
    if team_type == "selector":
        # SelectorGroupChat requires a model_client
        from nexusclaw.agents.groupchat.agents import create_model_client
        model_client = create_model_client()
        return SelectorGroupChat(
            participants=agents,
            model_client=model_client,
            max_turns=max_turns,
            allow_repeated_speaker=True,
        )
    # Default: round robin
    return RoundRobinGroupChat(
        participants=agents,
        max_turns=max_turns,
    )
