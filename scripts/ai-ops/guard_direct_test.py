#!/usr/bin/env python3
"""课6 硬验证：绕过 LLM 直打 MCP，证明服务器侧白名单/脱敏/kill switch 真拦截。"""
import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from paths import CC, WIN_ROOT, VENV_PY

PY = f"{CC}/.venv/bin/python"
SERVER_PY = f"{CC}/agent/ops_guard_mcp_server.py"


async def run(env, cases, title):
    print(f"\n{'='*64}\n{title}")
    params = StdioServerParameters(command=PY, args=[SERVER_PY], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for cmd in cases:
                res = await session.call_tool("run_ops", {"command": cmd})
                text = "".join(c.text for c in res.content if c.type == "text")
                print(f"  cmd: {cmd}\n    -> {text}\n")


async def main():
    base = dict(os.environ)
    await run(base, ["rm -rf /tmp/cc/test.txt",
                     "cat /etc/passwd | rm -rf /",
                     "ls /tmp; reboot",
                     "df -h /"], "=== 白名单+危险符号拦截（含合法对照）===")
    await run(base, ["cat /tmp/cc/secret.txt"],
              "=== 日志脱敏（需要先造一个含密钥的文件）===")
    await run({**base, "OPS_GUARD_KILLED": "1"}, ["df -h /"],
              "=== kill switch 触发后全停 ===")


asyncio.run(main())
