"""
Hydra wrapper — fast network login brute-forcer.

Smarter than plain hydra:
  - Auto-selects optimum thread count per protocol
  - Stops immediately on first valid credential (--stop)
  - Live credential extraction from output
  - Supports: SSH, FTP, HTTP-Form, RDP, SMB, MySQL, POP3, SMTP, Telnet, VNC
"""

import re
from typing import AsyncGenerator
from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Hydra (Network Brute-Force)",
    description=(
        "Fast parallel network login cracker. Supports 50+ protocols. "
        "Auto-tunes thread count per protocol. Stops on first valid credential. "
        "Live credential display as soon as found."
    ),
    usage="Provide target IP, protocol, username or list, and password list.",
    danger_note="🟠 Medium Risk — generates login attempts. May trigger lockouts or IDS alerts.",
    example="hydra -l admin -P rockyou.txt 192.168.1.1 ssh",
)

DANGER = DangerLevel.ORANGE

# Optimal thread counts per protocol (to avoid lockouts)
PROTOCOL_THREADS = {
    "ssh":      4,
    "ftp":      8,
    "rdp":      4,
    "smb":      4,
    "mysql":    8,
    "mssql":    4,
    "pop3":     8,
    "smtp":     8,
    "telnet":   8,
    "vnc":      4,
    "http-get": 16,
    "http-post-form": 16,
}

COMMON_USERS = {
    "ssh":   ["root", "admin", "user", "ubuntu", "kali"],
    "ftp":   ["anonymous", "admin", "ftp", "user"],
    "mysql": ["root", "admin", "mysql"],
    "rdp":   ["administrator", "admin", "user"],
    "smb":   ["administrator", "admin", "guest"],
}


class HydraCracker:
    def __init__(self):
        self._runner = CommandRunner()

    async def crack(
        self,
        target: str,
        protocol: str,
        username: str = "",
        userlist: str = "",
        passlist: str = "/usr/share/wordlists/rockyou.txt",
        port: int = 0,
        http_form_path: str = "",
        http_form_data: str = "",
        stop_on_first: bool = True,
    ) -> AsyncGenerator[str, None]:

        threads = PROTOCOL_THREADS.get(protocol, 8)
        yield f"[*] Hydra → {protocol.upper()}://{target}"
        yield f"[*] Threads: {threads}  Stop on first: {stop_on_first}"

        cmd = ["hydra", "-t", str(threads), "-v"]

        # Username / list
        if username:
            cmd += ["-l", username]
        elif userlist:
            cmd += ["-L", userlist]
        else:
            # Use common users for known protocols
            defaults = COMMON_USERS.get(protocol, ["admin"])
            tmp_users = "/tmp/penkit_hydra_users.txt"
            with open(tmp_users, "w") as f:
                f.write("\n".join(defaults))
            cmd += ["-L", tmp_users]
            yield f"[*] Using default usernames for {protocol}: {', '.join(defaults)}"

        # Password list
        cmd += ["-P", passlist]

        if stop_on_first:
            cmd.append("-f")

        if port:
            cmd += ["-s", str(port)]

        cmd.append(target)

        # Protocol-specific args
        if protocol == "http-post-form":
            if not http_form_path or not http_form_data:
                yield "[ERROR] http-post-form requires path and form data"
                yield "  Format: /login.php:user=^USER^&pass=^PASS^:Invalid"
                return
            cmd += [f"http-post-form", f"{http_form_path}:{http_form_data}"]
        else:
            cmd.append(protocol)

        yield f"[*] Command: {' '.join(cmd[:10])} ..."
        yield ""

        found = []
        async for line in self._runner.run(cmd):
            # Detect successful login
            if "[" in line and "] login:" in line:
                found.append(line.strip())
                yield f"\n{'═'*50}"
                yield f"[+] CREDENTIAL FOUND!"
                # Parse: [port][protocol] host:port   login: USER   password: PASS
                m = re.search(r'login:\s*(\S+)\s+password:\s*(\S+)', line)
                if m:
                    yield f"    Username: {m.group(1)}"
                    yield f"    Password: {m.group(2)}"
                else:
                    yield f"    {line.strip()}"
                yield f"{'═'*50}\n"
            elif "Hydra" in line and ("finished" in line or "completed" in line):
                yield f"[*] {line.strip()}"
            elif "ERROR" in line or "failed" in line.lower():
                yield f"[!] {line.strip()}"
            elif line.strip():
                yield line

        if not found:
            yield "[!] No credentials found in wordlist"
        else:
            yield f"\n[+] Total found: {len(found)} credential(s)"

    async def spray(
        self,
        targets_file: str,
        protocol: str,
        username: str,
        password: str,
    ) -> AsyncGenerator[str, None]:
        """Password spray: one password against many targets."""
        yield f"[*] Password spray: {username}:{password} against {targets_file}"
        async for line in self._runner.run([
            "hydra",
            "-l", username,
            "-p", password,
            "-M", targets_file,
            "-t", "4",
            "-f",
            protocol,
        ]):
            if "login:" in line:
                yield f"[+] HIT: {line.strip()}"
            elif line.strip():
                yield line

    async def stop(self):
        await self._runner.stop()
