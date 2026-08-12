#!/usr/bin/env python3
"""值班助手：一个真正能用的 AI 运维工具
一条命令搞定：自然语言查系统 / 看图 / 画图 / 语音汇报，全程白名单安全 + 成本记账

用法：
  python ops_assistant.py ask "node1 磁盘多少"        # 查系统（白名单工具）
  python ops_assistant.py look <图片路径>             # 看图分析
  python ops_assistant.py diagram "<描述>"            # 画示意图
  python ops_assistant.py speak "<文字>"              # 语音播报
  python ops_assistant.py report                      # 本次记账
"""
import base64
import json
import os
import subprocess
import sys

from openai import OpenAI

import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from paths import CC, WIN_ROOT, VENV_PY

MODEL = os.environ.get("OPS_MODEL", "qwen3.7-plus")
COST_FILE = "/tmp/cc/ops_cost.json"

# ---------- 安全白名单（只读命令）----------
ALLOW = {"df", "free", "uptime", "ls", "cat", "systemctl", "journalctl",
         "grep", "ps", "top", "ss", "du", "stat", "date", "hostname", "whoami", "id"}
DENY = ["rm", "shutdown", "reboot", "sudo", "mkfs", "fdisk", "kill", "chmod", "dd", ">", "<", "|", ";", "&", "`"]


def guarded_run(command: str) -> str:
    """执行白名单只读命令，危险词全拦。"""
    first = command.strip().split()[0] if command.strip() else ""
    if first not in ALLOW:
        return f"PERMISSION_DENIED: {first} 不在白名单"
    if any(x in command for x in DENY):
        return "PERMISSION_DENIED: 含危险操作/符号"
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        return (r.stdout or r.stderr).strip()
    except Exception as e:
        return f"ERROR: {e}"


def record_cost(tokens: int):
    data = {}
    if os.path.exists(COST_FILE):
        data = json.load(open(COST_FILE))
    data["tokens"] = data.get("tokens", 0) + tokens
    data["calls"] = data.get("calls", 0) + 1
    json.dump(data, open(COST_FILE, "w"))


def client():
    return OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"], base_url=os.environ["DASHSCOPE_BASE_URL"])


# ---------- 1. 自然语言查系统 ----------
TOOLS = [{"type": "function", "function": {"name": "run_ops",
    "description": "执行只读运维命令（白名单：df/free/uptime/ls/cat/systemctl/journalctl/grep/ps/ss/du 等）。",
    "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}]


def ask(question: str) -> str:
    """自然语言 → agent 用白名单工具查 → 回答。"""
    c = client()
    messages = [{"role": "user", "content": question}]
    total = 0
    for _ in range(5):
        r = c.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, max_tokens=300)
        total += r.usage.total_tokens
        msg = r.choices[0].message
        if not msg.tool_calls:
            record_cost(total)
            return msg.content or "(空)"
        messages.append(msg)
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            result = guarded_run(args.get("command", ""))
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    record_cost(total)
    return "（超过轮数）"


# ---------- 2. 看图 ----------
def look(image_path: str, question: str = "这张图说明了什么？一句话") -> str:
    c = client()
    b64 = base64.b64encode(open(image_path, "rb").read()).decode()
    r = c.chat.completions.create(model="qwen3-vl-plus", messages=[
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": question}]}], max_tokens=150)
    record_cost(r.usage.total_tokens)
    return r.choices[0].message.content


# ---------- 3. 画图 ----------
def diagram(prompt: str) -> str:
    out = subprocess.run(["dashscope", "image-generation", "create",
                          "-m", "qwen-image-3.0-pro", "-t", prompt, "--size", "1024*1024"],
                         capture_output=True, text=True, timeout=240).stdout
    url = None
    for ln in out.splitlines():
        ln = ln.strip()
        if not ln.startswith("{"):
            continue
        try:
            d = json.loads(ln)
        except Exception:
            continue
        ch = d.get("choices") or []
        if ch and ch[0].get("message", {}).get("content"):
            for item in ch[0]["message"]["content"]:
                if isinstance(item, dict) and item.get("image"):
                    url = item["image"]
                    break
        if url:
            break
    if not url:
        return f"ERROR: {out[:120]}"
    os.makedirs("/tmp/cc/assist", exist_ok=True)
    import urllib.request
    path = "/tmp/cc/assist/diagram.png"
    urllib.request.urlretrieve(url, path)
    return f"已保存 {path}"


# ---------- 4. 语音 ----------
def speak(text: str) -> str:
    subprocess.run([f"{CC}/.venv/bin/python", f"{CC}/realtime/voice_io.py",
                    "play", text], timeout=90)
    return "已播报"


# ---------- 5. 记账 ----------
def report() -> str:
    if not os.path.exists(COST_FILE):
        return "本次还没有调用。"
    d = json.load(open(COST_FILE))
    return f"累计 {d.get('calls', 0)} 次调用 / {d.get('tokens', 0)} tokens"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "ask":
        print(ask(" ".join(sys.argv[2:]) or "检查根目录磁盘使用率，一句话"))
    elif cmd == "look":
        print(look(sys.argv[2], " ".join(sys.argv[3:]) or "这张图说明了什么？一句话"))
    elif cmd == "diagram":
        print(diagram(" ".join(sys.argv[2:])))
    elif cmd == "speak":
        print(speak(" ".join(sys.argv[2:])))
    elif cmd == "report":
        print(report())
    else:
        print(f"未知命令 {cmd}")
