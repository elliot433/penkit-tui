"""Tests for the async CommandRunner."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pytest
from core.runner import CommandRunner, check_tool


class TestCommandRunner:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_echo_output(self):
        async def _t():
            r = CommandRunner()
            lines = []
            async for l in r.run(["echo", "hello penkit"]):
                lines.append(l)
            return lines
        lines = self._run(_t())
        assert any("hello penkit" in l for l in lines)

    def test_command_not_found(self):
        async def _t():
            r = CommandRunner()
            lines = []
            async for l in r.run(["this_command_does_not_exist_at_all_xyz"]):
                lines.append(l)
            return lines
        lines = self._run(_t())
        assert any("[ERROR]" in l for l in lines)

    def test_running_flag_resets(self):
        async def _t():
            r = CommandRunner()
            assert r.running is False
            lines = []
            async for l in r.run(["echo", "test"]):
                lines.append(l)
            assert r.running is False
        self._run(_t())

    def test_check_tool_found(self):
        async def _t():
            return await check_tool("echo")
        assert self._run(_t()) is True

    def test_check_tool_not_found(self):
        async def _t():
            return await check_tool("this_fake_tool_xyz_999")
        assert self._run(_t()) is False

    def test_multiline_output(self):
        async def _t():
            r = CommandRunner()
            lines = []
            async for l in r.run(["printf", "line1\nline2\nline3\n"]):
                lines.append(l)
            return lines
        lines = self._run(_t())
        assert len(lines) >= 3
