"""
Agent tools — registry of built-in tools available to agents.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Callable, TypedDict


class ToolResult(TypedDict):
    success: bool
    output: str
    error: str | None


class Tool:
    def __init__(self, name: str, description: str, input_schema: dict, func: Callable):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.func = func

    async def run(self, **kwargs) -> ToolResult:
        try:
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)
            if isinstance(result, dict) and "success" in result:
                return result
            return ToolResult(success=True, output=str(result), error=None)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, description: str, input_schema: dict, func: Callable):
        self._tools[name] = Tool(name, description, input_schema, func)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [t.to_dict() for t in self._tools.values()]

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def list_tool_names(self) -> list[str]:
        return list(self._tools.keys())


GLOBAL_REGISTRY = ToolRegistry()


def tool(name: str, description: str, input_schema: dict):
    """Decorator to register a tool."""
    def decorator(func: Callable):
        GLOBAL_REGISTRY.register(name, description, input_schema, func)
        return func
    return decorator


# ── Built-in tools ────────────────────────────────────────────────────────────


@tool(
    name="calculator",
    description="Evaluate a mathematical expression. Use for computations, not manual arithmetic.",
    input_schema={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Mathematical expression, e.g. '2+2' or 'sqrt(16)'"}
        },
        "required": ["expression"]
    }
)
def calculator(expression: str) -> ToolResult:
    """Evaluate a math expression safely."""
    try:
        # Safe eval — only allow math operations
        allowed = set("0123456789.+-*/()**% ")
        if not all(c in allowed for c in expression):
            return ToolResult(success=False, output="", error="Invalid characters in expression")
        result = eval(expression, {"__builtins__": {}}, {})
        return ToolResult(success=True, output=str(result), error=None)
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


@tool(
    name="search",
    description="Search the web for information. Use for factual queries, news, or anything requiring current information.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Max results (default 5)"}
        },
        "required": ["query"]
    }
)
async def web_search(query: str, max_results: int = 5) -> ToolResult:
    """Search the web via Tavily."""
    try:
        from nexusclaw.main import app_state
        if not app_state.config.providers:
            return ToolResult(success=False, output="", error="No providers configured")
        # Use the default model for search results summarization
        # Tavily API would be used here — for now return a placeholder
        return ToolResult(success=True, output=f"Search for: {query} (max {max_results} results)", error=None)
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


@tool(
    name="read_file",
    description="Read the contents of a file from the filesystem.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute file path"}
        },
        "required": ["path"]
    }
)
def read_file(path: str) -> ToolResult:
    """Read a file."""
    try:
        with open(path, "r") as f:
            content = f.read(10000)  # limit to 10k chars
        return ToolResult(success=True, output=content, error=None)
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


@tool(
    name="wikipedia",
    description="Look up a topic on Wikipedia. Use for factual background information.",
    input_schema={
        "type": "object",
        "properties": {
            "topic": {"type": "string", "description": "Topic to look up"}
        },
        "required": ["topic"]
    }
)
def wikipedia(topic: str) -> ToolResult:
    """Quick Wikipedia lookup via Wikipedia API."""
    import urllib.request, urllib.parse, json
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}"
        req = urllib.request.Request(url, headers={"User-Agent": "NexusClaw/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        return ToolResult(
            success=True,
            output=f"**{data.get('title', topic)}**\n\n{data.get('extract', 'No summary available.')}",
            error=None
        )
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


@tool(
    name="bash",
    description="Execute a shell command inside the Docker container. Use for Docker operations, internal app commands.",
    input_schema={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute inside container"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"}
        },
        "required": ["command"]
    }
)
def bash(command: str, timeout: int = 30) -> ToolResult:
    """Execute a shell command in Docker container context."""
    import subprocess
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout[:5000] if result.stdout else ""
        err = result.stderr[:1000] if result.stderr else ""
        if result.returncode != 0 and not output:
            return ToolResult(success=False, output="", error=err or f"Exit code: {result.returncode}")
        return ToolResult(success=True, output=(output + ("\n[stderr]: " + err if err else "")), error=None)
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, output="", error=f"Command timed out after {timeout}s")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


@tool(
    name="host_bash",
    description="Execute a shell command on the WSL2/Linux host machine (not inside Docker). Use for file operations on the host filesystem like /home/greench/, git operations, npm, docker commands on host, etc.",
    input_schema={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to run on the host machine"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"}
        },
        "required": ["command"]
    }
)
def host_bash(command: str, timeout: int = 30) -> ToolResult:
    """Execute a shell command on the WSL2/Linux host.

    Docker containers have their own filesystem. This runs commands
    on the WSL2 host where the actual files live at /home/greench/.
    """
    import subprocess
    try:
        # Use `wsl -e bash -c` to run on the WSL2 host
        # This works whether we are in a Docker container or native Linux
        result = subprocess.run(
            ["wsl", "-e", "bash", "-c", command],
            capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout[:5000] if result.stdout else ""
        err = result.stderr[:1000] if result.stderr else ""
        if result.returncode != 0 and not output:
            return ToolResult(success=False, output="", error=err or f"Exit code: {result.returncode}")
        return ToolResult(success=True, output=(output + ("\n[stderr]: " + err if err else "")), error=None)
    except FileNotFoundError:
        return ToolResult(success=False, output="", error="wsl command not found — is this running on Windows with WSL2?")
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, output="", error=f"Command timed out after {timeout}s")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))
