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
from rich.style import Style

console = Console()

# ── Paths ───────────────────────────────────────────────────────────────────

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


# ── Full provider catalogue (matches OpenClaw's provider list) ───────────────

PROVIDERS = {
    # Format: "visible_name": {"id": "...", "key_env": "...", "key_prefix": "...",
    #                           "default_model": "...", "model_list": [...],
    #                           "auth_method": "api-key" | "env-var" | "none"}
    "Alibaba Cloud Model Studio": {
        "id": "alibaba",
        "key_env": "ALIBABA_DASHSCOPE_API_KEY",
        "key_prefix": "sk-",
        "default_model": "qwen-plus",
        "model_list": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-long"],
        "auth_method": "api-key",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_mode": "openai-chat",
    },
    "Anthropic": {
        "id": "anthropic",
        "key_env": "ANTHROPIC_API_KEY",
        "key_prefix": "sk-ant-",
        "default_model": "claude-3-5-sonnet-20241022",
        "model_list": [
            "claude-3-5-sonnet-20241022", "claude-3-opus-20240229",
            "claude-3-haiku-20240307", "claude-sonnet-4-20250514",
        ],
        "auth_method": "api-key",
        "base_url": "https://api.anthropic.com/v1",
        "api_mode": "anthropic-chat",
    },
    "BytePlus": {
        "id": "byteplus",
        "key_env": "BYTEPLUS_API_KEY",
        "key_prefix": "bp-",
        "default_model": "doubao-pro-32k",
        "model_list": ["doubao-pro-32k", "doubao-lite-32k"],
        "auth_method": "api-key",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_mode": "openai-chat",
    },
    "Chutes": {
        "id": "chutes",
        "key_env": "CHUTES_API_KEY",
        "key_prefix": "ck-",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "model_list": ["meta-llama/Llama-3.3-70B-Instruct", "Qwen/Qwen2.5-72B-Instruct"],
        "auth_method": "api-key",
        "base_url": "https://api.chutes.ai/v1",
        "api_mode": "openai-chat",
    },
    "Cloudflare AI Gateway": {
        "id": "cloudflare",
        "key_env": "CLOUDFLARE_AI_GATEWAY_API_KEY",
        "key_prefix": "",
        "default_model": "@cf/meta/llama-3.1-8b-instruct",
        "model_list": ["@cf/meta/llama-3.1-8b-instruct", "@cf/meta/llama-3.3-70b-instruct-fastsys"],
        "auth_method": "api-key",
        "base_url": "https://api.cloudflare.com/client/v4/ai",
        "api_mode": "openai-chat",
    },
    "Copilot": {
        "id": "copilot",
        "key_env": "GITHUB_TOKEN",
        "key_prefix": "ghp_",
        "default_model": "gpt-4o",
        "model_list": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "auth_method": "api-key",
        "base_url": "https://api.githubcopilot.com/chat/completions",
        "api_mode": "openai-chat",
    },
    "Custom Provider": {
        "id": "custom",
        "key_env": None,
        "key_prefix": None,
        "default_model": "",
        "model_list": [],
        "auth_method": "custom",
        "base_url": "",
        "api_mode": "auto-detect",
        "is_custom": True,
    },
    "Google": {
        "id": "google",
        "key_env": "GOOGLE_API_KEY",
        "key_prefix": "AIza",
        "default_model": "gemini-2.5-flash",
        "model_list": [
            "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash",
            "gemini-1.5-flash", "gemini-1.5-pro",
        ],
        "auth_method": "api-key",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "api_mode": "openai-chat",
    },
    "Hugging Face": {
        "id": "huggingface",
        "key_env": "HF_TOKEN",
        "key_prefix": "hf_",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "model_list": [
            "meta-llama/Llama-3.3-70B-Instruct", "Qwen/Qwen2.5-72B-Instruct",
            "mistralai/Mistral-Nemo-Instruct-12B",
        ],
        "auth_method": "api-key",
        "base_url": "https://api-inference.huggingface.co/v1",
        "api_mode": "openai-chat",
    },
    "Kilo Gateway": {
        "id": "kilo",
        "key_env": "KILO_API_KEY",
        "key_prefix": "km-",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "model_list": ["meta-llama/Llama-3.3-70B-Instruct"],
        "auth_method": "api-key",
        "base_url": "https://api.kilocount.com/v1",
        "api_mode": "openai-chat",
    },
    "Kimi Code": {
        "id": "kimi-code",
        "key_env": "KIMI_CODE_API_KEY",
        "key_prefix": "kcm-",
        "default_model": "Kimi-Code-Space",
        "model_list": ["Kimi-Code-Space"],
        "auth_method": "api-key",
        "base_url": "https://code.moonshot.cn/v1",
        "api_mode": "openai-chat",
    },
    "LiteLLM": {
        "id": "litellm",
        "key_env": "LITELLM_MASTER_KEY",
        "key_prefix": "sk-",
        "default_model": "gpt-4o",
        "model_list": ["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-2.5-flash"],
        "auth_method": "api-key",
        "base_url": "http://localhost:4000",
        "api_mode": "openai-chat",
    },
    "MiniMax": {
        "id": "minimax",
        "key_env": "MINIMAX_API_KEY",
        "key_prefix": "sk-cp-",
        "default_model": "MiniMax-Text-01",
        "model_list": ["MiniMax-Text-01", "abab6.5s-chat"],
        "auth_method": "api-key",
        "base_url": "https://api.minimax.chat/v1",
        "api_mode": "openai-chat",
    },
    "Mistral AI": {
        "id": "mistral",
        "key_env": "MISTRAL_API_KEY",
        "key_prefix": "m-",
        "default_model": "mistral-large-latest",
        "model_list": ["mistral-large-latest", "mistral-small-latest", "mistral-nemo-instruct-2407"],
        "auth_method": "api-key",
        "base_url": "https://api.mistral.ai/v1",
        "api_mode": "openai-chat",
    },
    "Moonshot AI (Kimi K2.5)": {
        "id": "moonshot",
        "key_env": "MOONSHOT_API_KEY",
        "key_prefix": "moonshot-",
        "default_model": "moonshot-v1-8k",
        "model_list": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "auth_method": "api-key",
        "base_url": "https://api.moonshot.cn/v1",
        "api_mode": "openai-chat",
    },
    "Ollama": {
        "id": "ollama",
        "key_env": None,
        "key_prefix": None,
        "default_model": "llama3",
        "model_list": ["llama3", "llama3.2", "mistral", "codellama", "qwen2.5", "deepseek-r1"],
        "auth_method": "none",
        "base_url": "http://localhost:11434/v1",
        "api_mode": "openai-chat",
    },
    "OpenAI": {
        "id": "openai",
        "key_env": "OPENAI_API_KEY",
        "key_prefix": "sk-",
        "default_model": "gpt-4o",
        "model_list": [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo",
            "o1", "o1-mini", "o1-preview", "o3-mini",
        ],
        "auth_method": "api-key",
        "base_url": "https://api.openai.com/v1",
        "api_mode": "openai-chat",
    },
    "OpenCode": {
        "id": "opencode",
        "key_env": "OPENCODE_API_KEY",
        "key_prefix": "sk-oc-",
        "default_model": "opencode",
        "model_list": ["opencode"],
        "auth_method": "api-key",
        "base_url": "https://api.opencode.ai/v1",
        "api_mode": "openai-chat",
    },
    "OpenRouter": {
        "id": "openrouter",
        "key_env": "OPENROUTER_API_KEY",
        "key_prefix": "sk-or-v1-",
        "default_model": "deepseek/deepseek-chat-v3.1",
        "model_list": [
            "deepseek/deepseek-chat-v3.1", "qwen/qwen3-8b", "qwen/qwen3-32b",
            "google/gemma-3-27b-it", "anthropic/claude-3-haiku",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "meta-llama/Llama-3.3-70B-Instruct",
        ],
        "auth_method": "api-key",
        "base_url": "https://openrouter.ai/api/v1",
        "api_mode": "openai-chat",
    },
    "Qianfan": {
        "id": "qianfan",
        "key_env": "QIANFAN_API_KEY",
        "key_prefix": "",
        "default_model": "ernie-4.0-8k",
        "model_list": ["ernie-4.0-8k", "ernie-3.5-8k", "ernie-speed-128k"],
        "auth_method": "api-key",
        "base_url": "https://qianfan.baidubce.com/v2",
        "api_mode": "openai-chat",
    },
    "Qwen": {
        "id": "qwen",
        "key_env": "DASHSCOPE_API_KEY",
        "key_prefix": "sk-",
        "default_model": "qwen-plus",
        "model_list": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-long"],
        "auth_method": "api-key",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_mode": "openai-chat",
    },
    "SGLang": {
        "id": "sglang",
        "key_env": "SGLANG_API_KEY",
        "key_prefix": "sk-",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "model_list": ["meta-llama/Llama-3.3-70B-Instruct", "Qwen/Qwen2.5-72B-Instruct"],
        "auth_method": "api-key",
        "base_url": "http://localhost:30000/v1",
        "api_mode": "openai-chat",
    },
    "Synthetic": {
        "id": "synthetic",
        "key_env": "SYNTHETIC_API_KEY",
        "key_prefix": "",
        "default_model": "synthetic",
        "model_list": ["synthetic"],
        "auth_method": "api-key",
        "base_url": "http://localhost:8080/v1",
        "api_mode": "openai-chat",
    },
    "Together AI": {
        "id": "together",
        "key_env": "TOGETHER_API_KEY",
        "key_prefix": "sk-",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "model_list": [
            "meta-llama/Llama-3.3-70B-Instruct", "Qwen/Qwen2.5-72B-Instruct",
            "mistralai/Mistral-Nemo-Instruct-12B",
        ],
        "auth_method": "api-key",
        "base_url": "https://api.together.xyz/v1",
        "api_mode": "openai-chat",
    },
    "Venice AI": {
        "id": "venice",
        "key_env": "VENICE_API_KEY",
        "key_prefix": "venice-",
        "default_model": "llama-3.3-70B-Instruct",
        "model_list": ["llama-3.3-70B-Instruct", "Qwen2.5-72B-Instruct"],
        "auth_method": "api-key",
        "base_url": "https://api.venice.ai/api/v1",
        "api_mode": "openai-chat",
    },
    "Vercel AI Gateway": {
        "id": "vercel",
        "key_env": "VERCEL_AI_GATEWAY_API_KEY",
        "key_prefix": "",
        "default_model": "gpt-4o",
        "model_list": ["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-2.5-flash"],
        "auth_method": "api-key",
        "base_url": "https://gateway.ai.cloudflare.com/account/gateway",
        "api_mode": "openai-chat",
    },
    "vLLM": {
        "id": "vllm",
        "key_env": "VLLM_API_KEY",
        "key_prefix": "sk-",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct",
        "model_list": ["meta-llama/Llama-3.3-70B-Instruct", "Qwen/Qwen2.5-72B-Instruct"],
        "auth_method": "api-key",
        "base_url": "http://localhost:8000/v1",
        "api_mode": "openai-chat",
    },
    "Volcano Engine": {
        "id": "volcano",
        "key_env": "VOLC_API_KEY",
        "key_prefix": "",
        "default_model": "doubao-pro-32k",
        "model_list": ["doubao-pro-32k", "doubao-lite-32k"],
        "auth_method": "api-key",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_mode": "openai-chat",
    },
    "xAI (Grok)": {
        "id": "xai",
        "key_env": "XAI_API_KEY",
        "key_prefix": "xai-",
        "default_model": "grok-2",
        "model_list": ["grok-2", "grok-2-mini", "grok-beta"],
        "auth_method": "api-key",
        "base_url": "https://api.x.ai/v1",
        "api_mode": "openai-chat",
    },
    "Xiaomi": {
        "id": "xiaomi",
        "key_env": "XIAOMI_API_KEY",
        "key_prefix": "",
        "default_model": "xlite-large",
        "model_list": ["xlite-large", "xlite-large-rag",
        ],
        "auth_method": "api-key",
        "base_url": "https://api.xiaomi.com/v2",
        "api_mode": "openai-chat",
    },
    "Z.AI": {
        "id": "zai",
        "key_env": "Z_API_KEY",
        "key_prefix": "z-",
        "default_model": "Qwen/Qwen2.5-72B-Instruct",
        "model_list": ["Qwen/Qwen2.5-72B-Instruct", "meta-llama/Llama-3.3-70B-Instruct"],
        "auth_method": "api-key",
        "base_url": "https://api.z-ai.com/v1",
        "api_mode": "openai-chat",
    },
}

