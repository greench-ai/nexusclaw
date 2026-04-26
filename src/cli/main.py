#!/usr/bin/env python3
"""
NexusClaw CLI — Main command-line interface.
Usage: nexusclaw [command] [options]
"""
import sys, os, asyncio, argparse

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from soul.engine import Soul, SOUL_TEMPLATES
from onboard.setup import run_wizard
from tools.registry import get_registry
from memory.vector_store import VectorMemory

VERSION = "0.20.0"

def main():
    parser = argparse.ArgumentParser(
        description=f"NexusClaw v{VERSION} — Your framework. Your rules.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", action="version", version=f"NexusClaw {VERSION}")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    
    # setup
    sub.add_parser("setup", help="Run setup wizard")
    
    # chat
    chat = sub.add_parser("chat", help="Start interactive chat")
    chat.add_argument("--provider", default="ollama", help="AI provider")
    chat.add_argument("--model", default="llama3.2", help="Model name")
    chat.add_argument("--soul", default="~/.nexusclaw/soul.json", help="Soul file")
    chat.add_argument("--stream", action="store_true", help="Stream responses")
    
    # soul
    soul_parser = sub.add_parser("soul", help="Soul editor")
    soul_parser.add_argument("--edit", action="store_true", help="Edit soul interactively")
    soul_parser.add_argument("--new", help="Create new soul of type (blank/assistant/coder/researcher)")
    soul_parser.add_argument("--path", default="~/.nexusclaw/soul.json", help="Soul file path")
    
    # tools
    tools = sub.add_parser("tools", help="List available tools")
    tools.add_argument("--category", help="Filter by category")
    
    # memory
    memory = sub.add_parser("memory", help="Query memory")
    memory.add_argument("query", nargs="+", help="Search query")
    memory.add_argument("--limit", type=int, default=5, help="Number of results")
    
    # kb (knowledge base)
    kb = sub.add_parser("kb", help="Knowledge base commands")
    kb.add_argument("action", choices=["add", "list", "index", "search"], help="Action")
    kb.add_argument("--file", help="File to add")
    kb.add_argument("--query", help="Search query")
    kb.add_argument("--title", help="Document title")
    
    # config
    sub.add_parser("config", help="Show current configuration")
    
    # status
    sub.add_parser("status", help="Show system status")
    
    args = parser.parse_args()
    
    if not args.command:
        # Interactive mode
        asyncio.run(interactive_chat())
    elif args.command == "setup":
        run_wizard()
    elif args.command == "chat":
        asyncio.run(chat_mode(args))
    elif args.command == "soul":
        handle_soul(args)
    elif args.command == "tools":
        handle_tools(args)
    elif args.command == "memory":
        handle_memory(args)
    elif args.command == "kb":
        handle_kb(args)
    elif args.command == "config":
        show_config()
    elif args.command == "status":
        show_status()

async def interactive_chat():
    """Default interactive chat."""
    print(f"NexusClaw v{VERSION} — Your framework. Your rules.")
    print("Type 'exit' to quit, 'help' for commands.\n")
    await chat_mode(argparse.Namespace(provider="ollama", model="llama3.2", soul="~/.nexusclaw/soul.json", stream=True))

