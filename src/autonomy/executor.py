"""
NexusClaw Autonomy Executor
Executes goals autonomously with task planning, approval gates, and kill switch.
"""
import asyncio, json, uuid, time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime

class GoalStatus(Enum):
    QUEUED = "queued"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class ApprovalRequest:
    id: str
    goal_id: str
    task_id: str
    action_type: str
    risk_level: str  # low, medium, high, critical
    request_json: dict
    status: str = "pending"
    decided_by: str = ""
    decided_at: str = ""
    created_at: str = ""

@dataclass
class Task:
    id: str
    goal_id: str
    parent_task_id: Optional[str]
    step_index: int
    description: str
    tool_name: str
    input_json: dict
    output_json: dict = field(default_factory=dict)
    status: str = "queued"
    retries: int = 0
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"

@dataclass
class Goal:
    id: str
    workspace_id: str
    creator_user_id: str
    title: str
    objective: str
    constraints: dict
    status: str = "queued"
    tasks: list = field(default_factory=list)
    events: list = field(default_factory=list)
    approvals: list = field(default_factory=list)
    budget: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"

class AutonomyExecutor:
    """
    Executes goals autonomously with:
    - Task decomposition (goal → tasks)
    - Tool execution
    - Approval gates for sensitive actions
    - Kill switch (pause all)
    """
    
    def __init__(self, api_url: str = "http://localhost:8080"):
        self.api_url = api_url
        self.active_goals: dict[str, Goal] = {}
        self.pending_approvals: list[ApprovalRequest] = []
        self.kill_switched = False
        self.tool_registry = self._build_tool_registry()
    
    def _build_tool_registry(self) -> dict:
        """Register available tools."""
        return {
            "web_search": self.tool_web_search,
            "read_file": self.tool_read_file,
            "write_file": self.tool_write_file,
            "run_code": self.tool_run_code,
            "http_request": self.tool_http_request,
            "spawn_agent": self.tool_spawn_agent,
            "ask_human": self.tool_ask_human,
        }
    
    async def create_goal(self, title: str, objective: str, constraints: dict = None, 
                         creator_id: str = "system", workspace_id: str = "default") -> Goal:
        """Create and queue a new goal."""
        goal = Goal(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            creator_user_id=creator_id,
            title=title,
            objective=objective,
            constraints=constraints or {}
        )
        self.active_goals[goal.id] = goal
        goal.events.append({"type": "created", "at": goal.created_at})
        return goal
    
    async def execute_goal(self, goal_id: str, user_id: str = "system") -> Goal:
        """Execute a goal: plan → execute → complete."""
        goal = self.active_goals.get(goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found")
        
        if self.kill_switched:
            goal.status = GoalStatus.PAUSED.value
            goal.events.append({"type": "killed", "at": datetime.utcnow().isoformat() + "Z", "by": "kill_switch"})
            return goal
        
        # Phase 1: Planning
        goal.status = GoalStatus.PLANNING.value
        goal.tasks = await self._decompose(goal)
        goal.status = GoalStatus.EXECUTING.value
        goal.events.append({"type": "started", "at": datetime.utcnow().isoformat() + "Z", "by": user_id})
        
        # Phase 2: Execute tasks
        for task in goal.tasks:
            if self.kill_switched:
                goal.status = GoalStatus.PAUSED.value
                goal.events.append({"type": "killed", "at": datetime.utcnow().isoformat() + "Z", "by": "kill_switch"})
                break
            
            result = await self._execute_task(task, goal)
            if result["status"] == "blocked":
                goal.status = GoalStatus.BLOCKED.value
                break
            elif result["status"] == "failed":
                goal.status = GoalStatus.FAILED.value
                goal.events.append({"type": "failed", "at": datetime.utcnow().isoformat() + "Z", "task": task.id})
                break
        
        if goal.status == GoalStatus.EXECUTING.value:
            goal.status = GoalStatus.COMPLETED.value
            goal.events.append({"type": "completed", "at": datetime.utcnow().isoformat() + "Z"})
        
        goal.updated_at = datetime.utcnow().isoformat() + "Z"
        return goal
    
    async def _decompose(self, goal: Goal) -> list[Task]:
        """Decompose goal objective into tasks using LLM planning."""
        # Simple rule-based decomposition for now
        # In production: use LLM to generate task plan
        tasks = []
        objectives = goal.objective.split(";")
        
        for i, obj in enumerate(objectives):
            obj = obj.strip()
            if not obj:
                continue
            
            task = Task(
                id=str(uuid.uuid4()),
                goal_id=goal.id,
                parent_task_id=None,
                step_index=i,
                description=obj,
                tool_name=self._select_tool(obj),
                input_json={"objective": obj}
            )
            tasks.append(task)
        
        return tasks
    
    def _select_tool(self, task_description: str) -> str:
        """Select appropriate tool for task."""
        desc = task_description.lower()
        if "search" in desc or "find" in desc or "what is" in desc:
            return "web_search"
        if "read" in desc or "get" in desc:
            return "read_file"
        if "write" in desc or "save" in desc or "create" in desc:
            return "write_file"
        if "run" in desc or "execute" in desc or "code" in desc:
            return "run_code"
        if "ask" in desc or "confirm" in desc or "approve" in desc:
            return "ask_human"
        return "spawn_agent"
    
    async def _execute_task(self, task: Task, goal: Goal) -> dict:
        """Execute a single task with tool + approval gates."""
        task.status = TaskStatus.RUNNING.value
        task.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # Check if approval needed
        risk = self._assess_risk(task)
        if risk in ("high", "critical"):
            task.status = TaskStatus.WAITING_APPROVAL.value
            approval = ApprovalRequest(
                id=str(uuid.uuid4()),
                goal_id=goal.id,
                task_id=task.id,
                action_type=task.tool_name,
                risk_level=risk,
                request_json=task.input_json,
                created_at=datetime.utcnow().isoformat() + "Z"
            )
            self.pending_approvals.append(approval)
            goal.approvals.append(approval)
            goal.events.append({
                "type": "approval_requested",
                "task_id": task.id,
                "risk": risk,
                "at": datetime.utcnow().isoformat() + "Z"
            })
            return {"status": "waiting_approval", "approval_id": approval.id}
        
        # Execute directly
        tool_fn = self.tool_registry.get(task.tool_name)
        if tool_fn:
            try:
                output = await tool_fn(task.input_json)
                task.output_json = output
                task.status = TaskStatus.COMPLETED.value
            except Exception as e:
                task.status = TaskStatus.FAILED.value
                task.output_json = {"error": str(e)}
                return {"status": "failed"}
        else:
            task.output_json = {"error": f"Unknown tool: {task.tool_name}"}
            task.status = TaskStatus.FAILED.value
            return {"status": "failed"}
        
        task.updated_at = datetime.utcnow().isoformat() + "Z"
        return {"status": "completed"}
    
    def _assess_risk(self, task: Task) -> str:
        """Assess risk level of a task."""
        high_risk = ["write_file", "spawn_agent", "http_request"]
        critical_risk = ["run_code"]
        
        if task.tool_name in critical_risk:
            return "critical"
        elif task.tool_name in high_risk:
            return "high"
        return "low"
    
    def approve(self, approval_id: str, user_id: str) -> bool:
        """Approve a pending action."""
        for approval in self.pending_approvals:
            if approval.id == approval_id:
                approval.status = "approved"
                approval.decided_by = user_id
                approval.decided_at = datetime.utcnow().isoformat() + "Z"
                
                # Find and resume task
                for goal in self.active_goals.values():
                    for task in goal.tasks:
                        if task.id == approval.task_id:
                            task.status = TaskStatus.RUNNING.value
                            goal.events.append({
                                "type": "approval_granted",
                                "task_id": task.id,
                                "by": user_id,
                                "at": approval.decided_at
                            })
                            # Resume execution
                            asyncio.create_task(self._resume_task(task, goal))
                            return True
        return False
    
    def deny(self, approval_id: str, user_id: str) -> bool:
        """Deny a pending action."""
        for approval in self.pending_approvals:
            if approval.id == approval_id:
                approval.status = "denied"
                approval.decided_by = user_id
                approval.decided_at = datetime.utcnow().isoformat() + "Z"
                
                for goal in self.active_goals.values():
                    for task in goal.tasks:
                        if task.id == approval.task_id:
                            task.status = TaskStatus.BLOCKED.value
                            goal.status = GoalStatus.BLOCKED.value
                            goal.events.append({
                                "type": "approval_denied",
                                "task_id": task.id,
                                "by": user_id,
                                "at": approval.decided_at
                            })
                            return True
        return False
    
    async def _resume_task(self, task: Task, goal: Goal):
        """Resume a task after approval."""
        tool_fn = self.tool_registry.get(task.tool_name)
        if tool_fn:
            try:
                output = await tool_fn(task.input_json)
                task.output_json = output
                task.status = TaskStatus.COMPLETED.value
            except Exception as e:
                task.output_json = {"error": str(e)}
                task.status = TaskStatus.FAILED.value
    
    def kill_all(self, user_id: str = "system") -> int:
        """Kill switch: pause all active goals."""
        self.kill_switched = True
        count = 0
        for goal in self.active_goals.values():
            if goal.status == GoalStatus.EXECUTING.value:
                goal.status = GoalStatus.PAUSED.value
                goal.events.append({
                    "type": "killed",
                    "at": datetime.utcnow().isoformat() + "Z",
                    "by": user_id
                })
                count += 1
        self.kill_switched = False
        return count
    
    def resume_all(self, user_id: str = "system") -> int:
        """Resume all paused goals."""
        count = 0
        for goal in self.active_goals.values():
            if goal.status == GoalStatus.PAUSED.value:
                goal.status = GoalStatus.EXECUTING.value
                goal.events.append({
                    "type": "resumed",
                    "at": datetime.utcnow().isoformat() + "Z",
                    "by": user_id
                })
                asyncio.create_task(self.execute_goal(goal.id, user_id))
                count += 1
        return count
    
    # === Tools ===
    async def tool_web_search(self, input_json: dict) -> dict:
        """Perplexity-style web search."""
        query = input_json.get("objective", "")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
                ) as resp:
                    data = await resp.json()
                    results = data.get("RelatedTopics", [])[:5]
                    return {
                        "query": query,
                        "results": [{"text": r.get("Text",""), "url": r.get("FirstURL","")} for r in results if r.get("Text")],
                        "summary": data.get("AbstractText", "")
                    }
        except Exception as e:
            return {"error": str(e)}
    
    async def tool_read_file(self, input_json: dict) -> dict:
        """Read file contents."""
        import os
        path = input_json.get("path", "")
        try:
            with open(path) as f:
                content = f.read(int(input_json.get("max_chars", 10000)))
            return {"path": path, "content": content, "size": len(content)}
        except Exception as e:
            return {"error": str(e)}
    
    async def tool_write_file(self, input_json: dict) -> dict:
        """Write file contents."""
        import os
        path = input_json.get("path", "")
        content = input_json.get("content", "")
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return {"path": path, "bytes_written": len(content)}
        except Exception as e:
            return {"error": str(e)}
    
    async def tool_run_code(self, input_json: dict) -> dict:
        """Execute code in sandbox."""
        code = input_json.get("code", "")
        language = input_json.get("language", "python")
        # Security: in production, use proper sandbox
        return {"warning": "Code execution requires sandboxing", "code_length": len(code)}
    
    async def tool_http_request(self, input_json: dict) -> dict:
        """Make HTTP request."""
        return {"warning": "HTTP requests require approval for security"}
    
    async def tool_spawn_agent(self, input_json: dict) -> dict:
        """Spawn sub-agent."""
        return {"warning": "Agent spawning requires approval for security"}
    
    async def tool_ask_human(self, input_json: dict) -> dict:
        """Ask human for input."""
        return {"question": input_json.get("objective", "?"), "status": "requires_human"}

if __name__ == "__main__":
    executor = AutonomyExecutor()
    goal = asyncio.run(executor.create_goal("Research AI trends", "search for latest AI news; summarize top 3 findings"))
    print(f"Created goal: {goal.id}")
    result = asyncio.run(executor.execute_goal(goal.id))
    print(f"Goal status: {result.status}")
