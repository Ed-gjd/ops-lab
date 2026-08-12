#!/usr/bin/env python3
"""
阶段7-6：Agentic SRE —— 用 AI 做事故复盘（postmortem）
输入：一次明确标注"演练"的故障时间线；输出：现象→影响→根因→处理→改进
（演练数据，非真实生产事故）
"""
import os

from openai import OpenAI

client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"],
                base_url=os.environ["DASHSCOPE_BASE_URL"])
MODEL = os.environ.get("L3_MODEL", "qwen-flash")

INCIDENT = """【演练】某电商后端 2026-08-05 故障时间线：
14:00 磁盘使用率 82%（超过 80% 告警阈值），Prometheus 告警发出
14:05 值班开始排查，发现 / 分区被日志文件占满
14:12 定位到应用日志无轮转策略，单文件已 60G
14:20 手动清理旧日志 + 配置 logrotate 轮转，磁盘回落到 45%
14:30 恢复，共耗时 30 分钟
（演练设定：告警延迟 +5 分钟、排障走弯路 +7 分钟、修复 +8 分钟）"""

SYSTEM = ("你是 SRE 事故复盘专家。按固定模板输出复盘报告，每节用一两句，中文，"
          "只基于给定时间线，不编造额外事实。模板："
          "【现象】【影响】【根因】【处理过程】【改进措施】【SLO 影响】")

r = client.chat.completions.create(model=MODEL, messages=[
    {"role": "system", "content": SYSTEM},
    {"role": "user", "content": INCIDENT}])
print("=== AI 事故复盘（演练） ===")
print(r.choices[0].message.content)
