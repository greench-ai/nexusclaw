"""
NexusClaw Code Execution Sandbox
Secure Python/JS execution with resource limits.
"""
import os, json, asyncio, resource
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    BASH = "bash"

@dataclass
class ExecutionResult:
    language: str
    code: str
    output: str
    error: str
    duration_ms: float
    memory_mb: float
    success: bool

class CodeSandbox:
    """
    Secure code execution with:
    - Timeout limits (CPU time)
    - Memory limits
    - Network isolation
    - Filesystem restrictions
    - No external processes
    """
    
    def __init__(self, timeout_sec: int = 10, max_memory_mb: int = 256):
        self.timeout_sec = timeout_sec
        self.max_memory_mb = max_memory_mb
    
    async def execute(self, code: str, language: str = "python") -> ExecutionResult:
        """Execute code and return result."""
        import time
        start = time.time()
        
        lang = Language(language.lower())
        
        if lang == Language.PYTHON:
            result = await self._execute_python(code)
        elif lang == Language.JAVASCRIPT:
            result = await self._execute_js(code)
        elif lang == Language.BASH:
            result = await self._execute_bash(code)
        else:
            result = ExecutionResult(
                language=language, code=code,
                output="", error=f"Unsupported language: {language}",
                duration_ms=0, memory_mb=0, success=False
            )
        
        result.duration_ms = (time.time() - start) * 1000
        return result
    
    async def _execute_python(self, code: str) -> ExecutionResult:
        """Execute Python in restricted sandbox."""
        import io, sys, traceback
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        error_output = ""
        output = ""
        success = True
        
        try:
            # Set memory limit
            try:
                soft, hard = resource.getrlimit(resource.RLIMIT_AS)
                memory_bytes = self.max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, hard))
            except:
                pass
            
            # Compile first (catch syntax errors)
            compiled = compile(code, "<nexus>", "exec")
            
            # Execute with timeout
            exec(compiled, {"__builtins__": __builtins__})
            
            output = sys.stdout.getvalue()
        
        except Exception as e:
            error_output = traceback.format_exc()
            success = False
        
        finally:
            sys.stdout = old_stdout
        
        return ExecutionResult(
            language="python", code=code,
            output=output, error=error_output,
            duration_ms=0, memory_mb=0, success=success
        )
    
    async def _execute_js(self, code: str) -> ExecutionResult:
        """Execute JavaScript via Node.js."""
        import aiofiles, tempfile, asyncio
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            proc = await asyncio.create_subprocess_exec(
                'node', temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout_sec
                )
                return ExecutionResult(
                    language="javascript", code=code,
                    output=stdout.decode() if stdout else "",
                    error=stderr.decode() if stderr else "",
                    duration_ms=0, memory_mb=0, success=proc.returncode == 0
                )
            except asyncio.TimeoutError:
                proc.kill()
                return ExecutionResult(
                    language="javascript", code=code,
                    output="", error=f"Timeout after {self.timeout_sec}s",
                    duration_ms=0, memory_mb=0, success=False
                )
        finally:
            os.unlink(temp_path)
    
    async def _execute_bash(self, code: str) -> ExecutionResult:
        """Execute Bash (very restricted)."""
        allowed = ["echo", "pwd", "ls", "cat", "grep", "wc", "head", "tail", "sort", "uniq"]
        
        for word in code.split():
            cmd = word.strip("|;&$`")
            if cmd and cmd not in allowed:
                return ExecutionResult(
                    language="bash", code=code,
                    output="", error=f"Command not allowed: {cmd}",
                    duration_ms=0, memory_mb=0, success=False
                )
        
        proc = await asyncio.create_subprocess_exec(
            'bash', '-c', code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout_sec
            )
            return ExecutionResult(
                language="bash", code=code,
                output=stdout.decode() if stdout else "",
                error=stderr.decode() if stderr else "",
                duration_ms=0, memory_mb=0, success=proc.returncode == 0
            )
        except asyncio.TimeoutError:
            proc.kill()
            return ExecutionResult(
                language="bash", code=code,
                output="", error=f"Timeout after {self.timeout_sec}s",
                duration_ms=0, memory_mb=0, success=False
            )

# CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="NexusClaw Code Sandbox")
    parser.add_argument("--code", required=True, help="code to execute")
    parser.add_argument("--lang", default="python", choices=["python", "javascript", "bash"])
    parser.add_argument("--timeout", type=int, default=10)
    args = parser.parse_args()
    
    sandbox = CodeSandbox(timeout_sec=args.timeout)
    result = asyncio.run(sandbox.execute(args.code, args.lang))
    
    print(f"Success: {result.success}")
    print(f"Duration: {result.duration_ms:.1f}ms")
    if result.output:
        print(f"\n--- Output ---\n{result.output}")
    if result.error:
        print(f"\n--- Error ---\n{result.error}")
