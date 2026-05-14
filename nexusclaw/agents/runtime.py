"""
Agent runtime — proper autonomous agent loop.

Agent is:
1. Given a task, thinks step-by-step
2. Decides: respond, use tool, or reason more
3. If tool: executes, gets result, THINKS about it, continues
4. If reasoning: streams thoughts so user sees the process
5. Done when it has a real answer

Streaming LLM via providers.py.
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


# ── System prompt with thinking instructions ─────────────────────────────────

TOOL_DESCRIPTIONS = "\n".join(
    f"- **{t['name']}**: {t['description']}"
    for t in GLOBAL_REGISTRY.list_tools()
)

SYSTEM_PROMPT = f"""You are a precise, autonomous AI agent. You have access to tools.

## Available Tools
{TOOL_DESCRIPTIONS}

## How you work

**Step 1 — THINK**: Before every action, write your reasoning in a `thought` block.
**Step 2 — ACT**: Then either call a tool OR give your final answer.

Format your responses like this:

```
thought: I'm looking at the user's request. They want X. I should first check Y by running a command.
action: bash ls /some/path
```

```
tool_result: ...output from tool...
thought: I got the output. It shows Z. Now I should follow up with...
action: bash cat /some/file
```

```
thought: I have all the information I need. The answer is...
final: Your comprehensive answer here.
```

## Rules
- ALWAYS write a `thought:` before taking any action
- If a tool fails, note it and try an alternative approach
- Keep thoughts concise but show your reasoning
- When you have a verified answer, respond with `final:` prefix
- Never call the same tool 3 times in a row without making progress
"""


def _build_messages(task: str, tool_results: list[dict], agent_history: list[dict]) -> list[dict]:
    """Build the message list for the agent."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Add conversation history for continuity
    for entry in agent_history:
        messages.append({"role": entry["role"], "content": entry["content"]})
    # Add tool results
    for tr in tool_results:
        messages.append({
            "role": "user",
            "content": f"Tool result for {tr['tool']}:\n{tr['output']}"
        })
    # Current task
    messages.append({"role": "user", "content": task})
    return messages


# ── Parse model output ────────────────────────────────────────────────────────

THOUGHT_RE = re.compile(r'^thought:\s*(.+?)\s*$.', re.MULTILINE | re.IGNORECASE)
FINAL_RE = re.compile(r'^final:\s*(.+)', re.MULTILINE | re.IGNORECASE)
ACTION_RE = re.compile(r'^action:\s*(\w+)\s*(.+?)\s*$', re.MULTILINE)
TOOL_CALL_BLOCK_RE = re.compile(
    r'```tool_call\s*\n(.*?)\n\s*```',
    re.DOTALL
)


def _parse_response(text: str) -> tuple[str | None, str | None, str | None]:
    """
    Parse model output into (thought, action_tool, action_input).
    Returns (thought_text, tool_name, tool_input_json_str) or (None, None, None).
    """
    thought = None
    action_tool = None
    action_input = None

    # Extract thought
    t_matches = THOUGHT_RE.findall(text)
    if t_matches:
        thought = " ".join(t_matches).strip()

    # Check for final answer
    final_match = FINAL_RE.search(text)
    if final_match:
        return thought, "final", final_match.group(1).strip()

    # Check for action: tool_name input_json
    for match in ACTION_RE.finditer(text):
        tool_name = match.group(1).strip()
        input_str = match.group(2).strip()
        if GLOBAL_REGISTRY.has_tool(tool_name):
            action_tool = tool_name
            # Try to parse as JSON
            try:
                action_input = json.loads(input_str)
            except json.JSONDecodeError:
                # Treat as a simple string input if the tool accepts one field
                action_input = {"input": input_str}
            break

    # Also check tool_call blocks
    if not action_tool:
        for match in TOOL_CALL_BLOCK_RE.finditer(text):
            try:
                call = json.loads(match.group(1))
                name = call.get("tool", "")
                inp = call.get("input", {})
                if GLOBAL_REGISTRY.has_tool(name):
                    action_tool = name
                    action_input = inp
                    break
            except (json.JSONDecodeError, ValueError):
                pass

    return thought, action_tool, action_input


# ── Agent run ─────────────────────────────────────────────────────────────────

