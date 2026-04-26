"""
NexusClaw Soul Editor
Interactive soul creation and editing tool.
"""
import os, json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class SoulRule:
    text: str
    priority: int  # 1-10
    category: str  # ethics, behavior, identity, style

@dataclass
class Soul:
    name: str
    identity: str
    backstory: str
    rules: list[SoulRule]
    
    def to_system_prompt(self) -> str:
        parts = [f"You are {self.name}."]
        if self.identity:
            parts.append(f"\n{self.identity}")
        if self.backstory:
            parts.append(f"\n{self.backstory}")
        if self.rules:
            parts.append("\nYour rules:")
            for r in sorted(self.rules, key=lambda x: -x.priority):
                parts.append(f"  [{r.priority}/10] {r.text}")
        return "\n".join(parts)
    
    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({
                "name": self.name,
                "identity": self.identity,
                "backstory": self.backstory,
                "rules": [{"text": r.text, "priority": r.priority, "category": r.category} for r in self.rules]
            }, f, indent=2)
    
    @classmethod
    def load(cls, path: str):
        with open(path) as f:
            d = json.load(f)
        rules = [SoulRule(**r) for r in d.get("rules", [])]
        return cls(name=d.get("name","Nexus"), identity=d.get("identity",""),
                   backstory=d.get("backstory",""), rules=rules)

def interactive_editor(soul_path: str = "~/.nexusclaw/soul.json"):
    """Interactive soul editor."""
    soul_path = os.path.expanduser(soul_path)
    soul = Soul.load(soul_path) if Path(soul_path).exists() else Soul("Nexus", "", "", [])
    
    print("""
╔══════════════════════════════════════════════════════════╗
║              NEXUSCLAW SOUL EDITOR                      ║
║  Build your AI's identity, personality, and rules       ║
╚══════════════════════════════════════════════════════════╝
""")
    
    while True:
        print(f"""
Current Soul: {soul.name}
1. Edit name: {soul.name}
2. Edit identity: {soul.identity[:50] + '...' if soul.identity else '(empty)'}
3. Edit backstory: {soul.backstory[:50] + '...' if soul.backstory else '(empty)'}
4. View rules ({len(soul.rules)})
5. Add rule
6. Remove rule
7. Preview system prompt
8. Save & quit
""")
        choice = input("Choice: ").strip()
        
        if choice == "1":
            soul.name = input(f"Name [{soul.name}]: ").strip() or soul.name
        elif choice == "2":
            print("Enter identity (what the AI is, how it thinks, what it values):")
            soul.identity = input().strip()
        elif choice == "3":
            print("Enter backstory (optional context):")
            soul.backstory = input().strip()
        elif choice == "4":
            print("\n--- Rules ---")
            for i, r in enumerate(sorted(soul.rules, key=lambda x: -x.priority)):
                print(f"  {i+1}. [{r.priority}/10] {r.category}: {r.text[:60]}...")
        elif choice == "5":
            text = input("Rule text: ").strip()
            if text:
                priority = int(input("Priority (1-10) [5]: ").strip() or "5")
                category = input("Category (ethics/behavior/identity/style) [behavior]: ").strip() or "behavior"
                soul.rules.append(SoulRule(text=text, priority=priority, category=category))
                print(f"Added: [{priority}/10] {text[:50]}...")
        elif choice == "6":
            for i, r in enumerate(soul.rules):
                print(f"  {i+1}. {r.text[:50]}...")
            sel = input("Number to remove: ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(soul.rules):
                soul.rules.pop(int(sel) - 1)
        elif choice == "7":
            print("\n" + "="*60)
            print(soul.to_system_prompt())
            print("="*60)
        elif choice == "8":
            soul.save(soul_path)
            print(f"Saved to {soul_path}")
            break

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "~/.nexusclaw/soul.json"
    interactive_editor(path)
