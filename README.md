# ops-lab · 运维统一学习仓库

> WSL（Ubuntu-24.04）单机从零学运维：**小白 → 专家**。
> 主计划看 **[PLAN.md](PLAN.md)**（七阶段统一路线）。课程地图看 **[lessons/README.md](lessons/README.md)**。
> 协作模式：Claude 当助手，**先方案后执行、命令全明文、每课验收**（[docs/学习方法论与协作协议.md](docs/学习方法论与协作协议.md)）。

---

## 目录导航

| 路径 | 内容 |
|---|---|
| `PLAN.md` | **统一主计划**：七阶段 + SSH 穿插 + 网络排错预案 + 防兜圈协议 |
| `lessons/` | **课程主体**（按阶段编排）→ [课程地图](lessons/README.md) |
| `docs/` | 方法论 / 进度存档 / 原计划归档 / 阶段经验 / AI 运维文档 |
| `scripts/` | 运维脚本：`vm/`（Windows 侧 VM 辅助）、`ai-ops/`（AI 运维）、autoreconnect/vm_monitor |
| `configs/` | loki / promtail 监控配置 |
| `env/` | `setup-wsl.sh` WSL 环境初始化（幂等） |

## 课程主体 lessons/ 一览

| 目录 | 阶段 | 内容 |
|---|---|---|
| `stage5-监控与日志/` | 5 | **grafana-stack**（Loki+Promtail 可观测、演练时间线）、**log-archiver**（日志归档工具） |
| `stage7-高可用与SRE/` | 7 | 主从演练 / 安全加固 / 总验收 / SRE 复盘（引用 docs/阶段经验） |

其余阶段（0-6）的课程大纲在 `PLAN.md`，实操经验在 `docs/阶段经验/`，脚本在 `scripts/`。

## 快速开始

```bash
# 1. 环境体检 + 装缺的依赖
bash env/setup-wsl.sh

# 2. 对照进度
cat docs/学习进度存档-运维版.md

# 3. 开课：对 Claude 说「开始学阶段X第N课」→ 按方法论推进
```

## 外部独立仓库（运维相邻，不并入本仓库）

| 仓库 | 内容 |
|---|---|
| `../ssh-learning-lab` | SSH 7 阶段课程（登录→隧道→加固→PKI→前沿，全✅） |
| `../aws-course` | AWS 云课程（VPC/EC2/S3/Lambda/EKS/IaC/AgentCore） |
| `../bailian-learning` | 阿里云百炼 AI 学习（Agent/MCP/Realtime） |
