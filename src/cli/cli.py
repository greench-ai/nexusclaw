#!/usr/bin/env python3
"""
NexusClaw CLI v1.0
Usage: nexusclaw <command>

Commands:
  nexusclaw chat              Interactive chat
  nexusclaw chat --model xxx --provider openai
  nexusclaw setup             First-time configuration wizard
  nexusclaw status            System health check
  nexusclaw doctor            Diagnose issues
  nexusclaw soul --list       List available souls
  nexusclaw soul --edit       Edit soul interactively
  nexusclaw skills list       List installed skills
  nexusclaw skills search <q> Search skills marketplace
  nexusclaw skills install <name> Install a skill
  nexusclaw skills run <name> Run a skill
  nexusclaw memory "query"    Query long-term memory
  nexusclaw kb add --file <f> Add file to knowledge base
  nexusclaw kb list           List knowledge bases
  nexusclaw agent list        List running agents
  nexusclaw agent --new       Spawn new agent
  nexusclaw autonomy goals    List active goals
  nexusclaw autonomy kill     Kill all active goals
  nexusclaw update            Update from GitHub
  nexusclaw install           Install NexusClaw
  nexusclaw uninstall         Clean removal
"""
from __future__ import annotations

import os, sys, json, asyncio, click
from pathlib import Path
from typing import Optional

# ─── Config ─────────────────────────────────────────────────────────────────
NX_DIR    = Path.home() / ".nexusclaw"
NX_CONFIG = NX_DIR / "config.json"
NX_SOULS  = NX_DIR / "souls"
NX_CACHE  = NX_DIR / "cache"

API_BASE  = os.environ.get("NEXUS_API_URL", "http://localhost:8080")

def load_config() -> dict:
    if NX_CONFIG.exists():
        return json.loads(NX_CONFIG.read_text())
    return {}

def save_config(cfg: dict):
    NX_DIR.mkdir(parents=True, exist_ok=True)
    NX_CONFIG.write_text(json.dumps(cfg, indent=2))

# ─── Helpers ─────────────────────────────────────────────────────────────────
def api_get(path: str) -> Optional[dict]:
    try:
        import urllib.request, urllib.error
        req = urllib.request.Request(f"{API_BASE}{path}")
        req.add_header("Content-Type", "application/json")
        token = load_config().get("token")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[ERR] API unavailable: {e}")
        return None

def api_post(path: str, data: dict) -> Optional[dict]:
    try:
        import urllib.request, urllib.error
        body = json.dumps(data).encode()
        req = urllib.request.Request(f"{API_BASE}{path}", data=body, headers={"Content-Type": "application/json"})
        token = load_config().get("token")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[ERR] API error: {e}")
        return None

def ensure_dirs():
    for d in [NX_DIR, NX_SOULS, NX_CACHE]:
        d.mkdir(parents=True, exist_ok=True)

