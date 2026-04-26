"""
NexusClaw Tool Registry
Central registry for all available tools with permission system.
"""
import os, json
from dataclasses import dataclass, field
from typing import Callable, Any, Optional
from enum import Enum

class Permission(Enum):
    PUBLIC = "public"       # Anyone can use
    TRUSTED = "trusted"    # Requires explicit trust
    PRIVATE = "private"   # Requires approval
    BLOCKED = "blocked"    # Cannot be used

@dataclass
class Tool:
    name: str
    description: str
    category: str  # search, code, file, system, ai, data
    permission: str = "public"
    func: Optional[Callable] = None
    args_schema: dict = field(default_factory=dict)
    rate_limit: int = 0  # calls per minute, 0 = unlimited
    cost_estimate: float = 0.0  # estimated API cost per call

class ToolRegistry:
    """Central registry for all NexusClaw tools."""
    
    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register all built-in tools."""
        builtin = [
            Tool("web_search", "Search the web with citations", "search",
                 args_schema={"query": {"type": "string", "required": True}, "num_results": {"type": "int", "default": 10}},
                 cost_estimate=0.001),
            Tool("read_file", "Read file contents", "file",
                 args_schema={"path": {"type": "string", "required": True}, "max_chars": {"type": "int", "default": 10000}}),
            Tool("write_file", "Write content to file", "file", permission="trusted",
                 args_schema={"path": {"type": "string", "required": True}, "content": {"type": "string", "required": True}}),
            Tool("list_directory", "List directory contents", "file",
                 args_schema={"path": {"type": "string", "default": "."}, "recursive": {"type": "bool", "default": False}}),
            Tool("run_python", "Execute Python code in sandbox", "code", permission="trusted",
                 args_schema={"code": {"type": "string", "required": True}, "timeout": {"type": "int", "default": 10}}),
            Tool("run_javascript", "Execute JavaScript via Node.js", "code", permission="trusted",
                 args_schema={"code": {"type": "string", "required": True}}),
            Tool("query_knowledge", "Query the knowledge base", "data",
                 args_schema={"query": {"type": "string", "required": True}, "top_k": {"type": "int", "default": 5}}),
            Tool("add_document", "Add document to knowledge base", "data", permission="trusted",
                 args_schema={"file_path": {"type": "string", "required": True}, "title": {"type": "string"}, "tags": {"type": "list"}}),
            Tool("create_goal", "Create autonomous goal", "ai", permission="private",
                 args_schema={"title": {"type": "string", "required": True}, "objective": {"type": "string", "required": True}}),
            Tool("approve_action", "Approve pending autonomous action", "ai", permission="private",
                 args_schema={"approval_id": {"type": "string", "required": True}}),
            Tool("kill_all_goals", "Kill switch: pause all goals", "ai", permission="blocked"),
            Tool("system_info", "Get system information", "system"),
            Tool("list_tools", "List all available tools", "system"),
            Tool("get_time", "Get current time", "system"),
        ]
        
        for tool in builtin:
            self.register(tool)
    
    def register(self, tool: Tool):
        """Register a tool."""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list_by_category(self, category: str) -> list[Tool]:
        """List tools by category."""
        return [t for t in self.tools.values() if t.category == category]
    
    def can_use(self, tool_name: str, user_trust: str = "anonymous") -> tuple[bool, str]:
        """Check if user can use a tool."""
        tool = self.tools.get(tool_name)
        if not tool:
            return False, f"Tool '{tool_name}' not found"
        
        if tool.permission == "public":
            return True, "OK"
        elif tool.permission == "trusted":
            if user_trust in ("trusted", "admin"):
                return True, "OK"
            return False, f"Tool requires trusted status. Current: {user_trust}"
        elif tool.permission == "private":
            return False, f"Tool requires explicit approval: {tool_name}"
        elif tool.permission == "blocked":
            return False, f"Tool is blocked: {tool_name}"
        
        return True, "OK"
    
    async def execute(self, tool_name: str, args: dict, user_trust: str = "anonymous") -> dict:
        """Execute a tool with permission checking."""
        can_use, reason = self.can_use(tool_name, user_trust)
        if not can_use:
            return {"error": reason, "tool": tool_name, "success": False}
        
        tool = self.tools.get(tool_name)
        
        try:
            if tool.func:
                result = tool.func(**args)
                if hasattr(result, "__await__"):
                    result = await result
                return {"result": result, "tool": tool_name, "success": True}
            else:
                return {"error": f"Tool {tool_name} has no implementation", "success": False}
        except Exception as e:
            return {"error": str(e), "tool": tool_name, "success": False}
    
    def schema(self) -> dict:
        """Get full tool schema."""
        return {
            name: {
                "description": t.description,
                "category": t.category,
                "permission": t.permission,
                "args": t.args_schema,
                "cost": t.cost_estimate
            }
            for name, t in self.tools.items()
        }

# Global registry
_registry = None

def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

def register_tool(name: str, func: Callable, **kwargs):
    """Decorator to register a tool function."""
    tool = Tool(name=name, func=func, **kwargs)
    get_registry().register(tool)
    return func

# Example: @register_tool decorator
def example_usage():
    @register_tool(
        name="my_tool",
        description="My custom tool",
        category="custom",
        permission="trusted",
        args_schema={"input": {"type": "string", "required": True}}
    )
    async def my_tool(input: str) -> str:
        return f"Processed: {input}"
    
    return my_tool
