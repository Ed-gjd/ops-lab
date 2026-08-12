#!/usr/bin/env python3
"""
课6：带安全边界的运维 MCP Server
三层防线：
  1. 命令白名单（只读运维命令才放行）
  2. 危险操作/管道/重定向/反引号 -> PERMISSION_DENIED
  3. kill switch（OPS_GUARD_KILLED=1 全停）+ 日志脱敏（密钥打码）
改远程靶机时：把 subprocess.run 换成 paramiko ssh 执行同一白名单即可。
"""
import os
import re
import subprocess

from fastmcp import FastMCP

mcp = FastMCP("ops-guard")

# 白名单：只放行这些命令（首词匹配）
ALLOW = {"df", "free", "uptime", "ls", "cat", "systemctl", "journalctl",
         "grep", "ps", "top", "ss", "netstat", "uname", "whoami", "id",
         "du", "date", "stat", "hostname"}
# 危险词/符号：rm fdisk mkfs shutdown reboot dd kill chmod sudo 管道重定向反引号
DENY_RE = re.compile(
    r"\b(rm|fdisk|mkfs|shutdown|reboot|poweroff|dd|kill|pkill|chmod|chown|mv|sudo)\b"
    r"|[><;&|`$()]"
)
# 密钥/密码脱敏（\S+ 吞掉整段非空白，避免尾巴泄露）
SECRET_RE = re.compile(r"(AKID\S+|sk-\S+|password\s*[=:]\s*\S+|secret\s*[=:]\s*\S+)", re.I)


def masked(text):
    return SECRET_RE.sub("[MASKED]", text)


@mcp.tool(
    name="run_ops",
    description=("执行受白名单保护的只读运维命令。仅允许：df/free/uptime/ls/cat/"
                 "systemctl status/journalctl/grep/ps/top/ss/du/stat/uname 等。"
                 "删除、写入、改权限、关机、管道重定向都会被拒绝。"),
)
def run_ops(command: str) -> str:
    # 3. 防线：kill switch
    if os.environ.get("OPS_GUARD_KILLED") == "1":
        return "AGENT_OFFLINE: 该 agent 已下线（kill switch 触发），全部操作拒绝"
    # 1. 防线：白名单首词
    first = command.strip().split()[0] if command.strip() else ""
    if first not in ALLOW:
        return f"PERMISSION_DENIED: 命令 '{first}' 不在白名单"
    # 2. 防线：危险词/管道/重定向
    if DENY_RE.search(command):
        return "PERMISSION_DENIED: 命令含危险操作或管道/重定向，只读白名单拒绝"
    if first == "systemctl" and not command.strip().startswith("systemctl status"):
        return "PERMISSION_DENIED: systemctl 仅允许 status 查询"
    try:
        r = subprocess.run(command, shell=True, capture_output=True,
                           text=True, timeout=15)
        return masked((r.stdout or r.stderr).strip())
    except Exception as e:
        return f"ERROR: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
