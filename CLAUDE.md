# PenKit TUI — Claude Code Instructions

## Projekt
Pentesting-Framework für autorisierte Geräte. Kali Linux in VirtualBox.
- **Kali-Pfad:** `~/penkit-tui`
- **Windows-Pfad:** `C:\root\Documents\penkit-tui`
- **GitHub:** `https://github.com/elliot433/penkit-tui`
- **Starten:** `python3 classic_menu.py`

## Hardware
- ALFA AWUS036ACH (rtw88 Treiber) → bleibt als `wlan0` im Monitor Mode (NICHT `wlan0mon`)
- Kali in VirtualBox auf Windows 11

## Code-Regeln

### Async Generators
- `stop()` Methoden NIEMALS `yield` verwenden → macht sie zu AsyncGenerators, nicht awaitbar
- `async def` mit `yield` = AsyncGenerator → nur mit `async for` iterierbar, nie mit `await`
- Rückgabe-Annotation: wenn `yield` → `AsyncGenerator[str, None]`, wenn `return` → konkreter Typ

### Tools müssen echte Arbeit leisten
- Kein Dummy-Output, kein `print("TODO")`, kein simuliertes Ergebnis
- Jedes Tool das einen CLI-Befehl verspricht MUSS `runner.run([...])` oder `subprocess` aufrufen
- Bei fehlendem Binary: `shutil.which()` prüfen + klare Fehlermeldung mit Install-Hinweis

### Imports
- Fehlende Imports sofort hinzufügen
- Standard: `from core.runner import CommandRunner`, `from core.output_dir import get as out_dir`

## Nach jedem Fix
```bash
git add <geänderte_datei>
git commit -m "Fix: <was war kaputt>"
git push origin main
```

## Installierte Tools auf Kali
- apt: aircrack-ng, reaver, wash, mdk4, bettercap, responder, nmap, sqlmap, ffuf, hydra, hashcat, john, bloodhound, netexec, socat, hostapd, dnsmasq, subfinder, amass
- go: dalfox (~/.go/bin/dalfox) — PATH: `export PATH=$PATH:~/.go/bin`
- pip3: instaloader, pypykatz, websockets
- Wordlist: `/usr/share/wordlists/rockyou.txt`

## Bekannte Bugs (bereits gefixt)
1. `amsi_bypass.py` war leer → neu geschrieben
2. `handshake.py` fehlte `import asyncio`
3. `telegram_agent.py` here-string Einrückung (textwrap.dedent Bug)
4. `deauth.py` stop() hatte yield → async generator Bug
5. `wps.py` BeaconFlood.stop() yield Bug + wash `-o` ohne Dateiname
6. `auto_combo.py` falsche Annotation AsyncGenerator statt bool
7. `kahoot.py` fake WebSocket-Join → echte CometD/Bayeux Implementierung

## Menü-Tasten
| Taste | Funktion |
|-------|----------|
| 1 | WiFi Attacks |
| 2 | Network Intelligence |
| 3 | Web Attacks |
| 4 | Passwords & Hashes |
| 5 | MITM |
| 6 | OSINT Recon |
| 7 | Phishing Suite |
| 8 | Blue Team |
| 9 | C2 / RAT |
| N | Anonymität & OPSEC |
| W | Active Directory |
| P | Post-Exploitation |
