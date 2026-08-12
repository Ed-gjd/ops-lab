#!/usr/bin/env bash
# =============================================================================
# WSL 环境初始化（运维学习前置依赖安装）
# 对应 PLAN.md §一「待装」清单。幂等：已装的跳过。
# 用法：bash env/setup-wsl.sh
# 说明：docker/helm/k3d 走官方脚本；其余走 apt；loki/promtail 二进制见 labs/grafana-stack/README.md
# =============================================================================
set -euo pipefail

is_installed() { command -v "$1" >/dev/null 2>&1; }
need_sudo() { [ "$(id -u)" -ne 0 ] && echo "sudo " || true; }
S="$(need_sudo)"

echo "==> [1/6] apt 更新 + 基础工具"
${S}apt-get update -qq
${S}apt-get install -y -qq \
  jq shellcheck \
  curl ca-certificates gnupg lsb-release \
  dnsutils iproute2 bridge-utils net-tools \
  openvswitch-switch || true   # openvswitch 缺就忽略，网络实验备用

echo "==> [2/6] Ansible"
if ! is_installed ansible; then
  ${S}apt-get install -y -qq ansible || \
  pip3 install --user ansible || \
  echo "  !! ansible 安装失败，手动装：sudo apt install ansible"
fi

echo "==> [3/6] Docker Engine（容器当节点 / k8s 用）"
if ! is_installed docker; then
  # 优先官方脚本；失败则退回 apt docker.io
  curl -fsSL https://get.docker.com | ${S}sh || ${S}apt-get install -y -qq docker.io
  ${S}usermod -aG docker "$USER" || true
  echo "  !! 重新登录（或 newgrp docker）后 docker 免 sudo"
fi

echo "==> [4/6] Helm（阶段6 k8s 用）"
if ! is_installed helm; then
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | ${S}bash || echo "  !! helm 安装失败，手动装"
fi

echo "==> [5/6] k3d / kind（阶段6 k3s 轻量集群，二选一即可）"
if ! is_installed k3d; then
  curl -fsSL https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | ${S}bash || echo "  !! k3d 安装失败"
fi
if ! is_installed kind; then
  [ "$(go version 2>/dev/null | awk '{print $3}' | cut -d. -f2)" -ge 21 ] 2>/dev/null && \
    go install sigs.k8s.io/kind@latest || \
    curl -fsSLo /tmp/kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64 && ${S}install -m755 /tmp/kind /usr/local/bin/kind || \
    echo "  !! kind 未装，k3d 已够用"
fi

echo "==> [6/6] 监控组件提示（阶段5/7）"
echo "  Prometheus/Node Exporter/Grafana：可用 Docker 跑（先完成步骤3），或二进制装"
echo "  Loki/Promtail：二进制已在 ~/grafana/，配置见 configs/，来源见 labs/grafana-stack/README.md"

echo
echo "==> 完成。验证："
for t in jq shellcheck ansible docker helm k3d; do
  is_installed "$t" && echo "  ✅ $t" || echo "  ⬜ $t（未装，看上面输出）"
done
echo
echo "  下一步：阶段0 环境体检 → PLAN.md 进度表"