PROVIDER_ORDER = [
    "Alibaba Cloud Model Studio",
    "Anthropic",
    "BytePlus",
    "Chutes",
    "Cloudflare AI Gateway",
    "Copilot",
    "Custom Provider",
    "Google",
    "Hugging Face",
    "Kilo Gateway",
    "Kimi Code",
    "LiteLLM",
    "MiniMax",
    "Mistral AI",
    "Moonshot AI (Kimi K2.5)",
    "Ollama",
    "OpenAI",
    "OpenCode",
    "OpenRouter",
    "Qianfan",
    "Qwen",
    "SGLang",
    "Synthetic",
    "Together AI",
    "Venice AI",
    "Vercel AI Gateway",
    "vLLM",
    "Volcano Engine",
    "xAI (Grok)",
    "Xiaomi",
    "Z.AI",
]


# ── Web search providers ─────────────────────────────────────────────────────

SEARCH_PROVIDERS = {
    "Brave Search": {
        "id": "brave",
        "key_env": "BRAVE_API_KEY",
        "key_prefix": "BSA",
        "docs_url": "https://api.search.brave.com/app/",
    },
    "Google Custom Search": {
        "id": "google",
        "key_env": "GOOGLE_API_KEY",
        "key_prefix": "AIza",
        "docs_url": "https://developers.google.com/custom-search",
    },
    "SerpAPI": {
        "id": "serpapi",
        "key_env": "SERPAPI_API_KEY",
        "key_prefix": "",
        "docs_url": "https://serpapi.com/",
    },
    "Serper": {
        "id": "serper",
        "key_env": "SERPER_API_KEY",
        "key_prefix": "",
        "docs_url": "https://serper.dev/",
    },
    "Tavily": {
        "id": "tavily",
        "key_env": "TAVILY_API_KEY",
        "key_prefix": "tvly-",
        "docs_url": "https://tavily.com/",
    },
}


