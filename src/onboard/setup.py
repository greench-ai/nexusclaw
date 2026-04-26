#!/usr/bin/env python3
"""
NexusClaw Setup Wizard — Full onboarding experience
Inspired by OpenClaw's onboarding philosophy:
User defines everything. No agents. No restrictions. No correct workflow.
"""
import os, sys, json
from pathlib import Path

WORKSPACE = Path(os.environ.get("NEXUS_WORKSPACE", "~/.nexusclaw")).expanduser()

PROVIDERS = {
    "local": {
        "name": "🖥️  Local (Ollama)",
        "desc": "Free, private, runs on your machine. No internet needed.",
        "models": ["llama3.2", "llama3.1", "mistral", "codellama", "qwen2.5", "phi3"],
        "requires": "ollama (free install: curl -fsSL https://ollama.com/install.sh | sh)",
        "env_var": "OLLAMA_URL",
        "default_url": "http://localhost:11434"
    },
    "openai": {
        "name": "🤖  OpenAI",
        "desc": "GPT-4o, o1, o3. Fast, reliable. Pay per use.",
        "models": ["gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini", "gpt-3.5-turbo"],
        "requires": "OPENAI_API_KEY (from platform.openai.com)",
        "env_var": "OPENAI_API_KEY"
    },
    "anthropic": {
        "name": "🧠  Anthropic",
        "desc": "Claude 3.5 Sonnet, 3.5 Haiku. Great reasoning.",
        "models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
        "requires": "ANTHROPIC_API_KEY (from console.anthropic.com)",
        "env_var": "ANTHROPIC_API_KEY"
    },
    "minimaxi": {
        "name": "⚡  Minimaxi",
        "desc": "M2.7-highspeed. Very fast, very cheap.",
        "models": ["MiniMax-M2.7-highspeed", "abab6.5s-chat"],
        "requires": "MINIMAXI_API_KEY (from platform.minimaxi.com)",
        "env_var": "MINIMAXI_API_KEY"
    },
    "openrouter": {
        "name": "🌐  OpenRouter",
        "desc": "100+ models via single API. Unified billing.",
        "models": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "google/gemini-pro"],
        "requires": "OPENROUTER_API_KEY (from openrouter.ai)",
        "env_var": "OPENROUTER_API_KEY"
    }
}

CHANNELS = {
    "cli": {"name": "⌨️  CLI/Terminal", "desc": "Direct command line. SSH anywhere."},
    "web": {"name": "🌍  Web UI (OpenRoom)", "desc": "Browser interface. Streaming, voice, code."},
    "telegram": {"name": "✈️  Telegram", "desc": "Chat from anywhere. Bot-based."},
    "discord": {"name": "🎮  Discord", "desc": "Server bot. Community integration."},
}

MEMORY_MODES = {
    "persistent": {"name": "🧠  Persistent", "desc": "Vector DB (Qdrant). Learns forever."},
    "session": {"name": "🔒  Session Only", "desc": "Zero persistence. Maximum privacy."},
    "hybrid": {"name": "⚖️  Hybrid", "desc": "Remember important, forget rest."}
}

SOUL_TYPES = {
    "blank": {"name": "🪞  Blank Slate", "desc": "Start fresh. Build your own identity."},
    "assistant": {"name": "🤝  Assistant", "desc": "Helpful, neutral, balanced."},
    "coder": {"name": "💻  Coder", "desc": "Technical, precise, productive."},
    "researcher": {"name": "🔬  Researcher", "desc": "Curious, analytical, thorough."}
}

def print_banner():
    print("""
\033[96m╔══════════════════════════════════════════════════════════╗
║                                                            ║
║   ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗          ║
║   ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝          ║
║   ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗          ║
║   ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║          ║
║   ██║ ╚████║███████╗██╔╝ ╚██╗╚██████╔╝███████║          ║
║   ╚═╝  ╚═══╝╚══════╝╚═╝   ╚═╝ ╚═════╝ ╚══════╝          ║
║                                                            ║
║          Your framework. Your rules. No restrictions.      ║
║                                                            ║
╚══════════════════════════════════════════════════════════╝\033[0m
""")

def ask_choice(options: dict, question: str, default: str = None) -> str:
    print(f"\n{question}")
    for k, v in options.items():
        print(f"  [{k}] {v['name']} — {v['desc']}")
    
    while True:
        choice = input(f"\nYour choice{(' (' + default + ')') if default else ''}: ").strip()
        if not choice and default:
            return default
        if choice in options:
            return choice
        print(f"Please enter one of: {', '.join(options.keys())}")

