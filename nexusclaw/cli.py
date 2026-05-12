"""NexusClaw CLI — onboard, setup, start, stop, status."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

console = Console()


# ── Provider catalogue ────────────────────────────────────────────────────────
PROVIDER_CHOICES = {
    "1": ("ollama",      "http://localhost:11434/v1"),
    "2": ("openrouter",   "https://openrouter.ai/api/v1"),
    "3": ("deepseek",     "https://api.deepseek.com/v1"),
    "4": ("groq",         "https://api.groq.com/openai/v1"),
    "5": ("dashscope",    "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    "6": ("openai",       "https://api.openai.com/v1"),
    "7": ("anthropic",    "https://api.anthropic.com/v1"),
}

PROVIDER_LABELS = {
    "ollama":    "Ollama (local, free — no API key needed)",
    "openrouter": "OpenRouter (100+ models, DeepSeek/Qwen/Claude…)",
    "deepseek":  "DeepSeek (fast, cheap, excellent reasoning)",
    "groq":      "Groq (blazing fast, free tier)",
    "dashscope": "DashScope / Alibaba Qwen (powerful Chinese models)",
    "openai":    "OpenAI (GPT-4o, GPT-4o mini)",
    "anthropic": "Anthropic (Claude 3.5 Sonnet, Opus)",
}

PROVIDER_MODELS = {
    "ollama":     ["llama3", "llama3.2", "mistral", "codellama", "qwen2.5"],
    "openrouter": ["deepseek/deepseek-chat-v3.1", "qwen/qwen3-8b", "qwen/qwen3-32b",
                   "google/gemma-3-27b-it", "anthropic/claude-3-haiku",
                   "nvidia/nemotron-3-super-120b-a12b:free"],
    "deepseek":   ["deepseek-chat", "deepseek-coder"],
    "groq":       ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    "dashscope":  ["qwen-plus", "qwen-turbo", "qwen-max"],
    "openai":     ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    "anthropic":  ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
}

PROVIDER_KEY_ENV = {
    "ollama":     None,
    "openrouter": "OPENROUTER_API_KEY",
    "deepseek":   "DEEPSEEK_API_KEY",
    "groq":       "GROQ_API_KEY",
    "dashscope":  "DASHSCOPE_API_KEY",
    "openai":     "OPENAI_API_KEY",
    "anthropic":  "ANTHROPIC_API_KEY",
}

PROVIDER_NEEDS_KEY = {
    "ollama": False,
    "openrouter": True,
    "deepseek": True,
    "groq": True,
    "dashscope": True,
    "openai": True,
    "anthropic": True,
}


def get_config_path() -> Path:
    p = Path.home() / ".nexusclaw" / "config.yaml"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_config():
    path = get_config_path()
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config(data: dict) -> None:
    path = get_config_path()
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


# ── Click commands ────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0")
def main():
    """NexusClaw — Direct provider AI chat. No LiteLLM."""
    pass


@main.command()
def onboard():
    """Interactive first-run setup wizard — asks provider, API key, model."""
    lock = Path.home() / ".nexusclaw" / ".onboard.lock"
    if lock.exists():
        console.print("[yellow]Onboard is already running (lockfile exists). "
                      "Remove ~/.nexusclaw/.onboard.lock if this is an error.[/yellow]")
        return

    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text(str(os.getpid()))
    try:
        _onboard_inner()
    finally:
        lock.unlink(missing_ok=True)


def _onboard_inner():
    console.print(Panel.fit(
        "[bold green]⚡ NexusClaw Onboarding[/bold green]\n"
        "Let's get you set up in under 2 minutes.",
        border_style="green",
    ))
    console.print()

    # ── 1. Pick provider ────────────────────────────────────────────
    console.print("[bold]Step 1 — Choose your provider[/bold]")
    console.print("Type the number (or name) of your provider:\n")
    for num, (pid, _) in PROVIDER_CHOICES.items():
        label = PROVIDER_LABELS.get(pid, pid)
        console.print(f"  [bold]{num}[/bold]. {label}")

    console.print()
    raw = Prompt.ask(
        "[bold]Provider[/bold] (1-7, or name)",
        default="2",
    ).strip()

    # Resolve provider id
    if raw in PROVIDER_CHOICES:
        provider_id, base_url = PROVIDER_CHOICES[raw]
    elif raw in PROVIDER_LABELS:
        provider_id = raw
        base_url = None
    else:
        console.print(f"[yellow]Unknown provider '{raw}' — defaulting to OpenRouter[/yellow]")
        provider_id, base_url = "openrouter", "https://openrouter.ai/api/v1"

    if provider_id != "ollama" and base_url is None:
        base_url = {
            "openrouter": "https://openrouter.ai/api/v1",
            "deepseek":   "https://api.deepseek.com/v1",
            "groq":       "https://api.groq.com/openai/v1",
            "dashscope":  "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "openai":     "https://api.openai.com/v1",
            "anthropic":  "https://api.anthropic.com/v1",
        }.get(provider_id, "")

    console.print(f"  → [green]{provider_id}[/green]\n")

    # ── 2. API key ─────────────────────────────────────────────────
    api_key = ""
    key_env = PROVIDER_KEY_ENV.get(provider_id)
    existing_key = os.environ.get(key_env or "")

    if PROVIDER_NEEDS_KEY.get(provider_id, True):
        if existing_key:
            console.print(f"[green]✓[/green] Found [dim]{key_env}[/dim] in environment.")
            if Confirm.ask("Use it?", default=True):
                api_key = existing_key

        if not api_key:
            console.print(f"\n[bold]Step 2 — API key for {provider_id}[/bold]")
            console.print("Paste your API key (stored in [dim]~/.nexusclaw/config.yaml[/dim]).")
            console.print("Press Enter to skip, or type your key and press Enter.")
            api_key = Prompt.ask(f"[bold]API Key[/bold] (Enter to skip)").strip()
    else:
        console.print(f"[dim]No API key needed for {provider_id}.[/dim]\n")

    # ── 3. Model ───────────────────────────────────────────────────
    console.print(f"\n[bold]Step 3 — Pick a model for {provider_id}[/bold]")
    models = PROVIDER_MODELS.get(provider_id, [])
    default_model = models[0] if models else ""

    if models:
        console.print("Available models:")
        for m in models:
            console.print(f"  • [dim]{m}[/dim]")
        console.print()

    model = Prompt.ask(
        "[bold]Model[/bold]",
        default=default_model,
    ).strip()

    # ── 4. Save config ──────────────────────────────────────────────
    config = load_config()
    config.setdefault("version", "1.0.0")

    if not api_key and not models:
        console.print("\n[yellow]No API key and no model — config not saved.[/yellow]")
        return

    # Build provider config
    provider_cfg = {
        "name": provider_id,
        "base_url": base_url,
        "models": [model] if model else [],
        "enabled": True,
    }
    if api_key:
        provider_cfg["api_key"] = api_key

    config["providers"] = {provider_id: provider_cfg}
    config["default_provider"] = provider_id
    config["default_model"] = f"{provider_id}/{model}" if model else ""

    save_config(config)

    # ── Done ────────────────────────────────────────────────────────
    console.print()
    console.print(Panel.fit(
        f"[bold green]✓ You're all set![/bold green]\n\n"
        f"Config written to [dim]{get_config_path()}[/dim]\n"
        f"Default provider: [bold]{provider_id}[/bold]  |  Model: [bold]{model}[/bold]",
        border_style="green",
    ))
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print("  1. [dim]curl -fsSL https://nexusclaw.ai/install.sh | bash[/dim]  (if not already)")
    console.print("  2. [dim]nexusclaw start[/dim]  — start the API server")
    console.print("  3. Open [dim]http://localhost:14300[/dim] in your browser")
    console.print()


@main.command()
def setup():
    """First-run setup wizard (alias for onboard)."""
    onboard()


@main.command()
def status():
    """Show NexusClaw service status."""
    config = load_config()
    cfg_path = get_config_path()
    providers = config.get("providers", {})
    default = config.get("default_provider", "none")

    console.print(Panel.fit(
        f"[bold green]⚡ NexusClaw Status[/bold green]",
        border_style="green",
    ))
    console.print(f"\nConfig: [dim]{cfg_path}[/dim]")
    console.print(f"Default provider: [bold]{default}[/bold]")
    if providers:
        console.print("Providers:")
        for pid, pdata in providers.items():
            models = pdata.get("models", [])
            has_key = bool(pdata.get("api_key"))
            key_mark = "[green]✓ key[/green]" if has_key else "[dim]no key[/dim]"
            console.print(f"  • [bold]{pid}[/bold]  {key_mark}  models: [dim]{', '.join(models[:3])}[/dim]")
    else:
        console.print("\n[yellow]No providers configured — run [dim]nexusclaw onboard[/dim] first.[/yellow]")


@main.command()
def start():
    """Print instructions to start NexusClaw."""
    console.print(Panel.fit(
        "[bold green]⚡ Start NexusClaw[/bold green]",
        border_style="green",
    ))
    console.print("""
Make sure Docker is running, then:

    cd /home/greench/nexusclaw
    docker-compose up -d

Or run the API directly:

    cd /home/greench/nexusclaw
    pip install -e .
    python -m nexusclaw.api

Then open:  [bold]http://localhost:14300[/bold]
""")


if __name__ == "__main__":
    main()
