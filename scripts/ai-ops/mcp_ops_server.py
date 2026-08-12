#!/usr/bin/env python3
"""
课4：自定义 MCP Server —— 把课3 的 check_disk 迁移成 MCP 工具
用 FastMCP 一行装饰器注册工具，跑 stdio 传输（本地进程间）
生命周期：client 连上来 -> tools/list 报工具 -> 模型选工具 -> tools/call 执行
"""
import subprocess

from fastmcp import FastMCP

mcp = FastMCP("ops-server")


@mcp.tool(
    name="check_disk",
    description="查询指定挂载点的磁盘使用情况。参数是挂载点路径，如 / 或 /data。路径不存在返回 ERROR。",
)
def check_disk(mount_point: str) -> str:
    """查询挂载点磁盘使用情况（真实执行 df -h）。"""
    r = subprocess.run(["df", "-h", mount_point], capture_output=True,
                       text=True, timeout=10)
    return r.stdout.strip() if r.returncode == 0 else f"ERROR: {r.stderr.strip()}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
