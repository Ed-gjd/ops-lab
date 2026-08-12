# 学习环境运维知识库

## 主机拓扑
node1（node1-gw-20）：外网 192.168.56.20 / 内网 192.168.56.20，角色=网关+防火墙+NAT，内存 1G。
node2（node2-lb-30）：外网 192.168.56.30，角色=nginx 负载均衡，内存 1G。
node3（node3-ctl-40）：内网 192.168.56.40，角色=控制端/监控，内存 2G。

## 网络架构
外网 VMnet8(169.0/24) + 内网 VMnet2(170.0/24)。node1 双网卡做 NAT 网关，node3 在内网经 node1 出外网，node3 免密 SSH 到 node1/node2。

## 集群
k3s 集群：master=192.168.56.133，agent=node1(192.168.56.20)、node2(192.168.56.30)，版本 v1.36.2+k3s1。
k3s 的 containerd 不共享 Docker 加速器，需单独配 /etc/rancher/k3s/registries.yaml。

## 告警策略
磁盘使用率超过 80% 触发警告。node 宕机时 Alertmanager 发出告警。