def ask_text(question: str, default: str = "", required: bool = False) -> str:
    while True:
        val = input(f"{question}{(' (' + default + ')') if default else ''}: ").strip()
        if not val:
            val = default
        if val or not required:
            return val
        print("This field is required.")

def run_wizard():
    """Full interactive setup wizard."""
    print_banner()
    
    print("\n\033[93mWelcome to NexusClaw Setup\033[0m")
    print("Answer a few questions to configure your framework.")
    print("You can always change these settings later.\n")
    
    config = {}
    
    # Provider
    print("\n\033[1mSTEP 1: AI Provider\033[0m")
    print("Choose how NexusClaw connects to AI models.\n")
    
    provider = ask_choice(PROVIDERS, "Which AI provider?", "local")
    config["provider"] = provider
    config["provider_name"] = PROVIDERS[provider]["name"]
    
    # Get API key if needed
    if provider != "local":
        env_var = PROVIDERS[provider]["env_var"]
        current_key = os.environ.get(env_var, "")
        key_hint = current_key[:8] + "..." if current_key else ""
        
        print(f"\n\033[93mNote: Set {env_var} environment variable for API access.\033[0m")
        print(f"Current: {key_hint or 'not set'}")
        
        key = input(f"Or enter key now (skip to use env var): ").strip()
        if key:
            config[f"{env_var.lower()}"] = key
    
    # Model
    models = PROVIDERS[provider]["models"]
    default_model = models[0]
    print(f"\nAvailable models: {', '.join(models)}")
    config["model"] = input(f"Model{(' (' + default_model + ')') if default_model else ''}: ").strip() or default_model
    
    # URL for local
    if provider == "local":
        config["ollama_url"] = input(f"Ollama URL{(' (http://localhost:11434)') if True else ''}: ").strip() or "http://localhost:11434"
    
    # Memory
    print("\n\033[1mSTEP 2: Memory\033[0m")
    print("How much does NexusClaw remember?")
    
    memory = ask_choice(MEMORY_MODES, "Memory mode?", "hybrid")
    config["memory_mode"] = memory
    
    # Channels
    print("\n\033[1mSTEP 3: Channels\033[0m")
    print("How do you want to interact with NexusClaw?")
    
    selected_channels = []
    for ch in CHANNELS:
        answer = input(f"Enable {CHANNELS[ch]['name']}? [y/N]: ").strip().lower()
        if answer == "y":
            selected_channels.append(ch)
    
    if not selected_channels:
        selected_channels = ["cli", "web"]
    
    config["channels"] = selected_channels
    
    # Soul
    print("\n\033[1mSTEP 4: Soul\033[0m")
    print("What personality should NexusClaw have?")
    
    soul = ask_choice(SOUL_TYPES, "Soul type?", "assistant")
    config["soul_type"] = soul
    
    # Workspace
    print("\n\033[1mSTEP 5: Workspace\033[0m")
    config["workspace"] = input(f"Workspace directory{(' (~/.nexusclaw)') if True else ''}: ").strip() or str(WORKSPACE)
    
    # Save config
    os.makedirs(config["workspace"], exist_ok=True)
    config_path = Path(config["workspace"]) / "config.json"
    
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    # Print summary
    print(f"""
\033[92m╔══════════════════════════════════════════════════════════╗
║                  CONFIGURATION COMPLETE                    ║
╠══════════════════════════════════════════════════════════╣
║  Provider:     {config['provider_name']:<40} ║
║  Model:       {config.get('model', default_model):<40} ║
║  Memory:       {MEMORY_MODES[memory]['name'].split()[0]:<40} ║
║  Channels:     {', '.join(selected_channels):<40} ║
║  Soul:         {SOUL_TYPES[soul]['name'].split()[0]:<40} ║
║  Workspace:     {config['workspace']:<40} ║
╚══════════════════════════════════════════════════════════╝\033[0m

Configuration saved to: {config_path}

\033[1mQuick Start:\033[0m
  CLI:       python3 ~/.nexusclaw/src/cli/main.py chat
  API:       python3 ~/.nexusclaw/apps/api/main.py
  Web UI:    python3 ~/.nexusclaw/apps/web/server.py

  Or use Docker:
  docker-compose up

\033[93mNeed help?\033[0m
  Docs: https://github.com/greench-ai/nexusclaw
  Issues: https://github.com/greench-ai/nexusclaw/issues
""")

if __name__ == "__main__":
    run_wizard()
