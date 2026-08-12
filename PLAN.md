# 运维统一学习计划（小白 → 专家）

> **运行环境：WSL（Ubuntu-24.04，WSL2）**。本文档是把原《运维学习计划》《SSH学习计划》《网络架构学习方案》统一整合后的唯一主计划。
> 协作模式：Claude 当助手（vibe 工作法）。**遇问题先评估、提前说、不硬干卡死。**
> 版本：2026-08-12（统一整合版）

---

## 一、运行环境（WSL 基线，实测 2026-08-12）

**本机 = WSL Ubuntu-24.04 LTS**（WSL2，systemd 运行中，可用 systemctl）。

| 类别 | 工具 | 说明 |
|---|---|---|
| 已有 | git / curl / python3 / openssl / tmux | 基础 |
| 已有 | nginx / mariadb / mysqld | 阶段3/7 直接用 |
| 已有 | kubectl / terraform | 阶段5/6 用 |
| 待装 | docker（或 Docker Desktop）、ansible、jq、shellcheck、helm/k3d | 见 `env/setup-wsl.sh` |

**关键策略（WSL 单机跑多机）：**
- **多机阶段 → 用 Docker 容器当节点**（容器网络互连），替代原 VMware 克隆的 node1/2/3。
- **网络实验 → 用 `ip netns` / veth / bridge 手搓**（root 可用），练容器网络原理。
- **k8s → 用 k3d/kind**（Docker 内的轻量集群），单机跑全部节点。
- 原 VMware 拓扑文档（`docs/archive/`）保留作参考，不再作为主执行环境。

---

## 二、总纲（方法论铁律，所有阶段遵守）

1. **学的是"会折腾 + 会定位"，不是背命令**。知识长在动手上。
2. **先方案后执行**：破坏性/有风险操作先给方案（含回滚），确认后动手。
3. **每课验收**：有可测通过标准，过不了不进入下一课。
4. **不要重复**：已会内容直接跳，只补新的。
5. **保持最新**：涉及行业方向先调研当前成熟实践，不凭旧知识硬套。
6. **命令全明文**：每个要执行的命令先完整写出（含参数）→ 执行 → 输出全贴，绝不偷懒省略。
7. **vibe 循环**：直接讲 → 做 → 执行后解释 → 考问判断。不做"执行前让用户猜结果"。

---

## 三、主线（七阶段 + 支撑阶段）

```
阶段0 环境体检 → ①Linux地基 → ②系统管理 → ③网络服务 → [3.5 多机] → ④Shell自动化 → ⑤Ansible+监控 → ⑥容器云原生 → ⑦高可用/安全/SRE
(前置体检)     (看得懂)      (管得住)      (连得上)      (搭环境)    (会批量)     (自动化/看得见)   (会调度)     (扛得住)
```

### 阶段 0：环境体检与前置配置（1 次，30–60 分钟）
- 检查：SSH 是否连通、免密 sudo / SSH 免密是否配好、系统时间同步、磁盘水位、能否上网。
- 在 WSL 里：确认 `sudo -n true` 免密、`ssh-keygen` 生成密钥、`timedatectl` 时间同步、`df -h` 磁盘。
- **通过标准**：免密 sudo + SSH 密钥就绪 + 能联网 + 时间同步，防兜圈第一道墙砌好。

### 第一阶段：Linux 地基（2–3 周）
- **关键内容**：目录结构（/etc、/var、/usr…）、权限（chmod/chown/sudo）、用户与组、进程与 systemd（自己写 .service 单元）、apt、journalctl、**Git 基础**。
- **WSL 落地**：全部原生可做 ✅。systemd 可用（`systemctl --user` / 需 `systemctl` 有 pid1）。
- **验收**：不用查资料用 SSH 密钥登录；看懂一条服务自启配置；能重装一个出错的包。

### 第二阶段：系统管理（2–3 周）
- **关键内容**：磁盘分区与挂载（lsblk/fdisk/fstab）、LVM、cron 与 systemd timer、资源监控（top/free/df）、日志分析、软件源、chrony 时间同步。
- **WSL 落地**：注意 **WSL 虚拟磁盘不建议乱分区/fdisk**——磁盘是 vhdx 虚拟盘；分区/挂载练习用 **loop 设备或 Docker 容器**模拟。
- **验收**：能定位"磁盘 90% 是哪个进程在写"；定时任务设定并验证。

### 第三阶段：网络服务 + 网络架构模块（3–4 周）
- **关键内容**：IP/掩码/网关/NAT/DNS 原理、CIDR 手算、防火墙（ufw/iptables 概念）、nginx 反代、SSH 隧道与跳板、排错工具（ping/traceroute/ss/curl）。
- **网络架构专项模块（并入）**：netns → veth → bridge → VXLAN → NAT/DNAT 手搓；CNI 选型；eBPF/Cilium；零信任；Service Mesh 判断框架（10 课，见 `docs/archive/网络架构学习方案.md`）。
- **WSL 落地**：`ip netns`+veth+bridge **需 root**，WSL 内可用（`sudo`）；防火墙层面 WSL 是 NAT 网络，iptables 实验做 netns 内的即可。
- **验收**：从本机用 SSH 隧道访问 WSL 内部服务；按分层顺序排查一次"nginx 连不上"；手搓一对 veth 互联。

