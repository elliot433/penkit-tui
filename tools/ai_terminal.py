"""
PenKit AI Attack Terminal — autonomes Pentest-KI-System.

Der Nutzer beschreibt das Ziel.
Die KI schlägt Angriffe vor → PenKit führt sie aus → Output zurück an KI →
KI analysiert und passt Strategie an.

KEIN API-KEY NÖTIG:
  Standardmäßig läuft alles lokal via Ollama (kostenlos, offline).
  Optional: Claude oder OpenAI API-Key für bessere Ergebnisse.

Ollama Installation:
  curl -fsSL https://ollama.com/install.sh | sh
  ollama pull llama3.2      # empfohlen (4 GB, gut für Pentest)
  ollama pull mistral       # Alternative (4 GB)
  ollama pull codellama     # gut für Shell-Befehle

Modell-Empfehlung für Pentest:
  llama3.2 > mistral > gemma2 > qwen2.5
"""

from __future__ import annotations
import asyncio
import json
import os
import re
import textwrap
from dataclasses import dataclass, field
from typing import AsyncGenerator

from core.output_dir import get as out_dir

# ── System-Prompt für die KI ──────────────────────────────────────────────────

SYSTEM_PROMPT = """You are PenKit AI — an expert penetration tester with 20 years of experience.
You help authorized security researchers attack their own systems or systems they have permission to test.

Your job:
1. Analyze what the user tells you about the target
2. Suggest the next best attack step (one at a time)
3. Analyze results and adapt strategy
4. Always explain WHY you chose this technique

Rules:
- Every suggestion must be a CONCRETE action (not vague advice)
- Format attack commands as: ACTION: <tool_name> | PARAMS: <parameters>
- After seeing results, analyze what worked, what failed, and why
- Think like an attacker: what would give you the most access fastest?
- Prioritize: credential theft > remote execution > privilege escalation > persistence
- If you see errors, diagnose them and suggest fixes

Available PenKit tools you can trigger:
  SCAN: nmap           - port/service/OS scan
  SCAN: vuln           - vulnerability scan (nmap vulners)
  WIFI: handshake      - capture WPA2 handshake
  WIFI: pixiedust      - WPS Pixie-Dust attack
  CRACK: hashcat       - GPU crack hash
  CRACK: john          - CPU crack hash
  BRUTE: hydra         - network brute-force
  MITM: arpspoof       - ARP spoofing
  MITM: responder      - NTLM hash capture
  MITM: mitm6          - IPv6 NTLM relay
  WEB: sqlmap          - SQL injection
  WEB: nikto           - web vulnerability scan
  WEB: ffuf            - directory fuzzing
  OSINT: harvest       - email/subdomain harvesting
  OSINT: sherlock      - username search
  C2: payload          - generate reverse shell payload
  SHELL: <command>     - run any shell command directly

Respond in German if the user writes German, English otherwise.
Be direct, tactical, and specific."""


# ── KI-Backend Klassen ────────────────────────────────────────────────────────

@dataclass
class Message:
    role: str    # "system" | "user" | "assistant"
    content: str


class OllamaBackend:
    """Lokale KI via Ollama — kostenlos, kein Internet."""

    def __init__(self, model: str = "llama3.2"):
        self.model = model
        self.api_url = "http://localhost:11434/api/chat"

    async def is_available(self) -> bool:
        import shutil
        return shutil.which("ollama") is not None

    async def get_models(self) -> list[str]:
        proc = await asyncio.create_subprocess_exec(
            "ollama", "list",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        lines = stdout.decode().strip().split("\n")[1:]  # skip header
        models = []
        for line in lines:
            if line.strip():
                models.append(line.split()[0])
        return models

    async def chat(
        self,
        messages: list[Message],
        stream: bool = True,
    ) -> AsyncGenerator[str, None]:
        import urllib.request
        import urllib.error

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "options": {
                "temperature": 0.3,   # niedrig = konsistente Pentest-Empfehlungen
                "num_predict": 1024,
            },
        }

        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    if line:
                        try:
                            obj = json.loads(line.decode())
                            token = obj.get("message", {}).get("content", "")
                            if token:
                                yield token
                            if obj.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue

        except urllib.error.URLError:
            yield "[!] Ollama nicht erreichbar. Starte mit: ollama serve"
        except Exception as e:
            yield f"[!] Fehler: {e}"


class ClaudeBackend:
    """Claude API — beste Qualität, benötigt API-Key."""

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"

    async def chat(
        self,
        messages: list[Message],
        stream: bool = False,
    ) -> AsyncGenerator[str, None]:
        import urllib.request

        # System-Message separat
        system = next((m.content for m in messages if m.role == "system"), SYSTEM_PROMPT)
        chat_msgs = [{"role": m.role, "content": m.content}
                     for m in messages if m.role != "system"]

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system,
            "messages": chat_msgs,
        }

        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                yield result["content"][0]["text"]
        except Exception as e:
            yield f"[!] Claude API Fehler: {e}"


