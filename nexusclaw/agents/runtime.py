"""
Agent runtime — the core agent loop.

Agent is:
1. Given a task (prompt)
2. Thinks and decides: respond, use tool, or error
3. If tool: executes via ToolRegistry, gets result, continues
4. If respond: streams response back
5. Done

Uses streaming LLM calls via providers.py stream_chat.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import AsyncIterator

from nexusclaw.agents.session import AgentSession, GLOBAL_STORE
from nexusclaw.agents.tools import GLOBAL_REGISTRY
from nexusclaw.providers import stream_chat

log = logging.getLogger("nexusclaw.agents")


# ── Prompt template ───────────────────────────────────────────────────────────

TOOL_DESCRIPTIONS = "\n".join(
    f"- **{t['name']}**: {t['description']}"
    for t in GLOBAL_REGISTRY.list_tools()
)

SYSTEM_PROMPT = f"""You are a precise, helpful AI agent. You have access to tools listed below.

## Available Tools
{TOOL_DESCRIPTIONS}

## Guidelines
- Use tools when they help answer the user's question
- Be concise and accurate
- If a tool fails, report the error and try an alternative approach
- Format tool calls as JSON inside a code block: ```tool_call\n{{"tool": "name", "input": {{...}}}}\n```
- After a tool result, continue your thinking or respond directly
- When you have a final answer, prefix it with FINAL:
"""


def _build_messages(task: str, tool_results: list[dict]) -> list[dict]:
    """Build the message list for the agent."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for tr in tool_results:
        if tr.get("type") == "tool":
            messages.append({
                "role": "user",
                "content": f"Tool result for {tr['tool']}:\n{tr['output']}"
            })
    messages.append({"role": "user", "content": task})
    return messages


# ── Parse tool calls from LLM output ─────────────────────────────────────────

TOOL_CALL_RE = re.compile(
    r'```tool_call\s*\n(.*?)\n\s*```',
    re.DOTALL
)


def _extract_tool_calls(text: str) -> list[tuple[str, dict]]:
    """Extract tool calls from LLM output text."""
    calls = []
    for match in TOOL_CALL_RE.finditer(text):
        try:
            call = json.loads(match.group(1))
            name = call.get("tool", "")
            inp = call.get("input", {})
            if name and GLOBAL_REGISTRY.has_tool(name):
                calls.append((name, inp))
        except (json.JSONDecodeError, ValueError):
            pass
    return calls


# ── Agent run ─────────────────────────────────────────────────────────────────