### 阶段 3.5：多机搭建（3–5 天）——从 1 台到 N 台
- **关键内容**：Docker 网络（bridge/host/自定义网络）、容器当节点、SSH 进容器、多容器互通。
- **WSL 落地**：**用 Docker 容器替代物理 VM**——建 3 个 ubuntu 容器当 node1/2/3，配 sshd，互通 + 出外网。
- **验收**：从控制容器能免密 SSH 到所有节点；node2 的 nginx 能被 node3 curl 到。

### 第四阶段：Shell 自动化（3–4 周）——第一个分水岭
- **关键内容**：bash 基础、管道与三剑客（grep/awk/sed）+ jq、Git 正式课、退出码与 set -e、脚本参数、日志轮转。
- **WSL 落地**：原生可做 ✅（装 jq）。备份脚本、批量处理直接用 WSL。
- **验收**：写自动备份脚本（保留最近 7 份、带错误处理）；用循环批量改 10 个文件。

### 第五阶段：Ansible + 监控（4–6 周）——第二个分水岭，SRE 门槛
- **关键内容**：Ansible 架构/inventory/playbook/role/幂等性；Prometheus + Node Exporter + Alertmanager + Grafana；进阶 OpenTofu + Python。
- **WSL 落地**：**控制端 = WSL，被管端 = Docker 容器（sshd）**；监控组件原生可跑。
- **验收**：Ansible 一条命令给 3 个容器装好 nginx 且幂等；Prometheus 监控所有节点，宕一个能看到告警。

### 第六阶段：容器与云原生（4–6 周）
- **关键内容**：Docker（镜像/容器/网络/数据卷/Dockerfile/compose）、Helm、k8s 核心概念（Pod/Deployment/Service/Ingress）、HPA/KEDA、GitOps 入门（Argo CD）。
- **WSL 落地**：Docker 原生；k8s 用 **k3d 或 kind**（Docker 内集群）；Helm 装 k3d 集群。
- **验收**：把一个应用打成镜像跑起来；k3d 集群部署一个服务滚动更新不中断；配 HPA 压测看扩容。

### 第七阶段：高可用 / 安全 / SRE（3 个月以上）
- **关键内容**：负载均衡（nginx/HAProxy）、MySQL 主从与备份恢复（PITR）、故障演练（混沌）、安全加固、日志收集（Loki + Promtail，明确不跑 ELK）、OpenTelemetry 概念、eBPF 观测（Falco/Cilium）、AI 辅助运维（Agentic SRE）、SRE 方法论（SLI/SLO）。
- **WSL 落地**：MySQL 主从已在本机 WSL 跑通过一轮 ✅（mariadb 3306/3307）；Loki/Promtail 二进制已在 `~/grafana/`。
- **验收**：MySQL 主从故障 10 分钟内恢复；杀节点演练写总结；出一份安全加固清单并落实。

---

## 四、SSH 七级穿插表

| SSH 级别 | 内容 | 落在哪个阶段 |
|---|---|---|
| L1–L2 | 登录/密钥/config | 第一阶段 |
| L3 | 隧道/跳板/加固 | 第三阶段 |
| L4 | 协议/自动化 | 第四、五阶段 |
| L5–L7 | PKI/前沿/信任模型 | 第七阶段安全 |

以 SSH 为主线练"远程管理"，以七阶段练"业务能力"，交叉验证。

---

## 五、网络问题排查预案（重点）

### 5.1 分层定位法
```
① 自己层   网卡有 IP 吗？接口 up 吗？          → ip a
② 链路层   ping 得通网关吗？                   → ip route / ping 网关
③ 网络层   ping 得通外网 IP 吗？               → ping 223.5.5.5
④ DNS      域名能解析吗？                      → ping 域名 / resolvectl query
⑤ 端口/应用 目标端口在听吗？防火墙挡了吗？      → ss -tlnp / curl / ufw status
```

**一步定位口诀**：
| 现象 | 结论 |
|---|---|
| 能 ping 通 IP，不能 ping 通域名 | **DNS 问题** |
| 内网通，外网不通 | **网关 / 路由 / NAT 问题** |
| 别人能通，只有自己不通 | **防火墙 / 端口 / 服务没起** |
| 网络全通，服务还是怪 | **大概率不是网络**，查磁盘/内存/时间 |

**8 步自查**：`ip a` → `ip route` → `ping 网关` → `ping 223.5.5.5` → `ping 域名` → `ss -tlnp` → `curl -v http://127.0.0.1:<端口>` → 防火墙状态。