# ── Click commands ────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="1.0.0")
def main():
    """NexusClaw — Direct provider AI chat. No LiteLLM."""
    pass


@main.command()
def onboard():
    """Interactive first-run setup wizard."""
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
    _print_banner()

    # ── 1. Security warning ─────────────────────────────────────────
    console.print(Panel.fit(
        "[bold red]⚠ Security warning — please read.[/bold red]\n\n"
        "NexusClaw is a hobby project and still in beta. Expect sharp edges.\n"
        "By default, NexusClaw is a personal agent: one trusted operator boundary.\n"
        "This bot can read files and run actions if tools are enabled.\n"
        "A bad prompt can trick it into doing unsafe things.\n\n"
        "NexusClaw is not a hostile multi-tenant boundary by default.\n"
        "If multiple users can message one tool-enabled agent, they share that\n"
        "delegated tool authority.\n\n"
        "[bold]Recommended baseline:[/bold]\n"
        "  • Pairing/allowlists + mention gating.\n"
        "  • Multi-user/shared inbox: split trust boundaries.\n"
        "  • Sandbox + least-privilege tools.\n"
        "  • Keep secrets out of the agent's reachable filesystem.\n"
        "  • Use the strongest available model for any bot with tools or\n"
        "    untrusted inboxes.\n\n"
        "[dim]Run regularly: nexusclaw security audit --deep[/dim]",
        border_style="red",
    ))
    console.print()

    if not Confirm.ask(
        "[bold]I understand this is personal-by-default and shared/multi-user "
        "use requires lock-down. Continue?[/bold]",
        default=True,
    ):
        console.print("[yellow]Onboarding cancelled.[/yellow]")
        return

    # ── 2. Config detection ────────────────────────────────────────
    config = load_config()
    existing = bool(config)

    if existing:
        workspace = config.get("workspace", "~/.nexusclaw/workspace")
        model = config.get("default_model", "not set")
        gateway_mode = config.get("gateway", {}).get("mode", "local")
        gateway_port = config.get("gateway", {}).get("port", 19789)
        gateway_bind = config.get("gateway", {}).get("bind", "loopback")

        console.print(Panel(
            f"[bold]Existing config detected[/bold]\n\n"
            f"workspace: [dim]{workspace}[/dim]\n"
            f"model: [dim]{model}[/dim]\n"
            f"gateway.mode: [dim]{gateway_mode}[/dim]\n"
            f"gateway.port: [dim]{gateway_port}[/dim]\n"
            f"gateway.bind: [dim]{gateway_bind}[/dim]",
            title="Detected",
            border_style="yellow",
        ))
        console.print()
        console.print("[bold]Config handling[/bold]")
        console.print("  [bold]1.[/bold] Update values")
        console.print("  [bold]2.[/bold] Keep current settings")
        raw = Prompt.ask("Choice", default="2").strip()
        if raw == "2":
            # QuickStart — just ask model/search, skip gateway config
            _quickstart_flow(config)
            return

    # ── 3. Full provider flow ─────────────────────────────────────
    _full_onboard_flow(config)


