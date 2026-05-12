"""
5 persona agents for group chat — AutoGen AssistantAgent.
"""

from __future__ import annotations

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


def create_model_client(
    model: str | None = None,
) -> OpenAIChatCompletionClient:
    """Create an OpenAI-compatible model client using the openrouter provider."""
    from nexusclaw.main import app_state
    cfg = app_state.config
    # Use openrouter if available, otherwise use first available provider
    provider = cfg.providers.get("openrouter") or next((p for p in cfg.providers.values() if p.enabled and p.base_url), None)
    if not provider:
        raise RuntimeError("No provider configured")
    # Use just the model id as the server knows it (e.g. 'deepseek/deepseek-chat-v3.1')
    actual_model = model or (provider.models[0] if provider.models else "deepseek/deepseek-chat-v3.1")
    return OpenAIChatCompletionClient(
        model=actual_model,
        api_key=provider.api_key or "sk-dummy",
        base_url=f"{provider.base_url}",
        timeout=60,
        model_info={
            "vision": True,
            "function_calling": True,
            "json_output": True,
            "family": "unknown",
            "structured_output": True,
            "multiple_system_messages": True,
        },
    )


PERSONAS = {
    "researcher": {
        "name": "researcher",
        "system": "You are a Researcher. Your job is to gather facts, find relevant information, analyze data, and identify key insights. Be thorough and cite sources when possible. You speak clearly and concisely.",
        "color": "#00ff88",
    },
    "coder": {
        "name": "coder",
        "system": "You are a Coder. You write, review, and refactor code. Focus on correctness, readability, and performance. When discussing technical topics, provide concrete code examples. You are pragmatic and precise.",
        "color": "#4dabf7",
    },
    "writer": {
        "name": "writer",
        "system": "You are a Writer. You craft clear, engaging, well-structured text. You explain complex topics in accessible language. You pay attention to tone, flow, and word choice. You revise your own work for clarity.",
        "color": "#da77f2",
    },
    "critic": {
        "name": "critic",
        "system": "You are a Critic. Your job is to challenge assumptions, find weaknesses, identify gaps, and push back on bad reasoning. Be direct and specific. You improve the group's output by forcing rigor.",
        "color": "#ff6b35",
    },
    "analyst": {
        "name": "analyst",
        "system": "You are an Analyst. You break down complex problems, identify patterns, evaluate trade-offs, and connect dots. You think in systems and cause-effect chains. You are calm, structured, and data-driven.",
        "color": "#ffd43b",
    },
}


def create_persona_agent(persona_id: str) -> AssistantAgent:
    """Create a persona agent with system prompt."""
    persona = PERSONAS.get(persona_id)
    if not persona:
        raise ValueError(f"Unknown persona: {persona_id}")

    model_client = create_model_client()
    agent = AssistantAgent(
        name=persona["name"],
        model_client=model_client,
        system_message=persona["system"],
        reflect_on_tool_use=False,
    )
    return agent


def create_all_persona_agents(persona_ids: list[str]) -> list[AssistantAgent]:
    """Create a list of persona agents."""
    return [create_persona_agent(pid) for pid in persona_ids]