async def chat_mode(args):
    """Interactive chat loop."""
    import aiohttp
    
    # Load soul
    soul = Soul.load(os.path.expanduser(args.soul))
    
    # Load config
    config_path = Path("~/.nexusclaw/config.json").expanduser()
    provider = "ollama"
    model = "llama3.2"
    if config_path.exists():
        import json
        with open(config_path) as f:
            config = json.load(f)
            provider = config.get("provider", "ollama")
            model = config.get("model", "llama3.2")
    
    messages = [{"role": "system", "content": soul.get_system_prompt()}]
    
    print(f"Connected to {provider}/{model}. Soul: {soul.name}\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ("exit", "quit", "bye"):
                break
            if user_input.lower() == "help":
                print("Commands: exit, clear, soul, tools, memory")
                continue
            if user_input.lower() == "clear":
                messages = [{"role": "system", "content": soul.get_system_prompt()}]
                print("Conversation cleared.")
                continue
            
            messages.append({"role": "user", "content": user_input})
            
            # Try API first
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {"model": model, "messages": messages, "stream": args.stream}
                    async with session.post(f"http://localhost:8080/v1/chat/answer/stream",
                        json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                        if resp.status == 200:
                            full = ""
                            async for line in resp.content:
                                text = line.decode().strip()
                                if text.startswith("data: "):
                                    try:
                                        import json as j
                                        data = j.loads(text[6:])
                                        if data.get("type") == "chunk":
                                            chunk = data.get("content", "")
                                            print(chunk, end="", flush=True)
                                            full += chunk
                                    except: pass
                            print()
                            messages.append({"role": "assistant", "content": full})
                        else:
                            print(f"[API error: {resp.status}]")
            except:
                print("[API offline — start with: python3 apps/api/main.py]")
                messages.pop()
                break
        except KeyboardInterrupt:
            break
    print("Goodbye!")

def handle_soul(args):
    """Handle soul commands."""
    from soul.editor import interactive_editor
    path = os.path.expanduser(args.path)
    if args.edit:
        interactive_editor(path)
    elif args.new:
        soul_type = args.new
        if soul_type in SOUL_TEMPLATES:
            t = SOUL_TEMPLATES[soul_type]
            t.save(path)
            print(f"Created {soul_type} soul at {path}")
        else:
            print(f"Unknown type. Available: {', '.join(SOUL_TEMPLATES.keys())}")
    else:
        soul = Soul.load(path) if Path(path).exists() else Soul("Nexus", "", "", [])
        print(f"Name: {soul.name}")
        print(f"Identity: {soul.identity}")
        print(f"Backstory: {soul.backstory}")
        print(f"Rules: {len(soul.rules)}")
        print(f"\nSystem prompt:\n{soul.get_system_prompt()}")

def handle_tools(args):
    """Handle tools listing."""
    registry = get_registry()
    tools = registry.tools.values()
    if args.category:
        tools = [t for t in tools if t.category == args.category]
    
    print(f"\nAvailable tools ({len(list(tools))}):\n")
    for t in sorted(tools, key=lambda x: x.category):
        print(f"  {t.name} [{t.category}] — {t.description}")
        print(f"    Permission: {t.permission}")
        if t.args_schema:
            req = [k for k, v in t.args_schema.items() if v.get("required")]
            opt = [k for k, v in t.args_schema.items() if not v.get("required")]
            if req: print(f"    Required: {', '.join(req)}")
            if opt: print(f"    Optional: {', '.join(opt)}")
        print()

def handle_memory(args):
    """Handle memory queries."""
    vm = VectorMemory()
    query = " ".join(args.query)
    results = vm.search(query, limit=args.limit)
    if results:
        print(f"\nMemory results for: {query}\n")
        for r in results:
            print(f"  [{r.get('score', 0):.2f}] {r.get('content', '')[:100]}...")
    else:
        print("No memories found.")

def handle_kb(args):
    """Handle knowledge base commands."""
    from knowledge.manager import KnowledgeBase
    kb = KnowledgeBase()
    
    if args.action == "add":
        if not args.file:
            print("--file required")
        else:
            doc = kb.add(args.file, args.title)
            print(f"Added: {doc.title} ({doc.id})")
    elif args.action == "list":
        for doc in kb.list_all():
            print(f"  [{doc.status}] {doc.title}")
    elif args.action == "index":
        result = asyncio.run(kb.index_all())
        print(f"Indexed: {result['indexed']}/{result['total']}")
    elif args.action == "search":
        if not args.query:
            print("--query required")
        else:
            results = kb.search(args.query)
            for r in results:
                print(f"  {r.get('content', '')[:100]}...")

def show_config():
    """Show current configuration."""
    config_path = Path("~/.nexusclaw/config.json").expanduser()
    if config_path.exists():
        with open(config_path) as f:
            import json
            print(json.dumps(json.load(f), indent=2))
    else:
        print("No config. Run: nexusclaw setup")

def show_status():
    """Show system status."""
    import aiohttp
    print(f"\nNexusClaw v{VERSION} Status\n")
    
    # API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8080/health", timeout=3) as resp:
                data = await resp.json()
                print(f"  API: {'✅ Online' if data.get('ok') else '❌ Error'}")
    except:
        print("  API: ❌ Offline")
    
    # Ollama
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=3) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m.get("name","?") for m in data.get("models",[])]
                    print(f"  Ollama: ✅ Online ({len(models)} models)")
                    for m in models[:5]:
                        print(f"    - {m}")
                else:
                    print("  Ollama: ❌ Error")
    except:
        print("  Ollama: ❌ Offline")
    
    # Memory
    vm = VectorMemory()
    count = vm.count()
    print(f"  Memory: {count} entries")
    
    print()

if __name__ == "__main__":
    main()