**伪装成网络问题的非网络问题**（最坑，先查）：
| 假象 | 真凶 | 一分钟验证 |
|---|---|---|
| SSH 连不上/服务起不来/各种怪错 | **磁盘满了** | `df -h`（也看 `df -i`） |
| 连接被重置/进程莫名消失 | **内存不足被 OOM** | `free -h` |
| 证书/握手错 | **时间不同步** | `timedatectl`，配 chrony |

---

## 六、防兜圈协议（安全/权限/交互协作铁律）

**前置（一次配齐）**：WSL 免密 sudo（NOPASSWD）、SSH 密钥免密、known_hosts 用 accept-new 预填、常规命令加权限白名单。

**协作约定**：
1. 安全相关任务**先出预案再执行**：方案 + 回滚 + 需批准点，一次性确认，不中途反复问。
2. **能非交互就非交互**：免密、`-o BatchMode`、参数化命令、改配置文件代替交互工具。
3. **要密码提前说**：三方案（向用户要密码 / 配免密绕过 / 用户手动执行）。
4. **3 次升级机制**：失败 1 次自解决；2 次停止猜，贴"报错原文 + 相关配置 + 环境状态"三件套；3 次降级半自动。
5. **高危操作边界**：清防火墙/删数据/关安全/对外攻击性操作仍须确认，但"一次问清不绕"。

---

## 七、每日实操节奏（1 小时）
1. **前 10 分钟**：Claude 大白话讲今天概念 + 出一个练习。
2. **中间 40 分钟**：执行练习，出错进调试循环（贴报错 → 先解释 → 再修）。
3. **后 10 分钟**：3 句话总结 + 3 道复述题，答不上明天重学。

---

## 八、进度追踪表

| 阶段 | 验收标准 | 状态 |
|---|---|---|
| 0 环境体检 | 免密 sudo + SSH 密钥 + 联网 + 时间同步 | ⬜ WSL 待过 |
| 1 Linux地基 | SSH 密钥登录 + 看懂服务自启 + 重装出错包 | ⬜ |
| 2 系统管理 | 定时任务 + 定位磁盘写满真凶 | ⬜ |
| 3 网络服务 | SSH 隧道访问 + 分层排错 + 手搓 veth | ⬜ |
| 3.5 多机 | Docker 容器节点互连 + 免密管理 | ⬜ |
| 4 Shell | 备份脚本(7份) + 批量改 10 文件 | ⬜ |
| 5 Ansible+监控 | 3 容器幂等装 nginx + Prometheus 告警 | ⬜ |
| 6 容器云原生 | 镜像跑起 + k3d 滚动更新 + HPA | ⬜ |
| 7 高可用/SRE | MySQL 主从 10 分钟恢复 + 演练总结 + 加固清单 | 🟡 VM 上过过，WSL 待系统化 |

> 进度明细见 `docs/学习进度存档-运维版.md`。历史经验见 `docs/阶段经验/`。

---

## 九、2026 前沿（实时雷达，原则：方向性知识入课，名词了解即可）
1. **Agentic SRE / AI 辅助运维** ⭐：Gartner 预测 2029 年 85% 企业用 AI SRE 工具。关键不是模型多聪明，是"护栏 + 可信"。本计划从第一天就在练"人定护栏、AI 执行"。
2. **OpenTofu**：开源 IaC 默认选项，语法与 Terraform 兼容，阶段 5 学它。
3. **OpenTelemetry**：观测事实标准（指标/日志/链路三合一），阶段 7 一个概念 + 一个 Demo。
4. **GitOps**：Argo CD / Flux，阶段 6 最小案例。
5. **eBPF**：Cilium / Falco，阶段 7 概念 + 装一个看效果。
6. **供应链安全**（SBOM/SLSA）：阶段 7 一笔带过。

---

## 十、相关资源
- `README.md`：仓库总览与目录导航
- `lessons/`：课程主体（按阶段编排），课程地图见 `lessons/README.md`
  - `stage5-监控与日志/`：grafana-stack（Loki/Promtail 可观测 + 演练时间线）、log-archiver（日志归档工具）
  - `stage7-高可用与SRE/`：主从演练 / 安全加固 / 总验收 / SRE 复盘索引
- `docs/`：方法论（`学习方法论与协作协议.md`）、进度存档（`学习进度存档-运维版.md`）、原计划归档（`archive/`）、阶段经验（`阶段经验/`）、AI 运维（`ai-ops/`）
- `env/setup-wsl.sh`：WSL 环境初始化（装缺失工具，幂等）
- `configs/`：loki/promtail 监控配置
- `scripts/`：`vm/`（Windows 侧 VM 辅助脚本 + 公钥）、`ai-ops/`（MCP 运维 / 值班助手 / 监控模拟 / SRE 复盘）、`autoreconnect.sh`、`vm_monitor.sh`
- 外部独立仓库（不并入）：`ssh-learning-lab`、`aws-course`、`bailian-learning`
