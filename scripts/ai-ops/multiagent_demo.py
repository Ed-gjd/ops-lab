#!/usr/bin/env python3
"""
课7：多智能体编排 —— Planner(规划) -> Executor×N(执行) -> Summarizer(汇总)
全本地 LLM 编排，工具复用课6 白名单。对照：这相当于把一个人拆成
"组长(拆活) + 组员×N(干活) + 汇报人(汇总)"。
"""
import json
import os
import subprocess

from openai import OpenAI

client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"],
                base_url=os.environ["DASHSCOPE_BASE_URL"])
MODEL = os.environ.get("L3_MODEL", "qwen-plus")

# --- Executor 的工具：复用课6 白名单（精简版） ---
ALLOW = {"df", "free", "uptime", "ls", "cat", "systemctl", "journalctl",
         "grep", "ps", "top", "ss", "du", "stat", "date"}

def run_ops(command: str) -> str:
    first = command.strip().split()[0] if command.strip() else ""
    if first not in ALLOW or any(x in command for x in [";", "|", "&", ">", "<", "`"]):
        return f"PERMISSION_DENIED: {command}"
    try:
        return subprocess.run(command, shell=True, capture_output=True,
                              text=True, timeout=15).stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"

TOOLS = [{"type": "function", "function": {
    "name": "run_ops", "description": "执行只读运维命令（白名单）。",
    "parameters": {"type": "object",
                   "properties": {"command": {"type": "string"}},
                   "required": ["command"]}}}]

def llm(messages, tools=None):
    return client.chat.completions.create(
        model=MODEL, messages=messages, tools=tools).choices[0].message

# --- 三个角色 ---
def planner(task):
    m = llm([{"role": "system", "content": "你是任务规划 agent。把下面运维任务拆成不超过3个子任务，每行一个，只列子任务不执行。"},
             {"role": "user", "content": task}])
    return [l.strip(" -").strip() for l in m.content.splitlines() if l.strip()]

def executor(subtask):
    m = llm([{"role": "user", "content": subtask}], tools=TOOLS)
    if m.tool_calls:
        out = ""
        for tc in m.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            out += run_ops(args.get("command", "")) + "\n"
        return out.strip() or "（执行后无输出）"
    return m.content or "（模型未调工具）"

def summarizer(task, parts):
    body = "\n".join(f"[结果{i+1}]\n{r}" for i, r in enumerate(parts))
    m = llm([{"role": "system", "content": "你是汇总 agent。根据各结果用中文给出一份简洁最终报告。"},
             {"role": "user", "content": f"任务：{task}\n{body}"}])
    return m.content

def main():
    task = "检查这台机器的磁盘使用率和内存情况，然后汇总"
    print(f"任务：{task}\n")
    subs = planner(task)
    print(f"[Planner] 拆出 {len(subs)} 个子任务：")
    for s in subs:
        print(f"  - {s}")
    parts = []
    for i, sub in enumerate(subs):
        print(f"\n[Executor{i+1}] 执行：{sub}")
        res = executor(sub)
        print(f"   结果：{res[:150]}")
        parts.append(res)
    print("\n[Summarizer] 汇总：")
    print(summarizer(task, parts))


if __name__ == "__main__":
    main()