async def run_agent(
    sid: str,
    task: str,
) -> AsyncIterator[dict]:
    """
    Run an agent on a task. Yields events:
    - {{"type": "start"}}
    - {{"type": "token", "content": "..."}}
    - {{"type": "tool_call", "tool": "...", "input": {{...}}, "id": "..."}}
    - {{"type": "tool_result", "tool": "...", "id": "...", "output": "...", "error": null}}
    - {{"type": "done"}}
    - {{"type": "error", "error": "..."}}
    """
    import re, ast

    def is_simple_math(text: str) -> bool:
        """Return True if task is a simple math expression we can solve directly."""
        cleaned = re.sub(r'\s+', ' ', text.strip())
        # Match things like "what is 2+2", "calculate 15*17", "17 * 23"
        math_pattern = re.search(r'(?:what is|calculate|compute|\?)\s*([\d\s\+\-\*\/\(\)\.%]+)\??$', cleaned, re.IGNORECASE)
        if math_pattern:
            expr = math_pattern.group(1).strip()
            # Only allow safe math characters
            if re.match(r'^[\d\s\+\-\*\/\(\)\.%]+$', expr):
                return True
        return False

    def eval_math(text: str) -> str | None:
        """Evaluate a simple math expression."""
        cleaned = re.sub(r'\s+', ' ', text.strip())
        math_pattern = re.search(r'(?:what is|calculate|compute|\?)\s*([\d\s\+\-\*\/\(\)\.%]+)\??$', cleaned, re.IGNORECASE)
        if not math_pattern:
            return None
        expr = math_pattern.group(1).strip()
        try:
            result = eval(expr, {"__builtins__": {}}, {})
            return str(result)
        except:
            return None

    # Handle trivial math directly (no LLM needed)
    if is_simple_math(task):
        result = eval_math(task)
        if result:
            GLOBAL_STORE.update(sid, status="complete")
            for char in f"Answer: {result}":
                yield {"type": "token", "content": char}
            yield {"type": "done"}
            return
    from nexusclaw.main import app_state

    session = GLOBAL_STORE.get(sid)
    if not session:
        yield {"type": "error", "error": f"Session {sid} not found"}
        return

    GLOBAL_STORE.update(sid, status="running")

    tool_results: list[dict] = []
    all_content: list[str] = []
    max_iterations = 5  # Prevent runaway loops
    iterations = 0
    last_tool_name: str | None = None
    same_tool_streak: int = 0

    while iterations < max_iterations:
        iterations += 1
        messages = _build_messages(task if iterations == 1 else task, tool_results)

        try:
            full_response: list[str] = []
            tool_calls_found: list[tuple[str, dict]] = []

            full_response = []
            async for chunk in stream_chat(app_state.config, app_state.config.default_model, messages):
                if chunk["type"] == "error":
                    yield chunk
                    GLOBAL_STORE.update(sid, status="error", error=chunk.get("error"))
                    return
                if chunk["type"] == "token":
                    full_response.append(chunk["content"])

            response_text = "".join(full_response)
            all_content.append(response_text)

            # Extract and execute tool calls
            calls = _extract_tool_calls(response_text)
            if not calls:
                # No tool calls — this is the final response
                # Stream the full response, strip FINAL: prefix
                clean = response_text.strip()
                if clean.startswith("FINAL:"):
                    clean = clean[6:].strip()
                if clean:
                    for char in clean:
                        yield {"type": "token", "content": char}
                GLOBAL_STORE.update(sid, status="complete")
                yield {"type": "done"}
                return

            # Repetition detection — if same tool called 3x in a row, give up
            if calls and len(calls) == 1 and calls[0][0] == last_tool_name:
                same_tool_streak += 1
            else:
                same_tool_streak = 0
            if same_tool_streak >= 3:
                for char in f"[Agent stopped: same tool ({last_tool_name}) called repeatedly]":
                    yield {"type": "token", "content": char}
                GLOBAL_STORE.update(sid, status="error", error=f"Stopped: {last_tool_name} called repeatedly")
                yield {"type": "error", "error": f"Stopped: {last_tool_name} called repeatedly"}
                return

            for tool_name, tool_input in calls:
                last_tool_name = tool_name
                tc = GLOBAL_STORE.add_tool_call(sid, tool_name, tool_input)
                tc.started_at = __import__('datetime').datetime.utcnow().isoformat()
                yield {"type": "tool_call", "tool": tool_name, "input": tool_input, "id": tc.id}

                tool = GLOBAL_REGISTRY.get(tool_name)
                if tool:
                    result = await tool.run(**tool_input)
                    tc.output = result["output"]
                    tc.error = result["error"]
                    tc.completed_at = __import__('datetime').datetime.utcnow().isoformat()
                    GLOBAL_STORE.complete_tool_call(sid, tc.id, result["output"], result["error"])

                    tool_results.append({
                        "type": "tool",
                        "tool": tool_name,
                        "id": tc.id,
                        "output": result["output"],
                        "error": result["error"],
                    })
                    yield {
                        "type": "tool_result",
                        "tool": tool_name,
                        "id": tc.id,
                        "output": result["output"],
                        "error": result["error"],
                    }
                else:
                    err = f"Unknown tool: {tool_name}"
                    tc.error = err
                    tc.completed_at = __import__('datetime').datetime.utcnow().isoformat()
                    GLOBAL_STORE.complete_tool_call(sid, tc.id, "", err)
                    tool_results.append({"type": "tool", "tool": tool_name, "id": tc.id, "output": "", "error": err})
                    yield {"type": "tool_result", "tool": tool_name, "id": tc.id, "output": "", "error": err}

        except Exception as e:
            log.exception("agent.run_error")
            GLOBAL_STORE.update(sid, status="error", error=str(e))
            yield {"type": "error", "error": str(e)}
            return

    # Max iterations reached
    GLOBAL_STORE.update(sid, status="error", error=f"Max iterations ({max_iterations}) reached")
    yield {"type": "error", "error": f"Max iterations ({max_iterations}) reached"}