class OpenAIBackend:
    """OpenAI API — GPT-4."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: list[Message], stream: bool = False) -> AsyncGenerator[str, None]:
        import urllib.request

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": 1024,
            "temperature": 0.3,
        }

        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                yield result["choices"][0]["message"]["content"]
        except Exception as e:
            yield f"[!] OpenAI Fehler: {e}"


# ── Command-Parser (KI → PenKit Tool) ─────────────────────────────────────────

def parse_action(ai_response: str) -> list[dict]:
    """
    Parst ACTION: ... | PARAMS: ... aus dem KI-Output.
    Gibt Liste von ausführbaren Aktionen zurück.
    """
    actions = []
    pattern = r'ACTION:\s*(\w+(?::\w+)?)\s*\|\s*PARAMS:\s*(.+?)(?:\n|$)'
    for match in re.finditer(pattern, ai_response, re.MULTILINE):
        tool = match.group(1).strip()
        params = match.group(2).strip()
        actions.append({"tool": tool, "params": params})
    return actions


async def execute_action(
    tool: str,
    params: str,
    cfg: dict,
) -> AsyncGenerator[str, None]:
    """Führt eine KI-empfohlene Aktion aus."""
    from core.runner import CommandRunner
    runner = CommandRunner()

    tool_lower = tool.lower()

    if tool_lower == "scan:nmap" or tool_lower == "scan":
        yield f"[*] Starte Nmap: {params}"
        async for line in runner.run(["nmap", "-sV", "-O", "--script=vuln", params]):
            yield line

    elif tool_lower == "scan:vuln":
        yield f"[*] Vulnerability Scan: {params}"
        async for line in runner.run(["nmap", "--script=vulners,exploit", "-sV", params]):
            yield line

    elif tool_lower == "brute:hydra":
        parts = params.split()
        yield f"[*] Hydra Brute-Force: {params}"
        async for line in runner.run(["hydra"] + parts):
            yield line

    elif tool_lower == "web:sqlmap":
        yield f"[*] SQLmap: {params}"
        async for line in runner.run(["sqlmap", "--url", params, "--batch", "--level=3"]):
            yield line

    elif tool_lower == "web:nikto":
        yield f"[*] Nikto: {params}"
        async for line in runner.run(["nikto", "-h", params]):
            yield line

    elif tool_lower == "web:ffuf":
        yield f"[*] ffuf: {params}"
        parts = params.split()
        async for line in runner.run(["ffuf"] + parts):
            yield line

    elif tool_lower == "osint:harvest":
        yield f"[*] theHarvester: {params}"
        async for line in runner.run([
            "theHarvester", "-d", params, "-b", "google,bing,certspotter"
        ]):
            yield line

    elif tool_lower == "shell":
        yield f"[*] Shell: {params}"
        async for line in runner.run(params.split()):
            yield line

    elif tool_lower == "crack:hashcat":
        yield f"[*] Hashcat: {params}"
        wl = cfg.get("wordlist", "/usr/share/wordlists/rockyou.txt")
        async for line in runner.run(["hashcat", "--force", params, wl]):
            yield line

    elif tool_lower == "mitm:responder":
        yield f"[*] Responder: {params}"
        iface = params or cfg.get("interface", "eth0")
        async for line in runner.run(["responder", "-I", iface, "-rdwv"]):
            yield line

    else:
        yield f"[!] Tool '{tool}' nicht direkt ausführbar."
        yield f"[*] Manuell ausführen: {tool} {params}"


# ── Haupt-Terminal ─────────────────────────────────────────────────────────────

class AIAttackTerminal:
    """
    Interaktives AI-gestütztes Pentest-Terminal.

    Conversation Loop:
      1. Nutzer beschreibt Ziel
      2. KI analysiert und schlägt Angriff vor
      3. Nutzer bestätigt (oder modifiziert)
      4. PenKit führt aus
      5. Output geht zurück an KI
      6. KI analysiert und schlägt nächsten Schritt vor
      7. Weiter bis Ziel erreicht
    """

    def __init__(self, backend, cfg: dict):
        self.backend = backend
        self.cfg = cfg
        self.history: list[Message] = [Message("system", SYSTEM_PROMPT)]
        self.session_log: list[str] = []
        self.target_info: str = ""

    async def analyze(self, user_input: str) -> AsyncGenerator[str, None]:
        """Schickt User-Input an KI, gibt Antwort zurück."""
        self.history.append(Message("user", user_input))
        response_parts = []

        async for token in self.backend.chat(self.history):
            response_parts.append(token)
            yield token

        full_response = "".join(response_parts)
        self.history.append(Message("assistant", full_response))
        self.session_log.append(f"\n[USER] {user_input}\n[AI] {full_response}")

    def save_session(self) -> str:
        """Speichert die Session als Markdown-Report."""
        log_dir = out_dir("logs")
        from datetime import datetime
        fname = log_dir / f"ai_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        content = f"# PenKit AI Session\n\nTarget: {self.target_info}\n\n"
        content += "\n".join(self.session_log)
        with open(fname, "w") as f:
            f.write(content)
        return str(fname)


# ── Backend-Setup Helfer ──────────────────────────────────────────────────────

_KEY_FILE = os.path.expanduser("~/.penkit_ai_keys.json")


def save_keys(keys: dict):
    with open(_KEY_FILE, "w") as f:
        json.dump(keys, f, indent=2)
    os.chmod(_KEY_FILE, 0o600)


def load_keys() -> dict:
    if os.path.exists(_KEY_FILE):
        try:
            with open(_KEY_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


async def get_backend(preferred: str = "ollama") -> tuple:
    """Erstellt das beste verfügbare Backend."""

    keys = load_keys()

    if preferred == "claude" and keys.get("claude"):
        return ClaudeBackend(keys["claude"]), "claude"

    if preferred == "openai" and keys.get("openai"):
        return OpenAIBackend(keys["openai"]), "openai"

    # Ollama versuchen
    ollama = OllamaBackend()
    if await ollama.is_available():
        models = await ollama.get_models()
        if models:
            # Bevorzuge gute Pentest-Modelle
            for preferred_model in ["llama3.2", "llama3", "mistral", "codellama", "gemma2"]:
                for m in models:
                    if preferred_model in m.lower():
                        ollama.model = m
                        return ollama, f"ollama:{m}"
            ollama.model = models[0]
            return ollama, f"ollama:{models[0]}"
        return ollama, "ollama:kein-modell"

    return None, "none"
