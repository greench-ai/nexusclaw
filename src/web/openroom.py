"""
NexusClaw OpenRoom UI
Browser-based chat interface with real-time streaming, image upload, voice, code execution.
"""
from dataclasses import dataclass
import os

@dataclass
class OpenRoomConfig:
    host: str = "0.0.0.0"
    port: int = 51234
    theme: str = "dark"  # dark, light, midnight
    streaming: bool = True
    code_highlight: bool = True
    math_render: bool = True
    voice_input: bool = False
    image_upload: bool = True

    def save(self, path: str = "~/.nexusclaw/openroom.json"):
        import json
        path = os.path.expanduser(path)
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)

# Full feature matrix
FEATURES = {
    "chat": {
        "streaming": "Real-time token streaming",
        "code_blocks": "Syntax highlighting + copy button",
        "math": "LaTeX / KaTeX rendering",
        "images": "Upload images for analysis",
        "voice": "Microphone input (Web Speech API)",
        "files": "PDF, DOC, TXT, code files",
    },
    "providers": {
        "ollama": "Local free models",
        "openai": "GPT-4o, o1, o3",
        "anthropic": "Claude 3.5, 3.7",
        "minimaxi": "M2.7-highspeed (fast/cheap)",
        "openrouter": "100+ models via single API",
        "custom": "Any OpenAI-compatible endpoint",
    },
    "memory": {
        "persistent": "Qdrant vector DB — learns forever",
        "session": "Zero persistence — maximum privacy",
        "hybrid": "Remember important, forget rest",
        "import": "Load from file, URL, or paste",
    },
    "channels": {
        "web": "Browser UI (OpenRoom)",
        "cli": "Terminal/SSH",
        "telegram": "Chat from anywhere",
        "discord": "Server / community bot",
        "slack": "Team workspace integration",
    },
    "tools": {
        "web_search": "Perplexity-style with citations",
        "code_exec": "Run Python/JS in sandbox",
        "file_ops": "Read, write, browse filesystem",
        "rag": "Document Q&A over your files",
        "api": "Call any external API",
    },
    "soul": {
        "templates": "Blank, Assistant, Coder, Researcher",
        "custom": "Write your own identity",
        "import": "Load from file",
        "switch": "Hot-swap souls mid-conversation",
    },
}
