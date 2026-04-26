#!/usr/bin/env python3
"""NexusClaw CLI — Freedom-first AI agent framework."""
import sys, os, asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from soul.engine import Soul, SOUL_TEMPLATES
from providers.engine import create_provider
from onboard.wizard import NexusConfig

def main():
    import argparse
    parser = argparse.ArgumentParser(description="NexusClaw — Your framework. Your rules.")
    parser.add_argument("command", nargs="?", default="chat", help="chat, setup, shell")
    parser.add_argument("--config", default="~/.nexusclaw/config.json", help="Config path")
    parser.add_argument("--soul", default="~/.nexusclaw/soul.json", help="Soul path")
    parser.add_argument("--stream", action="store_true", help="Stream responses")
    args = parser.parse_args()
    
    if args.command == "setup":
        from onboard.wizard import run_wizard
        run_wizard()
    elif args.command == "chat":
        asyncio.run(chat_loop(args))
    elif args.command == "shell":
        print("NexusClaw shell — use 'nexusclaw chat' for interactive mode")
    else:
        print(f"Unknown command: {args.command}")
        print("Usage: nexusclaw [setup|chat]")

async def chat_loop(args):
    config = NexusConfig.load(args.config)
    if config is None:
        print("Not configured. Run: nexusclaw setup")
        return
    
    soul = Soul.load(args.soul)
    if soul.identity == "":
        soul = SOUL_TEMPLATES.get(config.soul_type, SOUL_TEMPLATES["blank"])
    
    provider = create_provider(
        provider=config.provider.split()[0].lower(),
        api_key=config.provider_key,
        base_url=config.provider_base_url or "",
        model=config.model or "llama3.2"
    )
    
    messages = [{"role": "system", "content": soul.get_system_prompt()}]
    
    print(f"NexusClaw ready. Provider: {config.provider}. Type 'exit' to quit.\n")
    
    while True:
        try:
            user = input("You: ")
            if user.lower() in ("exit", "quit", "bye"):
                break
            messages.append({"role": "user", "content": user})
            
            if args.stream:
                print("Nexus: ", end="", flush=True)
                full = ""
                async for chunk in provider.stream(messages):
                    print(chunk, end="", flush=True)
                    full += chunk
                print()
                messages.append({"role": "assistant", "content": full})
            else:
                response = await provider.chat(messages)
                print(f"Nexus: {response}")
                messages.append({"role": "assistant", "content": response})
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