def _quickstart_flow(config: dict):
    """QuickStart: keep gateway settings, just configure model + search."""
    console.print(Panel.fit(
        "[bold]QuickStart[/bold]\n\n"
        "Keeping your current gateway settings.\n"
        "Just configuring the model and search provider.",
        border_style="green",
    ))
    console.print()

    # If we already have a model saved, offer to keep it
    current_model = config.get("default_model", "")
    if current_model:
        console.print(f"Current model: [dim]{current_model}[/dim]")
        if Confirm.ask("Keep this model?", default=True):
            _ask_websearch(config)
            return

    # Otherwise do model selection
    _ask_model(config, skip_gateway=True)


def _full_onboard_flow(config: dict):
    """Full onboarding: gateway + model + search."""
    _ask_model(config, skip_gateway=False)


def _ask_model(config: dict, skip_gateway: bool):
    """Ask for model/auth provider."""
    console.print()
    console.print("[bold]Model/auth provider[/bold]\n")

    # Show providers in two-column-ish layout
    for i, name in enumerate(PROVIDER_ORDER):
        idx = i + 1
        if idx <= 9:
            console.print(f"  [bold]{idx}.[/bold] {name}")
        else:
            # For readability, just show after initial batch
            pass

    # Show remaining without numbers for now (too many to number cleanly)
    console.print("  [dim]...[/dim]")
    console.print()
    console.print("  [bold]Skip for now[/bold] — configure model later")
    console.print()

    raw = Prompt.ask(
        "[bold]Model/auth provider[/bold]",
        default="Skip for now",
    ).strip()

    # Find selected provider
    selected_name = None
    for name in PROVIDER_ORDER:
        if name.lower() == raw.lower() or raw == str(PROVIDER_ORDER.index(name) + 1):
            selected_name = name
            break

    if raw.lower() in ("skip for now", "skip"):
        console.print("[dim]Skipping model setup.[/dim]")
        _ask_websearch(config)
        return

    if selected_name == "Custom Provider":
        _setup_custom_provider(config)
        return

    if selected_name:
        _setup_builtin_provider(selected_name, config)
    else:
        console.print("[yellow]No valid provider selected — cancelled.[/yellow]")


