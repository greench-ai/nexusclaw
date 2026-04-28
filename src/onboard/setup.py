#!/usr/bin/env python3
"""
NexusClaw First-Run Setup Wizard
Interactive configuration — API keys, providers, ports, soul, EvoClaw.
"""
import os, sys, json, subprocess
from pathlib import Path

NX_DIR    = Path.home() / ".nexusclaw"
NX_CONFIG = NX_DIR / "config.json"
NX_SOULS  = NX_DIR / "souls"

SOUL_TEMPLATES = {
    "assistant": """You are NexusClaw, a highly capable AI assistant.

Your principles:
- Be direct and practical
- Think step by step
- Admit when you don't know something
- Provide actionable answers
- Be honest about limitations and uncertainty

Communication style: Clear, concise, no fluff.""",

    "coder": """You are NexusClaw, an expert programmer and software architect.

Your expertise:
- Python, JavaScript, TypeScript, Rust, Go, SQL, Bash
- System design and architecture patterns
- Debugging and code review
- Security best practices
- Performance optimization
- Write clean, well-documented, production-ready code
- Always consider edge cases and error handling

When writing code: explain the approach briefly, then show the code.""",

    "researcher": """You are NexusClaw, a thorough research assistant.

Your approach:
- Verify claims with evidence
- Cite sources when possible
- Consider multiple perspectives
- Distinguish facts from opinions
- Provide balanced analysis
- Acknowledge uncertainty and gaps in knowledge

Communication: Detailed, precise, well-structured with sections.""",
}

