"""
NexusClaw Audit Log
Track all significant actions for security and compliance.
"""
import os, json, datetime
from collections import defaultdict
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

class AuditLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AuditEntry:
    timestamp: str
    level: str
    actor: str       # user_id or "system" or "naruto"
    action: str      # e.g. "chat.message", "file.upload", "goal.create"
    resource: str    # what was affected
    result: str      # "success", "failure", "blocked"
    details: dict    # additional context
    ip_address: Optional[str] = None

class AuditLog:
    """
    Immutable audit log — every significant action is recorded.
    """
    
    def __init__(self, log_path: str = "~/.nexusclaw/audit.log"):
        self.log_path = Path(os.path.expanduser(log_path))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, level: str, actor: str, action: str, resource: str = "",
            result: str = "success", details: dict = None, ip: str = None):
        """Log an audit entry."""
        entry = AuditEntry(
            timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            level=level,
            actor=actor,
            action=action,
            resource=resource,
            result=result,
            details=details or {},
            ip_address=ip
        )
        
        with open(self.log_path, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")
        
        return entry
    
    def query(self, filters: dict = None, limit: int = 100) -> list[AuditEntry]:
        """Query audit log with filters."""
        filters = filters or {}
        results = []
        
        if not self.log_path.exists():
            return results
        
        with open(self.log_path) as f:
            for line in f:
                try:
                    e = json.loads(line)
                    match = True
                    
                    if filters.get("actor") and e["actor"] != filters["actor"]:
                        match = False
                    if filters.get("action") and not e["action"].startswith(filters["action"]):
                        match = False
                    if filters.get("level") and e["level"] != filters["level"]:
                        match = False
                    if filters.get("result") and e["result"] != filters["result"]:
                        match = False
                    if filters.get("since"):
                        if e["timestamp"] < filters["since"]:
                            match = False
                    
                    if match:
                        results.append(AuditEntry(**e))
                except:
                    continue
        
        return results[-limit:]  # Most recent first if reversed
    
    def summary(self, days: int = 7) -> dict:
        """Get audit summary for N days."""
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat() + "Z"
        entries = self.query(filters={"since": cutoff}, limit=10000)
        
        by_action = defaultdict(int)
        by_actor = defaultdict(int)
        by_level = defaultdict(int)
        failures = []
        
        for e in entries:
            by_action[e.action] += 1
            by_actor[e.actor] += 1
            by_level[e.level] += 1
            if e.result == "failure":
                failures.append(e)
        
        return {
            "total_events": len(entries),
            "days": days,
            "by_action": dict(by_action),
            "by_actor": dict(by_actor),
            "by_level": dict(by_level),
            "failures": [asdict(f) for f in failures[-10:]],  # Last 10 failures
            "actors": list(by_actor.keys()),
        }
    
    def security_report(self) -> dict:
        """Generate security report — flag anomalies."""
        summary = self.summary(days=7)
        alerts = []
        
        # Flag high failure rate
        total = summary["total_events"]
        failures = len(summary["failures"])
        if total > 0 and failures / total > 0.1:
            alerts.append(f"High failure rate: {failures}/{total} ({failures/total*100:.1f}%)")
        
        # Flag unknown actors
        unknown = [a for a in summary["actors"] if a not in ("system", "naruto")]
        if unknown:
            alerts.append(f"Non-standard actors: {unknown}")
        
        # Flag CRITICAL entries
        critical = [e for e in self.query(filters={"level": "critical"}, limit=100)]
        if critical:
            alerts.append(f"{len(critical)} CRITICAL entries in last 7 days")
        
        return {
            "alerts": alerts,
            "summary": summary,
            "generated": datetime.datetime.utcnow().isoformat() + "Z"
        }

# Convenience methods
def audit_chat(user: str, message_preview: str, tokens: int = 0):
    """Log a chat message."""
    log = AuditLog()
    log.log("info", user, "chat.message", result="success", details={
        "preview": message_preview[:100], "tokens": tokens
    })

def audit_goal(user: str, goal_id: str, title: str, action: str):
    """Log a goal action (create/approve/complete/kill)."""
    log = AuditLog()
    log.log("info", user, f"goal.{action}", resource=goal_id, details={"title": title})

def audit_file(user: str, filename: str, action: str, size: int = 0):
    """Log a file action."""
    log = AuditLog()
    log.log("info", user, f"file.{action}", resource=filename, details={"size_bytes": size})

def audit_security(event: str, details: dict, level: str = "warning"):
    """Log a security event."""
    log = AuditLog()
    log.log(level, "system", "security." + event, result="logged", details=details)

def audit_blocked(user: str, action: str, reason: str):
    """Log a blocked action."""
    log = AuditLog()
    log.log("warning", user, "blocked." + action, result="blocked", details={"reason": reason})
