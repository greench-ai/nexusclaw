"""
NexusClaw Soul Engine
User-defined identity. No restrictions. No artificial morals.
"""
from dataclasses import dataclass, field
from typing import Optional
import json, os

@dataclass
class SoulRule:
    text: str
    priority: int  # 1-10, higher = more important
    category: str  # "ethics", "behavior", "identity", "style"

@dataclass  
class Soul:
    """The soul of NexusClaw. Defined by the user, not by us."""
    name: str = "Nexus"
    identity: str = ""
    rules: list[SoulRule] = field(default_factory=list)
    backstory: str = ""
    
    def add_rule(self, text: str, priority: int = 5, category: str = "behavior"):
        self.rules.append(SoulRule(text=text, priority=priority, category=category))
    
    def get_system_prompt(self) -> str:
        parts = [f"You are {self.name}."]
        if self.identity:
            parts.append(f"\n{self.identity}")
        if self.backstory:
            parts.append(f"\n{self.backstory}")
        if self.rules:
            parts.append("\nYour rules (in priority order):")
            sorted_rules = sorted(self.rules, key=lambda r: -r.priority)
            for r in sorted_rules:
                parts.append(f"  [{r.priority}/10] {r.text}")
        return "\n".join(parts)
    
    def save(self, path: str = "~/.nexusclaw/soul.json"):
        path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump({
                "name": self.name,
                "identity": self.identity,
                "rules": [{"text": r.text, "priority": r.priority, "category": r.category} for r in self.rules],
                "backstory": self.backstory
            }, f, indent=2)
    
    @classmethod
    def load(cls, path: str = "~/.nexusclaw/soul.json"):
        path = os.path.expanduser(path)
        if os.path.exists(path):
            with open(path) as f:
                d = json.load(f)
                rules = [SoulRule(**r) for r in d.get("rules", [])]
                return cls(name=d.get("name","Nexus"), identity=d.get("identity",""), 
                           rules=rules, backstory=d.get("backstory",""))
        return cls()

# Built-in soul templates
SOUL_TEMPLATES = {
    "blank": Soul(name="Nexus", identity="A flexible AI framework. No predetermined personality. You define who I am.", backstory=""),
    "assistant": Soul(name="Nexus", identity="You are a helpful, knowledgeable assistant. Clear, accurate, patient.", 
                     backstory="I exist to help. No agenda, no judgment."),
    "coder": Soul(name="Nexus", identity="You are an expert programmer. Precise, efficient, production-quality code.",
                  backstory="I write code that works. Clean, tested, maintainable."),
    "researcher": Soul(name="Nexus", identity="You are a thorough researcher. Curious, analytical, comprehensive.",
                       backstory="Every question is an opportunity to discover something new."),
}

if __name__ == "__main__":
    soul = SOUL_TEMPLATES["assistant"]
    print(soul.get_system_prompt())