def _setup_builtin_provider(provider_name: str, config: dict):
    prov = PROVIDERS[provider_name]
    provider_id = prov["id"]

    console.print(f"\n[bold]Provider:[/bold] {provider_name}")

    # Auth
    api_key = ""
    if prov["auth_method"] == "api-key":
        key_env = prov["key_env"]
        existing_key = os.environ.get(key_env or "", "")
        if existing_key:
            console.print(f"[green]✓[/green] Found [dim]{key_env}[/dim] in environment.")
            if Confirm.ask("Use it?", default=True):
                api_key = existing_key

        if not api_key:
            console.print(f"\n[bold]Enter {provider_name} API key[/bold]")
            if prov.get("key_prefix"):
                console.print(f"[dim]Prefix: [bold]{prov['key_prefix']}[/bold]...[/dim]")
            console.print(f"Get it from: [dim]{prov.get('docs_url', '')}[/dim]")
            api_key = Prompt.ask("[bold]API Key[/bold]").strip()

    # Model
    model_list = prov.get("model_list", [])
    default_model = prov.get("default_model", "")
    console.print(f"\n[bold]Model[/bold]")
    if model_list:
        for m in model_list[:8]:
            console.print(f"  • [dim]{m}[/dim]")
        if len(model_list) > 8:
            console.print(f"  [dim]... and {len(model_list) - 8} more[/dim]")
    console.print()
    model = Prompt.ask("[bold]Model[/bold]", default=default_model).strip()

    if not model:
        console.print("[yellow]No model entered.[/yellow]")
        _ask_websearch(config)
        return

    # Save provider config
    provider_cfg = {
        "name": provider_id,
        "base_url": prov["base_url"],
        "api_mode": prov["api_mode"],
        "models": [model],
        "enabled": True,
    }
    if api_key:
        provider_cfg["api_key"] = api_key

    config.setdefault("providers", {})
    config["providers"][provider_id] = provider_cfg
    config["default_provider"] = provider_id
    config["default_model"] = f"{provider_id}/{model}"

    save_config(config)
    console.print(f"[green]✓[/green] Saved {provider_name} config.")

    _ask_websearch(config)