# ─── Chat ────────────────────────────────────────────────────────────────────
@click.command()
@click.option("--model", default="", help="Model to use")
@click.option("--provider", default="openrouter", help="Provider")
@click.option("--stream/--no-stream", default=True)
def chat(model: str, provider: str, stream: bool):
    """Interactive chat with NexusClaw."""
    import httpx, urllib.request, urllib.error

    cfg = load_config()
    token = cfg.get("token")
    model = model or cfg.get("model", "qwen/qwen3.5-plus")
    provider = provider or cfg.get("provider", "openrouter")

    print("╔══════════════════════════════════════╗")
    print("║   NexusClaw v1.0 — Interactive Chat  ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Provider: {provider} | Model: {model}")
    print("  Type 'exit' to quit | 'clear' to clear | 'model <name>' to switch")
    print()

    messages = []
    soul = cfg.get("soul", "You are NexusClaw, a helpful AI assistant.")
    messages.append({"role": "system", "content": soul})

    while True:
        try:
            user = input("\n👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break

        if not user:
            continue
        if user.lower() in ("exit", "quit", "q"):
            print("👋 Goodbye!")
            break
        if user.lower() == "clear":
            messages = [messages[0]]  # keep system
            print("✓ Cleared")
            continue
        if user.lower().startswith("model "):
            model = user[6:].strip()
            print(f"✓ Model set to: {model}")
            continue

        messages.append({"role": "user", "content": user})
        print("\n🤖 NexusClaw: ", end="", flush=True)

        # Stream response
        try:
            body = json.dumps({
                "message": user, "provider": provider, "model": model,
                "stream": stream, "session_id": None, "use_rag": True
            }).encode()
            req = urllib.request.Request(
                f"{API_BASE}/chat",
                data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}" if token else ""}
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
                reply = data.get("response", "[no response]")
                print(reply)
                messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            print(f"\n[ERR] {e}")

# ─── Setup ───────────────────────────────────────────────────────────────────
@click.command()
def setup():
    """First-time configuration wizard."""
    ensure_dirs()
    cfg = load_config()

    print("\n⚡ NexusClaw Setup Wizard")
    print("=" * 40)

    # API Keys
    print("\n[1/6] API Keys (all optional — press Enter to skip)")
    for key_name, env_var in [
        ("OpenAI", "OPENAI_API_KEY"),
        ("Anthropic", "ANTHROPIC_API_KEY"),
        ("OpenRouter", "OPENROUTER_API_KEY"),
        ("Perplexity", "PERPLEXITY_API_KEY"),
    ]:
        val = os.environ.get(env_var, "")
        prompt = f"  {key_name} API key"
        if val:
            print(f"  {key_name}: ✓ detected from env")
            cfg.setdefault("providers", {}).setdefault(key_name.lower(), {})["api_key"] = val
        else:
            user_val = click.prompt(prompt, default="", show_default=False).strip()
            if user_val:
                cfg.setdefault("providers", {}).setdefault(key_name.lower(), {})["api_key"] = user_val

    # Default provider
    print("\n[2/6] Default Provider")
    cfg["provider"] = click.prompt("  Provider", default="openrouter", show_default=True,
        type=click.Choice(["openrouter", "openai", "anthropic", "ollama"]))

    print("\n[3/6] Default Model")
    default_models = {
        "openrouter": "qwen/qwen3.5-plus",
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "ollama": "llama3.2",
    }
    cfg["model"] = click.prompt("  Model", default=default_models.get(cfg["provider"], "llama3.2"), show_default=True)

    print("\n[4/6] Soul / Personality")
    cfg["soul"] = click.prompt(
        "  Soul template",
        default="assistant",
        type=click.Choice(["assistant", "coder", "researcher"])
    )

    print("\n[5/6] EvoClaw Self-Evolution")
    cfg["evoclaw_enabled"] = click.confirm("  Enable EvoClaw?", default=True)

    print("\n[6/6] Ports")
    cfg["api_port"] = click.prompt("  API port", default=8080, show_default=True, type=int)
    cfg["web_port"] = click.prompt("  Web UI port", default=19789, show_default=True, type=int)

    save_config(cfg)

    print("\n✅ Configuration saved!")
    print(f"   Config: {NX_CONFIG}")
    print("\nNext: nexusclaw chat   # Start chatting")
    print("      nexusclaw status  # Check system health")

# ─── Status ──────────────────────────────────────────────────────────────────
@click.command()
def status():
    """Check system health."""
    print("\n⚡ NexusClaw Status")
    print("=" * 40)

    # Config
    cfg = load_config()
    print(f"  Config:    {'✓' if NX_CONFIG.exists() else '✗'} {NX_CONFIG}")
    print(f"  Version:   1.0.0")
    print(f"  Provider:  {cfg.get('provider', 'openrouter')}")
    print(f"  Model:     {cfg.get('model', 'not set')}")
    print(f"  Soul:      {cfg.get('soul', 'not set')}")
    print(f"  EvoClaw:   {'✓ enabled' if cfg.get('evoclaw_enabled') else '✗ disabled'}")

    # API
    print()
    result = api_get("/health")
    if result:
        print(f"  API:       ✓ Online")
        for k, v in result.get("providers", {}).items():
            print(f"    {k}:   {'✓' if v else '✗'}")
        print(f"  Memory:    {result.get('memory', 'unknown')}")
    else:
        print(f"  API:       ✗ Offline (start with: python apps/api/main.py)")

    # Web
    try:
        import urllib.request
        req = urllib.request.Request(f"http://localhost:{cfg.get('web_port',19789)}/health")
        with urllib.request.urlopen(req, timeout=3):
            print(f"  Web UI:    ✓ Online")
    except Exception:
        print(f"  Web UI:    ✗ Offline (start with: python apps/web/server.py)")

    print()

# ─── Doctor ──────────────────────────────────────────────────────────────────
@click.command()
def doctor():
    """Diagnose system issues."""
    print("\n🩺 NexusClaw Doctor")
    print("=" * 40)

    issues = 0

    # Python version
    v = sys.version_info
    print(f"  Python:   {'✓' if v >= (3,10) else '✗'} {v.major}.{v.minor}.{v.micro}")
    if v < (3, 10):
        print("    ⚠️  Upgrade to Python 3.10+ recommended")
        issues += 1

    # Config
    if not NX_CONFIG.exists():
        print(f"  Config:    ✗ Not configured")
        print("    Run: nexusclaw setup")
        issues += 1
    else:
        print(f"  Config:    ✓ {NX_CONFIG}")

    # API
    if not api_get("/health"):
        print(f"  API:       ✗ Not running")
        print("    Start: python ~/nexusclaw/apps/api/main.py")
        issues += 1

    # Packages
    for pkg in ["fastapi", "uvicorn", "httpx", "pydantic"]:
        try:
            __import__(pkg)
            print(f"  {pkg}:     ✓")
        except ImportError:
            print(f"  {pkg}:     ✗ (pip install {pkg})")
            issues += 1

    print()
    if issues == 0:
        print("  ✅ All checks passed!")
    else:
        print(f"  ⚠️  {issues} issue(s) found")
    print()

# ─── Soul ───────────────────────────────────────────────────────────────────
@click.group(name="soul")
def soul_group():
    """Manage souls (personalities)."""
    pass

@soul_group.command("list")
def soul_list():
    """List available souls."""
    ensure_dirs()
    print("\n🎭 Available Souls:")
    templates = {
        "assistant": "Balanced, helpful assistant. Good for general use.",
        "coder": "Programming expert. Clean, efficient code.",
        "researcher": "Deep researcher. Thorough, cites sources.",
        "devops": "Infrastructure and deployment specialist.",
    }
    for name, desc in templates.items():
        print(f"  • {name:12s} — {desc}")
    print()

@soul_group.command("edit")
def soul_edit():
    """Edit soul interactively."""
    ensure_dirs()
    cfg = load_config()
    current = cfg.get("soul", "assistant")
    print(f"\n🎭 Edit Soul (current: {current})")
    print("Available: assistant, coder, researcher, devops")
    new_soul = click.prompt("Select soul", default=current,
        type=click.Choice(["assistant","coder","researcher","devops"]))
    cfg["soul"] = new_soul
    save_config(cfg)
    print(f"✓ Soul set to: {new_soul}")

# ─── Skills ─────────────────────────────────────────────────────────────────
@click.group(name="skills")
def skills_group():
    """Manage skills."""
    pass

@skills_group.command("list")
def skills_list():
    """List installed skills."""
    import urllib.request, urllib.error
    cfg = load_config()
    token = cfg.get("token")
    try:
        req = urllib.request.Request(f"{API_BASE}/skills",
            headers={"Authorization": f"Bearer {token}" if token else ""})
        with urllib.request.urlopen(req, timeout=5) as r:
            skills = json.loads(r.read())
            print(f"\n🎯 Installed Skills ({len(skills)})")
            for s in skills:
                print(f"  • {s['name']:30s} — {s.get('description','')[:50]}")
    except Exception as e:
        print(f"[ERR] {e}")
    print()

@skills_group.command("run")
@click.argument("skill_name")
def skills_run(skill_name: str):
    """Run a skill."""
    result = api_post("/skills/run", {"skill_name": skill_name, "params": {}})
    if result:
        print(json.dumps(result, indent=2))
    else:
        print(f"[ERR] Skill '{skill_name}' failed or API unavailable")

# ─── Memory ──────────────────────────────────────────────────────────────────
@click.command()
@click.argument("query", required=False)
def memory(query: str):
    """Query long-term memory."""
    if not query:
        query = click.prompt("Memory query")
    result = api_post("/memory/query", {"query": query, "top_k": 5})
    if result and result.get("results"):
        print(f"\n🧠 Memory results for: {query}")
        for r in result["results"]:
            print(f"\n  [{r['score']:.3f}] {r['text'][:200]}...")
    else:
        print("\n🧠 No results found")

# ─── Knowledge Base ───────────────────────────────────────────────────────────
@click.group(name="kb")
def kb_group():
    """Knowledge base management."""
    pass

@kb_group.command("add")
@click.option("--file", "file_path", required=True, help="File to add")
def kb_add(file_path: str):
    """Add file to knowledge base."""
    p = Path(file_path).expanduser()
    if not p.exists():
        print(f"[ERR] File not found: {file_path}")
        return
    print(f"Uploading {p.name}...")
    import urllib.request, urllib.error, mimetypes
    cfg = load_config()
    token = cfg.get("token")
    try:
        with open(p, "rb") as f:
            from urllib.parse import quote
            from io import BytesIO
            boundary = "----NexusClawBoundary"
            body = BytesIO()
            filename = quote(p.name)
            body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n\r\n".encode())
            body.write(f.read())
            body.write(f"--{boundary}--\r\n".encode())
            req = urllib.request.Request(
                f"{API_BASE}/files/upload",
                data=body.getvalue(),
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Authorization": f"Bearer {token}" if token else "",
                }
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                result = json.loads(r.read())
                print(f"✓ Indexed: {result['filename']} ({result['chunks']} chunks)")
    except Exception as e:
        print(f"[ERR] {e}")

@kb_group.command("list")
def kb_list():
    """List knowledge bases."""
    result = api_get("/files/list")
    if result:
        for f in result.get("files", []):
            print(f"  • {f['filename']} — {f.get('chunks',0)} chunks — {f.get('status')}")
    else:
        print("[ERR] API unavailable")

# ─── Update ──────────────────────────────────────────────────────────────────
@click.command()
def update():
    """Update NexusClaw from GitHub."""
    nx_dir = Path(__file__).resolve().parent.parent.parent
    if not (nx_dir / ".git").exists():
        print("[ERR] Not a git repository. Clone from: https://github.com/greench-ai/nexusclaw")
        return
    print("Updating from GitHub...")
    import subprocess
    result = subprocess.run(["git", "-C", str(nx_dir), "pull", "origin", "main"],
        capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Updated successfully")
    else:
        print(f"✗ Update failed: {result.stderr}")

# ─── MAIN ────────────────────────────────────────────────────────────────────
@click.group()
@click.version_option(version="1.0.0")
def cli():
    """NexusClaw v1.0 — Your framework. Your rules."""
    pass

cli.add_command(chat)
cli.add_command(setup)
cli.add_command(status)
cli.add_command(doctor)
cli.add_command(memory)
cli.add_command(update)
cli.add_command(soul_group)
cli.add_command(skills_group)
cli.add_command(kb_group)

if __name__ == "__main__":
    cli()
