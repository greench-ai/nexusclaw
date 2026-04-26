"""
NexusClaw Onboarding Wizard
No agents. No restrictions. User builds what they need.
"""
from dataclasses import dataclass, field
from typing import Optional

PROVIDER_OPTIONS = {
    "1": {"name": "Local (Ollama)", "desc": "Free, private, runs on your machine", "icon": "🖥️"},
    "2": {"name": "OpenAI", "desc": "GPT-4o, o1, o3", "icon": "🤖"},
    "3": {"name": "Anthropic", "desc": "Claude 3.5, 3.7", "icon": "🧠"},
    "4": {"name": "Minimaxi", "desc": "M2.7-highspeed, fast + cheap", "icon": "⚡"},
    "5": {"name": "OpenRouter", "desc": "100+ models, unified API", "icon": "🌐"},
    "6": {"name": "Custom API", "desc": "Any OpenAI-compatible endpoint", "icon": "🔧"},
}

CHANNEL_OPTIONS = {
    "1": {"name": "Terminal/CLI", "desc": "Direct command line", "icon": "⌨️"},
    "2": {"name": "Telegram", "desc": "Chat from anywhere", "icon": "✈️"},
    "3": {"name": "Discord", "desc": "Server bot", "icon": "🎮"},
    "4": {"name": "Slack", "desc": "Team workspace", "icon": "💬"},
    "5": {"name": "Web UI", "desc": "Browser interface", "icon": "🌍"},
}

MEMORY_OPTIONS = {
    "1": {"name": "Full persistence (Qdrant)", "desc": "Long-term vector memory, learns forever", "icon": "🧠"},
    "2": {"name": "Session only", "desc": "Forget after close, max privacy", "icon": "🔒"},
    "3": {"name": "Hybrid", "desc": "Remember important, forget rest", "icon": "⚖️"},
}

SOUL_OPTIONS = {
    "1": {"name": "Blank slate", "desc": "Start fresh, build your own soul", "icon": "🪞"},
    "2": {"name": "Assistant template", "desc": "Helpful, neutral, balanced", "icon": "🤝"},
    "3": {"name": "Coder template", "desc": "Technical, precise, productivity", "icon": "💻"},
    "4": {"name": "Researcher template", "desc": "Curious, thorough, analytical", "icon": "🔬"},
    "5": {"name": "Import existing soul", "desc": "Load from file or URL", "icon": "📥"},
}

@dataclass
class NexusConfig:
    """User's NexusClaw configuration. Built during onboarding."""
    provider: str = ""
    provider_key: str = ""
    provider_base_url: str = ""
    model: str = ""
    channels: list[str] = field(default_factory=list)
    memory_mode: str = "hybrid"
    soul_type: str = "blank"
    soul_content: str = ""
    workspace: str = "~/.nexusclaw"
    install_mode: str = "cli"  # cli, systemd, docker
    
    def save(self, path: str = "~/.nexusclaw/config.json"):
        import json, os
        path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)
    
    @classmethod
    def load(cls, path: str = "~/.nexusclaw/config.json"):
        import json, os
        path = os.path.expanduser(path)
        if os.path.exists(path):
            with open(path) as f:
                return cls(**json.load(f))
        return None

def run_wizard():
    """Interactive onboarding wizard."""
    print("""
╔══════════════════════════════════════════════════════════╗
║                    NEXUSCLAW                            ║
║         Your framework. Your rules. No restrictions.    ║
╚══════════════════════════════════════════════════════════╝
""")
    
    config = NexusConfig()
    
    # Step 1: Provider
    print("STEP 1: Choose your AI provider")
    print("(You can always change this later)\n")
    for k, v in PROVIDER_OPTIONS.items():
        print(f"  [{k}] {v['icon']} {v['name']} — {v['desc']}")
    
    choice = input("\nYour choice (1-6): ").strip()
    provider_data = PROVIDER_OPTIONS.get(choice, PROVIDER_OPTIONS["1"])
    config.provider = provider_data["name"]
    
    if config.provider == "Custom API":
        config.provider_base_url = input("API base URL: ").strip()
        config.model = input("Model name: ").strip()
    elif config.provider != "Local (Ollama)":
        key = input(f"\n{config.provider} API key: ").strip()
        config.provider_key = key
    
    # Step 2: Memory
    print("\n\nSTEP 2: Memory & Learning")
    print("(How much does NexusClaw remember across sessions?)\n")
    for k, v in MEMORY_OPTIONS.items():
        print(f"  [{k}] {v['icon']} {v['name']} — {v['desc']}")
    
    choice = input("\nYour choice (1-3): ").strip()
    config.memory_mode = MEMORY_OPTIONS.get(choice, {"name": "hybrid"})["name"].lower()
    
    # Step 3: Soul
    print("\n\nSTEP 3: Your Soul")
    print("(The personality and rules that define NexusClaw)\n")
    for k, v in SOUL_OPTIONS.items():
        print(f"  [{k}] {v['icon']} {v['name']} — {v['desc']}")
    
    choice = input("\nYour choice (1-5): ").strip()
    config.soul_type = SOUL_OPTIONS.get(choice, SOUL_OPTIONS["1"])["name"].lower()
    
    # Summary
    print("""
╔══════════════════════════════════════════════════════════╗
║                   CONFIGURATION COMPLETE                  ║
╠══════════════════════════════════════════════════════════╣""")
    print(f"║  Provider:     {config.provider:<40} ║")
    print(f"║  Memory:       {config.memory_mode:<40} ║")
    print(f"║  Soul:         {config.soul_type:<40} ║")
    print("""╚══════════════════════════════════════════════════════════╝
    
NexusClaw is ready. Start with: nexusclaw chat
""")
    
    config.save()
    return config

if __name__ == "__main__":
    run_wizard()