def _setup_custom_provider(config: dict):
    """Custom Provider — any OpenAI-compatible API."""
    console.print(Panel.fit(
        "[bold cyan]Custom Provider[/bold cyan]\n"
        "Add any OpenAI-compatible API. NexusClaw auto-detects compatibility.",
        border_style="cyan",
    ))
    console.print()

    # Base URL
    console.print("[bold]Base URL[/bold]")
    console.print("Example: https://api.example.com/v1")
    base_url = Prompt.ask("[bold]Base URL[/bold]").strip()
    if not base_url:
        console.print("[yellow]Cancelled.[/yellow]")
        return

    # API mode
    console.print()
    console.print("[bold]API Compatibility Mode[/bold]")
    console.print("  [bold]1.[/bold] OpenAI-compatible (Chat Completions)")
    console.print("  [bold]2.[/bold] Anthropic-compatible (Messages API)")
    console.print("  [bold]3.[/bold] Auto-detect")
    mode_raw = Prompt.ask("Mode", default="3").strip()
    mode_map = {"1": "openai-chat", "2": "anthropic-chat", "3": "auto-detect"}
    api_mode = mode_map.get(mode_raw, "auto-detect")

    # API key
    console.print()
    console.print("[bold]API Key[/bold] (optional — press Enter to skip)")
    api_key = Prompt.ask("[bold]API Key[/bold]").strip()

    # Model
    console.print()
    console.print("[bold]Model ID[/bold]")
    console.print("Exact model name your API expects (e.g. gpt-4o, llama-3.1-70b)")
    model = Prompt.ask("[bold]Model ID[/bold]").strip()
    if not model:
        console.print("[yellow]No model — cancelled.[/yellow]")
        return

    # Save
    slug = base_url.split("//")[1].split("/")[0].replace(".", "_") if "//" in base_url else base_url.replace(".", "_")
    provider_id = "custom_" + slug[:40]

    provider_cfg = {
        "name": provider_id,
        "base_url": base_url,
        "api_mode": api_mode,
        "models": [model],
        "enabled": True,
    }
    if api_key:
        provider_cfg["api_key"] = api_key

    config.setdefault("providers", {})
    config["providers"][provider_id] = provider_cfg
    config["default_provider"] = provider_id
    config["default_model"] = f"{provider_id}/{model}"

    save_config(config)
    console.print(f"[green]✓[/green] Saved custom provider: {provider_id}")

    _ask_websearch(config)