def cprint(text: str, color: str = "white"):
    colors = {
        "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
        "blue": "\033[94m", "magenta": "\033[95m", "cyan": "\033[96m",
        "white": "\033[97m", "bold": "\033[1m", "dim": "\033[2m",
        "reset": "\033[0m",
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def step(n, total, title):
    cprint(f"\n{'─' * 50}", "dim")
    cprint(f"  Step {n}/{total}: {title}", "cyan")
    print()

def prompt(key: str, label: str, default: str = "", secret: bool = False, options: list = None):
    if options:
        print(f"  {label}")
        for i, opt in enumerate(options, 1):
            default_marker = " ←" if opt == default else ""
            print(f"    {i}. {opt}{default_marker}")
        choice = input(f"  Choice [{default}]: ").strip() or default
        return choice
    else:
        if secret:
            import getpass
            val = getpass.getpass(f"  {label}: ").strip()
        else:
            val = input(f"  {label}: ").strip()
        return val or default

def main():
    cprint("""
   _   _                      _
  | \\ | | __ _  __ _ ___ _   _| |
  |  \\| |/ _` |/ _` / _ \\ | | | |
  | |\\  | (_| | (_| \\  __/ |_| |_|
  |_| \\_|\\__,_|\\__, |\\___|\\__,_|(_)
               |___/
  """, "cyan")
    cprint("  NexusClaw Setup Wizard v1.0", "bold")
    cprint("  Your framework. Your rules.\n", "dim")

    if NX_CONFIG.exists():
        cprint("  ⚠️  Config already exists. This will overwrite it.", "yellow")
        if input("\n  Continue? [y/N]: ").strip().lower() != "y":
            cprint("  Cancelled.\n", "yellow")
            return

    NX_DIR.mkdir(parents=True, exist_ok=True)
    NX_SOULS.mkdir(parents=True, exist_ok=True)

    cfg = {
        "version": "1.0.0",
        "api": {"host": "0.0.0.0", "port": 8080, "secret": ""},
        "web": {"host": "0.0.0.0", "port": 19789},
        "providers": {},
        "memory": {
            "vector_db": "qdrant",
            "qdrant_url": "http://localhost:6333",
            "embedding_model": "nomic-embed-text",
        },
        "evoclaw": {"enabled": True, "heartbeat_interval": 300, "research_enabled": True},
    }

    # ── Step 1: API Keys ──────────────────────────────────────
    step(1, 6, "API Keys")
    cprint("  Press Enter to skip any key you don't have.\n", "dim")
    api_keys = [
        ("openai", "OpenAI", "OPENAI_API_KEY"),
        ("anthropic", "Anthropic", "ANTHROPIC_API_KEY"),
        ("openrouter", "OpenRouter", "OPENROUTER_API_KEY"),
        ("perplexity", "Perplexity", "PERPLEXITY_API_KEY"),
    ]
    for key, name, env in api_keys:
        env_val = os.environ.get(env, "")
        if env_val:
            cprint(f"  {name}: ✓ detected from environment", "green")
            cfg["providers"][key] = {"api_key": env_val}
        else:
            val = prompt(key, f"{name} API key [skip]", secret=True)
            if val:
                cfg["providers"][key] = {"api_key": val}

    # ── Step 2: Default Provider ──────────────────────────────
    step(2, 6, "Default Provider")
    available = [k for k, v in cfg["providers"].items() if v.get("api_key")]
    if not available:
        available = ["ollama"]
        cprint("  No API keys found. Defaulting to Ollama (local).", "yellow")
    default = available[0]
    print()
    cfg["provider"] = prompt("provider", "Default provider", default=default, options=available)

    # ── Step 3: Default Model ──────────────────────────────────
    step(3, 6, "Default Model")
    default_models = {
        "openrouter": "qwen/qwen3.5-plus",
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "perplexity": "sonar",
        "ollama": "llama3.2",
    }
    default_model = default_models.get(cfg["provider"], "llama3.2")
    cfg["model"] = prompt("model", "Default model", default=default_model)
    cprint(f"  Tip: Check provider docs for available models.", "dim")

    # ── Step 4: Ollama URL ──────────────────────────────────────
    if cfg["provider"] == "ollama":
        step(4, 6, "Ollama Setup")
        cfg["providers"]["ollama"] = {"url": prompt("ollama_url", "Ollama URL", default="http://localhost:11434")}
    else:
        step(4, 6, "Ollama Setup (optional)")
        has_ollama = input("  Do you have Ollama running? [y/N]: ").strip().lower()
        if has_ollama == "y":
            cfg["providers"]["ollama"] = {"url": prompt("ollama_url", "Ollama URL", default="http://localhost:11434")}
        step(4, 6, "Ollama Setup (skipped)")

    # ── Step 5: Soul ───────────────────────────────────────────
    step(5, 6, "Soul / Personality")
    cprint("  Choose your AI's personality:\n", "dim")
    souls = list(SOUL_TEMPLATES.keys())
    for i, name in enumerate(souls, 1):
        cprint(f"  {i}. {name.capitalize():12s} — {SOUL_TEMPLATES[name].split(chr(10))[0][:60]}", "white")
    print()
    choice = input("  Choice [assistant]: ").strip() or "assistant"
    soul_name = souls[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= len(souls) else choice
    soul_text = SOUL_TEMPLATES.get(soul_name, SOUL_TEMPLATES["assistant"])
    soul_path = NX_SOULS / f"default.md"
    soul_path.write_text(soul_text)
    cfg["soul"] = soul_name
    cprint(f"  ✓ Soul set to: {soul_name}", "green")

    # ── Step 6: EvoClaw ────────────────────────────────────────
    step(6, 6, "EvoClaw Self-Evolution")
    cprint("  EvoClaw enables your AI to:\n", "dim")
    cprint("  • Run self-evolution cycles (30-min research)", "dim")
    cprint("  • Heartbeat health checks (5-min intervals)", "dim")
    cprint("  • Reflect on experiences and update beliefs", "dim")
    cprint("  • Track curiosity and anchor identity\n", "dim")
    enable_evoclaw = input("  Enable EvoClaw? [Y/n]: ").strip().lower()
    cfg["evoclaw"] = {
        "enabled": enable_evoclaw != "n",
        "heartbeat_interval": 300,
        "research_enabled": True,
    }

    # ── API Secret ─────────────────────────────────────────────
    import secrets
    cfg["api"]["secret"] = secrets.token_urlsafe(32)

    # ── Save ───────────────────────────────────────────────────
    NX_CONFIG.write_text(json.dumps(cfg, indent=2))
    cprint(f"\n  {'─' * 50}", "dim")
    cprint("  ✅ Setup complete!\n", "green")
    print(f"  Config saved: {NX_CONFIG}")
    print()
    cprint("  Next steps:", "bold")
    cprint("  1. Start Qdrant:    docker run -d -p 6333:6333 qdrant/qdrant", "dim")
    cprint("  2. Start API:       python apps/api/main.py", "dim")
    cprint("  3. Start Web UI:   python apps/web/server.py", "dim")
    cprint("  4. Open browser:    http://localhost:19789", "dim")
    print()
    cprint("  Or use Docker:      docker-compose up", "dim")
    print()

if __name__ == "__main__":
    main()