async def run_agent(
    sid: str,
    task: str,
) -> AsyncIterator[dict]:
    """
    Run a proper autonomous agent loop.

    Events yielded:
    - {"type": "start"}
    - {"type": "reasoning", "content": "..."}     ← visible thinking
    - {"type": "tool_call", "tool": "...", "input": {...}, "id": "..."}
    - {"type": "tool_result", "tool": "...", "id": "...", "output": "...", "error": null}
    - {"type": "token", "content": "..."}          ← final answer tokens
    - {"type": "done"}
    - {"type": "error", "error": "..."}
    """
    session = GLOBAL_STORE.get(sid)
    if not session:
        yield {"type": "error", "error": f"Session {sid} not found"}
        return

    from nexusclaw.main import app_state

    GLOBAL_STORE.update(sid, status="running")

    tool_results: list[dict] = []
    agent_history: list[dict] = []
    max_iterations = 8
    iterations = 0
    last_tool_name: str | None = None
    same_tool_count = 0

    while iterations < max_iterations:
        iterations += 1
        messages = _build_messages(task, tool_results, agent_history)

        try:
            full_response = []
            async for chunk in stream_chat(app_state.config, app_state.config.default_model, messages):
                if chunk["type"] == "error":
                    yield chunk
                    GLOBAL_STORE.update(sid, status="error", error=chunk.get("error"))
                    return
                if chunk["type"] == "token":
                    full_response.append(chunk["content"])

            response_text = "".join(full_response)
            agent_history.append({"role": "assistant", "content": response_text})

            # Parse what the model said
            thought, action, action_input = _parse_response(response_text)

            # Stream the reasoning so user can see it
            if thought:
                yield {"type": "reasoning", "content": thought}

            # Check for final answer
            if action == "final":
                # Stream the final answer tokens
                final_text = action_input if action_input else ""
                for char in final_text:
                    yield {"type": "token", "content": char}
                GLOBAL_STORE.update(sid, status="complete")
                yield {"type": "done"}
                return

            # No action needed — model decided to respond
            if not action or action not in GLOBAL_REGISTRY.list_tool_names():
                # Model gave a text response without a tool — stream it as final
                clean = response_text.strip()
                if clean and not clean.startswith("thought:"):
                    for char in clean:
                        yield {"type": "token", "content": char}
                elif thought:
                    # Just reasoning, no answer yet — loop again
                    pass
                GLOBAL_STORE.update(sid, status="complete")
                yield {"type": "done"}
                return

            # Repetition guard
            if action == last_tool_name:
                same_tool_count += 1
            else:
                same_tool_count = 1
                last_tool_name = action

            if same_tool_count >= 3:
                yield {
                    "type": "reasoning",
                    "content": f"[Stopping: {action} called repeatedly without progress]"
                }
                GLOBAL_STORE.update(sid, status="error", error=f"Stopped: {action} called repeatedly")
                yield {"type": "error", "error": f"Tool {action} called repeatedly"}
                return

            # Execute the tool
            tc = GLOBAL_STORE.add_tool_call(sid, action, action_input or {})
            tc.started_at = __import__("datetime").datetime.utcnow().isoformat()
            yield {"type": "tool_call", "tool": action, "input": action_input or {}, "id": tc.id}

            tool = GLOBAL_REGISTRY.get(action)
            if tool:
                result = await tool.run(**(action_input or {}))
                tc.output = result["output"]
                tc.error = result["error"]
                tc.completed_at = __import__("datetime").datetime.utcnow().isoformat()
                GLOBAL_STORE.complete_tool_call(sid, tc.id, result["output"], result["error"])

                tool_results.append({
                    "type": "tool",
                    "tool": action,
                    "id": tc.id,
                    "output": result["output"],
                    "error": result["error"],
                })
                yield {
                    "type": "tool_result",
                    "tool": action,
                    "id": tc.id,
                    "output": result["output"],
                    "error": result["error"],
                }
            else:
                err = f"Unknown tool: {action}"
                tc.error = err
                tc.completed_at = __import__("datetime").datetime.utcnow().isoformat()
                GLOBAL_STORE.complete_tool_call(sid, tc.id, "", err)
                tool_results.append({"type": "tool", "tool": action, "id": tc.id, "output": "", "error": err})
                yield {"type": "tool_result", "tool": action, "id": tc.id, "output": "", "error": err}

        except Exception as e:
            log.exception("agent.run_error")
            GLOBAL_STORE.update(sid, status="error", error=str(e))
            yield {"type": "error", "error": str(e)}
            return

    GLOBAL_STORE.update(sid, status="error", error=f"Max iterations ({max_iterations}) reached")
    yield {"type": "error", "error": f"Max iterations ({max_iterations}) reached"}