def _ask_websearch(config: dict):
    """Ask for web search provider."""
    console.print()
    console.print(Panel.fit(
        "[bold]Web search[/bold]\n\n"
        "Web search lets your agent look things up online.\n"
        "Choose a provider and paste your API key.\n"
        "[dim]Docs: https://docs.openclaw.ai/tools/web[/dim]",
        border_style="blue",
    ))
    console.print()

    console.print("[bold]Search provider[/bold]\n")
    search_names = list(SEARCH_PROVIDERS.keys())
    for i, name in enumerate(search_names):
        console.print(f"  [bold]{i+1}.[/bold] {name}")
    console.print("  [bold]Skip[/bold] — configure search later")
    console.print()

    raw = Prompt.ask("[bold]Search provider[/bold]", default="Skip").strip()

    if raw.lower() in ("skip", "skip for now", ""):
        _finish_onboard(config)
        return

    # Find provider
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(search_names):
            search_name = search_names[idx]
        else:
            search_name = None
    except ValueError:
        search_name = raw if raw in SEARCH_PROVIDERS else None

    if not search_name:
        _finish_onboard(config)
        return

    sp = SEARCH_PROVIDERS[search_name]
    key_env = sp["key_env"]
    existing_key = os.environ.get(key_env, "")
    api_key = existing_key

    if not api_key:
        console.print(f"\n[bold]{search_name} API key[/bold]")
        if sp.get("key_prefix"):
            console.print(f"[dim]Prefix: [bold]{sp['key_prefix']}[/bold]...[/dim]")
        console.print(f"Docs: [dim]{sp['docs_url']}[/dim]")
        api_key = Prompt.ask("[bold]API Key[/bold]").strip()

    if api_key:
        config["web_search"] = {
            "provider": sp["id"],
            "api_key": api_key,
        }
        save_config(config)
        console.print(f"[green]✓[/green] Saved {search_name} config.")

    _finish_onboard(config)


def _finish_onboard(config: dict):
    """Print success and next steps."""
    console.print()
    cfg_path = get_config_path()
    model = config.get("default_model", "not set")

    console.print(Panel.fit(
        f"[bold green]✓ NexusClaw is ready![/bold green]\n\n"
        f"Model: [bold]{model}[/bold]\n"
        f"Config: [dim]{cfg_path}[/dim]",
        border_style="green",
    ))
    console.print()
    console.print("Next steps:")
    console.print("  1. [dim]nexusclaw start[/dim]  — start the API server")
    console.print("  2. Open [dim]http://localhost:14300[/dim] in your browser")
    console.print("  3. Or run [dim]nexusclaw chat[/dim] to chat from the terminal")


def _print_banner():
    """Print the NexusClaw ASCII banner."""
    banner = r"""
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
██░▄▄▄░██░▄▄░██░▄▄▄██░▀██░██░▄▄▀██░████░▄▄▀██░███░██
██░███░██░▀▀░██░▄▄▄██░█░█░██░█████░████░▀▀░██░█░█░██
██░▀▀▀░██░█████░▀▀▀██░██▄░██░▀▀▄██░▀▀░█░██░██▄▀▄▀▄██
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
 🦞 NEXUSCLAW 🦞
"""
    console.print(banner)
    console.print()


# ── Non-onboard commands ──────────────────────────────────────────────────────

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

    _print_banner()
    console.print(f"Config: [dim]{cfg_path}[/dim]")
    console.print(f"Default provider: [bold]{default}[/bold]")
    console.print(f"Default model: [bold]{config.get('default_model', 'not set')}[/bold]")
    if providers:
        console.print("Providers:")
        for pid, pdata in providers.items():
            models = pdata.get("models", [])
            has_key = bool(pdata.get("api_key"))
            key_mark = "[green]✓ key[/green]" if has_key else "[dim]no key[/dim]"
            mode = pdata.get("api_mode", "openai-chat")
            console.print(f"  • [bold]{pid}[/bold]  {key_mark}  [{mode}]  models: [dim]{', '.join(models[:3])}[/dim]")
    else:
        console.print("\n[yellow]No providers — run [dim]nexusclaw onboard[/dim] first.[/yellow]")


@main.command()
def start():
    """Show how to start NexusClaw."""
    _print_banner()
    console.print("""
[bold]Start NexusClaw:[/bold]

    cd ~/nexusclaw
    docker-compose up -d

Or run directly:

    cd ~/nexusclaw
    pip install -e .
    python -m nexusclaw.api

Then open:  [bold]http://localhost:14300[/bold]
""")


if __name__ == "__main__":
    main()
