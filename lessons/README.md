# 课程地图（lessons/）

> 以 **[PLAN.md](../PLAN.md)** 七阶段为骨架。每阶段配套的课程内容、实验、脚本归档在本仓库各处，这里给出映射。
> 学习方法：`docs/学习方法论与协作协议.md`（先读）。进度对照：`docs/学习进度存档-运维版.md`。

## 七阶段课程 → 内容资源

| 阶段 | 学什么 | 本仓库资源 |
|---|---|---|
| 阶段0 环境体检 | WSL 初始化、SSH 免密、VM 侧辅助 | [`env/setup-wsl.sh`](../env/setup-wsl.sh)、[`scripts/vm/`](../scripts/vm/) |
| 阶段1 Linux地基 | 目录/权限/用户/systemd/apt/journalctl/Git | PLAN.md §第一阶段、[`docs/archive/运维学习计划.md`](../docs/archive/运维学习计划.md) |
| 阶段2 系统管理 | 磁盘/LVM/cron/监控/日志/软件源/chrony | PLAN.md §第二阶段 |
| 阶段3 网络服务 | IP/防火墙/nginx/SSH隧道/排错 | PLAN.md §第三、五节、[`docs/archive/网络架构学习方案.md`](../docs/archive/网络架构学习方案.md) |
| 阶段3.5 多机搭建 | Docker 容器当节点、免密互连 | [`docs/阶段经验/阶段3.5多机搭建经验总结.md`](../docs/阶段经验/阶段3.5多机搭建经验总结.md) |
| 阶段4 Shell自动化 | 三剑客/jq/Git/脚本/日志轮转 | PLAN.md §第四阶段 |
| 阶段5 Ansible+监控 | Prometheus/Loki/Grafana、日志归档 | **[stage5-监控与日志/](stage5-监控与日志/)**（grafana-stack、log-archiver）、[`configs/`](../configs/) |
| 阶段6 容器云原生 | Docker/k3d/Helm/GitOps | PLAN.md §第六阶段 |
| 阶段7 高可用/SRE | 主从/PITR/加固/演练/混沌 | **[stage7-高可用与SRE/](stage7-高可用与SRE/)**、[`docs/阶段经验/`](../docs/阶段经验/) |
| 前沿 · AI 辅助运维 | Agentic SRE、MCP 运维、RAG 防幻觉 | [`docs/ai-ops/`](../docs/ai-ops/)、[`scripts/ai-ops/`](../scripts/ai-ops/) |

## 课程组织原则

- **阶段 = 课程主线**，实验/工具挂到对应阶段，不另起炉灶
- **只留运维**：AWS 云方向、SSH 专项、前端/驱动/AI 生成等独立方向不在本仓库（见 [`README.md`](../README.md) 外部仓库）
- **先方案后执行、命令全明文、每课验收** —— 铁律见 `docs/学习方法论与协作协议.md`
