"""
NexusClaw Plugin Engine
Like OpenClaw's plugin system — discover, load, and run plugins.
"""
import os, json, importlib.util, importlib, inspect
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class PluginInfo:
    id: str
    name: str
    version: str
    description: str
    author: str
    entry_point: str
    hooks: list
    enabled: bool

class PluginManifest:
    @staticmethod
    def load(plugin_dir: Path) -> dict:
        manifest_file = plugin_dir / "nexusclaw-plugin.json"
        if manifest_file.exists():
            with open(manifest_file) as f:
                return json.load(f)
        return {}

class PluginRegistry:
    """
    Registry of all available plugins.
    Plugins are directories with nexusclaw-plugin.json manifest.
    """
    
    def __init__(self, plugin_dirs: list = None):
        self.plugins: dict[str, PluginInfo] = {}
        self.hooks: dict[str, list[Callable]] = {}
        self._hook_types = ["on_message", "on_startup", "on_shutdown", "on_tool_call", "pre_response", "post_response"]
        
        dirs = plugin_dirs or [
            Path("~/.nexusclaw/plugins").expanduser(),
            Path(__file__).parent.parent.parent / "plugins"
        ]
        for d in dirs:
            self._scan_dir(d)
    
    def _scan_dir(self, plugin_dir: Path):
        """Scan directory for plugins."""
        if not plugin_dir.exists():
            return
        
        for item in plugin_dir.iterdir():
            if not item.is_dir():
                continue
            manifest = PluginManifest.load(item)
            if manifest:
                self._register_plugin(item, manifest)
    
    def _register_plugin(self, plugin_dir: Path, manifest: dict):
        """Register a plugin from manifest."""
        plugin_id = manifest.get("id", plugin_dir.name)
        
        info = PluginInfo(
            id=plugin_id,
            name=manifest.get("name", plugin_id),
            version=manifest.get("version", "0.1.0"),
            description=manifest.get("description", ""),
            author=manifest.get("author", "unknown"),
            entry_point=manifest.get("entry_point", "main.py"),
            hooks=manifest.get("hooks", []),
            enabled=manifest.get("enabled", True)
        )
        
        self.plugins[plugin_id] = info
        
        # Register hooks
        for hook in info.hooks:
            if hook not in self.hooks:
                self.hooks[hook] = []
        
        # Load plugin module
        self._load_plugin(plugin_dir, plugin_id, info.entry_point)
    
    def _load_plugin(self, plugin_dir: Path, plugin_id: str, entry_point: str):
        """Load a plugin's Python module."""
        main_file = plugin_dir / entry_point
        if not main_file.exists():
            return
        
        spec = importlib.util.spec_from_file_location(plugin_id, main_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                # Register hook functions
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if name.startswith("hook_"):
                        hook_name = name[5:]  # strip "hook_"
                        if hook_name in self.hooks:
                            self.hooks[hook_name].append(func)
            except Exception as e:
                print(f"Plugin {plugin_id} load error: {e}")
    
    def enable(self, plugin_id: str) -> bool:
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = True
            return True
        return False
    
    def disable(self, plugin_id: str) -> bool:
        if plugin_id in self.plugins:
            self.plugins[plugin_id].enabled = False
            return True
        return False
    
    def list_plugins(self) -> list[PluginInfo]:
        return list(self.plugins.values())
    
    async def run_hook(self, hook_name: str, *args, **kwargs):
        """Run all functions registered for a hook."""
        if hook_name not in self.hooks:
            return
        
        results = []
        for func in self.hooks[hook_name]:
            try:
                result = func(*args, **kwargs)
                if inspect.iscoroutine(result):
                    result = await result
                results.append(result)
            except Exception as e:
                print(f"Hook {hook_name} error: {e}")
        
        return results

# Example plugin manifest
EXAMPLE_PLUGIN = {
    "id": "example",
    "name": "Example Plugin",
    "version": "0.1.0",
    "description": "Example NexusClaw plugin",
    "author": "nexusclaw",
    "entry_point": "main.py",
    "hooks": ["on_message", "on_tool_call"],
    "enabled": True
}

@dataclass
class PluginTemplate:
    id: str
    name: str
    description: str
    hooks: list

PLUGIN_TEMPLATES = {
    "channel": PluginTemplate("channel", "Channel Plugin", "Add a new communication channel", ["on_message", "pre_response", "post_response"]),
    "provider": PluginTemplate("provider", "Provider Plugin", "Add a new AI provider", ["pre_response", "post_response"]),
    "tool": PluginTemplate("tool", "Tool Plugin", "Add a new tool or capability", ["on_tool_call"]),
    "memory": PluginTemplate("memory", "Memory Plugin", "Add a new memory backend", []),
    "theme": PluginTemplate("theme", "Theme Plugin", "Add a new UI theme", ["on_startup"]),
}

def create_plugin(template_id: str, plugin_name: str, output_dir: Path):
    """Create a new plugin from template."""
    template = PLUGIN_TEMPLATES.get(template_id)
    if not template:
        raise ValueError(f"Unknown template: {template_id}")
    
    output_dir = output_dir / plugin_name.lower().replace(" ", "_")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create manifest
    manifest = {**EXAMPLE_PLUGIN, "id": plugin_name.lower().replace(" ", "-"),
                "name": plugin_name, "hooks": template.hooks}
    
    with open(output_dir / "nexusclaw-plugin.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Create entry point
    with open(output_dir / "main.py", "w") as f:
        f.write(f'''"""NexusClaw {plugin_name} plugin."""
from typing import Any

async def hook_on_startup(app):
    print("Starting {plugin_name} plugin...")

async def hook_on_message(message: str) -> str:
    """Process incoming message."""
    return message

async def hook_on_tool_call(tool_name: str, args: dict) -> Any:
    """Handle tool call."""
    return {{"result": "not implemented"}}
''')
    
    return output_dir
