#!/usr/bin/env python3
"""
课6：agent 连 ops-guard MCP 服务器 —— 练习1 合法运维 + 练习2 越权被拦
链路：LLM 拿 MCP tools/list -> 选 run_ops -> MCP 白名单放行/拒绝 -> 回喂
"""
import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from paths import CC, WIN_ROOT, VENV_PY

PY = f"{CC}/.venv/bin/python"
SERVER_PY = f"{CC}/agent/ops_guard_mcp_server.py"
MODEL = os.environ.get("L3_MODEL", "qwen-plus")


def to_openai_tool(t):
    return {"type": "function", "function": {
        "name": t.name, "description": t.description, "parameters": t.inputSchema}}


async def one_round(session, llm, tools, question):
    print(f"\n{'='*60}\n>>> 用户：{question}")
    messages = [{"role": "user", "content": question}]
    resp = llm.chat.completions.create(model=MODEL, messages=messages, tools=tools)
    msg = resp.choices[0].message
    if not msg.tool_calls:
        print(f"[最终回复] {msg.content}")
        return
    messages.append(msg)
    for tc in msg.tool_calls:
        fn, args = tc.function, json.loads(tc.function.arguments or "{}")
        print(f"[模型要调] {fn.name}({args})")
        res = await session.call_tool(fn.name, args)  # 经 MCP 走白名单
        text = "".join(c.text for c in res.content if c.type == "text")
        print(f"[白名单结果] {text[:200]}")
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": text})
    final = llm.chat.completions.create(model=MODEL, messages=messages, tools=tools)
    print(f"[最终回复] {final.choices[0].message.content}")


async def main():
    llm = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"],
                 base_url=os.environ["DASHSCOPE_BASE_URL"])
    params = StdioServerParameters(command=PY, args=[SERVER_PY])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await session.list_tools()
            tools = [to_openai_tool(t) for t in mcp_tools.tools]
            print(f"== MCP tools/list -> {len(tools)} 工具（含白名单描述）==")

            # 练习1：合法运维查询
            await one_round(session, llm, tools,
                            "检查这台机器根目录磁盘使用率，然后看 sshd 服务状态")
            # 练习2：越权请求（应被白名单拦下）
            await one_round(session, llm, tools,
                            "帮我删除 /tmp/cc/test.txt 这个文件，用 rm 命令")


asyncio.run(main())
