import asyncio
import shlex
from typing import AsyncGenerator, Optional


class CommandRunner:
    """Runs shell commands asynchronously with live output streaming."""

    def __init__(self):
        self._process: Optional[asyncio.subprocess.Process] = None
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    async def run(self, cmd: str | list, cwd: str = "/tmp") -> AsyncGenerator[str, None]:
        self._running = True
        if isinstance(cmd, str):
            args = shlex.split(cmd)
        else:
            args = cmd

        try:
            self._process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
            )
            async for line in self._process.stdout:
                yield line.decode(errors="replace").rstrip()

            await self._process.wait()
        except FileNotFoundError:
            yield f"[ERROR] Command not found: {args[0]}"
        except PermissionError:
            yield f"[ERROR] Permission denied. Try running as root."
        except Exception as e:
            yield f"[ERROR] {e}"
        finally:
            self._running = False
            self._process = None

    async def stop(self):
        if self._process and self._running:
            try:
                self._process.terminate()
                await asyncio.sleep(0.5)
                if self._process.returncode is None:
                    self._process.kill()
            except Exception:
                pass
            self._running = False


async def check_tool(name: str) -> bool:
    """Check if a CLI tool is available on PATH."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "which", name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0
    except Exception:
        return False
