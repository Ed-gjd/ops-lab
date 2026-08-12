# 阶段7 · 高可用 / 安全 / SRE

> 第7阶段是"扛得住"的分水岭。核心：**复制跑通 ≠ 恢复跑通**——只有真杀过一次主库、真 PITR 过一次才算会。

## 课程内容（真实实操，2026-08-05 验收全过）

| 主题 | 资源 |
|---|---|
| MySQL 主从复制 + PITR + 故障接管 | [`docs/阶段经验/阶段7-1-MySQL主从故障演练报告.md`](../../docs/阶段经验/阶段7-1-MySQL主从故障演练报告.md) |
| 安全加固清单（SSH/密钥/最小权限/防火墙/基线） | [`docs/阶段经验/阶段7-安全加固清单.md`](../../docs/阶段经验/阶段7-安全加固清单.md) |
| 总验收（nginx LB / Loki / OTel / eBPF / Agentic SRE） | [`docs/阶段经验/阶段7-总验收总结.md`](../../docs/阶段经验/阶段7-总验收总结.md) |
| 可观测性演练时间线（Loki/Promtail） | [`../stage5-监控与日志/grafana-stack/`](../stage5-监控与日志/grafana-stack/) |
| SRE 事故复盘（AI 辅助，模板化） | [`scripts/ai-ops/sre_postmortem.py`](../../scripts/ai-ops/sre_postmortem.py) |

## 四个真实坑（面试可讲）

1. **坐标抓错丢数据**：SHOW MASTER STATUS 的 pos 抄错 → 重放起点不对 → 重复键
2. **重放起点不对齐**：PITR 必须精确到 binlog 事件边界
3. **apt 包名撞车**：Ubuntu 里 `loki` 是生物信息软件，装 Loki 日志系统先撞包
4. **pkill -f 自杀**：模糊匹配把会话自己杀了

## 关键认知

- 复制跑通 ≠ 恢复跑通（真演练才算会）
- SLI/SLO/错误预算是 SRE 和传统运维的分水岭
- AI 复盘要人审（AI 会脑补细节）
