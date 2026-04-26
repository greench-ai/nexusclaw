"""
NexusClaw Machine Tools — File browser, shell, and browser automation.
"""
import os, json, subprocess, asyncio
from pathlib import Path
from typing import Optional

# ─── FILE BROWSER ────────────────────────────────────────────────

def list_dir(path: str = "/home/greench", recursive: bool = False) -> dict:
    """List directory contents."""
    try:
        p = Path(os.path.expanduser(path))
        if not p.exists():
            return {"error": f"Path does not exist: {path}", "path": str(p)}
        if not p.is_dir():
            return {"error": f"Not a directory: {path}", "path": str(p)}
        
        items = []
        if recursive:
            for item in p.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(p)
                    items.append({"name": str(rel), "type": "file", "size": item.stat().st_size})
                elif item.is_dir() and "/." not in str(item):
                    rel = item.relative_to(p)
                    items.append({"name": str(rel), "type": "dir"})
        else:
            for item in sorted(p.iterdir()):
                if item.name.startswith("."):
                    continue
                if item.is_file():
                    items.append({"name": item.name, "type": "file", "size": item.stat().st_size})
                elif item.is_dir():
                    items.append({"name": item.name, "type": "dir"})
        
        return {"path": str(p), "items": items[:200], "total": len(items)}
    except PermissionError:
        return {"error": "Permission denied", "path": str(p)}
    except Exception as e:
        return {"error": str(e), "path": str(p)}

def read_file(path: str, max_chars: int = 50000) -> dict:
    """Read file contents."""
    try:
        p = Path(os.path.expanduser(path))
        if not p.exists():
            return {"error": f"File not found: {path}"}
        if not p.is_file():
            return {"error": f"Not a file: {path}"}
        
        size = p.stat().st_size
        if size > max_chars * 2:
            with open(p) as f:
                content = f.read(max_chars)
            return {"path": str(p), "content": content, "truncated": True, "total_size": size, "read": max_chars}
        
        with open(p) as f:
            content = f.read(max_chars)
        return {"path": str(p), "content": content, "truncated": False, "total_size": size}
    except PermissionError:
        return {"error": "Permission denied"}
    except Exception as e:
        return {"error": str(e)}

def write_file(path: str, content: str) -> dict:
    """Write content to file."""
    try:
        p = Path(os.path.expanduser(path))
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w") as f:
            f.write(content)
        return {"ok": True, "path": str(p), "bytes": len(content)}
    except Exception as e:
        return {"error": str(e)}

def file_info(path: str) -> dict:
    """Get file metadata."""
    try:
        p = Path(os.path.expanduser(path))
        if not p.exists():
            return {"error": f"Not found: {path}"}
        stat = p.stat()
        return {
            "path": str(p),
            "type": "dir" if p.is_dir() else "file",
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "readable": os.access(p, os.R_OK),
            "writable": os.access(p, os.W_OK),
        }
    except Exception as e:
        return {"error": str(e)}

# ─── SHELL ──────────────────────────────────────────────────────

def run_shell(command: str, timeout: int = 30) -> dict:
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return {
            "ok": True,
            "command": command,
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:2000],
            "returncode": result.returncode,
            "timed_out": False
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "command": command, "error": "Timeout", "timed_out": True}
    except Exception as e:
        return {"ok": False, "command": command, "error": str(e)}

async def run_shell_stream(command: str, timeout: int = 30) -> str:
    """Run shell command with streaming output."""
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return stdout.decode()[:50000] + ("\nSTDERR: " + stderr.decode()[:2000] if stderr else "")
    except asyncio.TimeoutExpired:
        proc.kill()
        return "TIMEOUT"

# ─── SYSTEM INFO ─────────────────────────────────────────────────

def system_info() -> dict:
    """Get system information."""
    try:
        import platform, psutil
        
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return {
            "os": platform.system(),
            "hostname": platform.node(),
            "cpu_percent": cpu,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(mem.total / (1024**3), 1),
            "memory_used_gb": round(mem.used / (1024**3), 1),
            "memory_percent": mem.percent,
            "disk_total_gb": round(disk.total / (1024**3), 1),
            "disk_used_gb": round(disk.used / (1024**3), 1),
            "disk_percent": disk.percent,
        }
    except Exception as e:
        return {"error": str(e)}

def running_processes() -> dict:
    """List running processes."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter()[:30]:
            try:
                procs.append({
                    "pid": p.pid,
                    "name": p.name(),
                    "cpu": p.cpu_percent(interval=0.01),
                    "mem": p.memory_percent()
                })
            except: pass
        return {"processes": procs}
    except Exception as e:
        return {"error": str(e)}

def docker_status() -> dict:
    """Get Docker status."""
    try:
        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"], capture_output=True, text=True)
        containers = [line.split("\t") for line in result.stdout.strip().split("\n") if line]
        return {"containers": [{"name": c[0], "status": c[1] if len(c) > 1 else ""} for c in containers]}
    except Exception as e:
        return {"error": str(e)}

# ─── BROWSER AUTOMATION ─────────────────────────────────────────

BROWSER_TOOLS = None

def get_browser_tools():
    """Lazy-load browser tools (requires playwright)."""
    global BROWSER_TOOLS
    if BROWSER_TOOLS is None:
        try:
            from .browser import BrowserTools
            BROWSER_TOOLS = BrowserTools()
        except ImportError:
            BROWSER_TOOLS = "not_installed"
    return BROWSER_TOOLS

def browser_navigate(url: str) -> dict:
    """Navigate browser to URL."""
    tools = get_browser_tools()
    if tools == "not_installed":
        return {"error": "Playwright not installed. Run: pip install playwright && playwright install chromium"}
    return tools.navigate(url)

def browser_screenshot(msg_id: str = "") -> dict:
    """Take screenshot."""
    tools = get_browser_tools()
    if tools == "not_installed":
        return {"error": "Playwright not installed."}
    return tools.screenshot(msg_id)

def browser_click(selector: str) -> dict:
    """Click element."""
    tools = get_browser_tools()
    if tools == "not_installed":
        return {"error": "Playwright not installed."}
    return tools.click(selector)

def browser_type(selector: str, text: str) -> dict:
    """Type into element."""
    tools = get_browser_tools()
    if tools == "not_installed":
        return {"error": "Playwright not installed."}
    return tools.type_text(selector, text)

def browser_evaluate(js: str) -> dict:
    """Execute JavaScript in page."""
    tools = get_browser_tools()
    if tools == "not_installed":
        return {"error": "Playwright not installed."}
    return tools.evaluate(js)

def browser_close() -> dict:
    """Close browser."""
    tools = get_browser_tools()
    if tools == "not_installed":
        return {"ok": True}
    return tools.close()
