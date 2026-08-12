# Grafana 可观测性实验区（Loki + Promtail）

> 阶段5/7 的可观测性实操。**二进制不入 git**，本目录只留来源说明 + 演练素材。

## 环境现状（WSL 实测 2026-08-05）

| 组件 | 状态 | 位置 |
|---|---|---|
| Loki | 二进制就位 | `~/grafana/loki/loki-linux-amd64`（v2026-07-22） |
| Promtail | 二进制就位 | `~/grafana/promtail/promtail-linux-amd64`（v2024-08-10） |
| 配置 | 已入库 | `configs/loki-config.yaml`、`configs/promtail-config.yaml` |

## 重新下载二进制（如丢失）

```bash
# Loki（日志聚合）
wget -O ~/grafana/loki.zip https://github.com/grafana/loki/releases/latest/download/loki-linux-amd64.zip
unzip -o ~/grafana/loki.zip -d ~/grafana/loki

# Promtail（日志采集 agent）
wget -O ~/grafana/promtail.zip https://github.com/grafana/loki/releases/latest/download/promtail-linux-amd64.zip
unzip -o ~/grafana/promtail.zip -d ~/grafana/promtail

chmod +x ~/grafana/loki/loki-linux-amd64 ~/grafana/promtail/promtail-linux-amd64
```

## 演练素材：scenario.log（一次 MySQL 主从故障演练时间线）

`scenario.log` 是 2026-08-05 阶段7 故障演练的 6 行完整日志，缝合了三条链路：

1. **主从故障切换**：备份（07:38:09）→ 主库宕机（07:40:29）→ failover 从库 3307 转正（07:40:30，**1 秒**）
2. **后端容灾**：backend B 被杀 → failover 到 A（07:44:00）
3. **日志与 PITR**：Loki 安装 apt 包名撞车解决（07:45:00，loki 是生物信息软件的坑）→ binlog 重放 PITR 恢复 2 行（07:46:00）

> 可用 `promtail` 采集本文件喂给 Loki 练 LogQL；也可以直接当"监控演练场景说明"读。
