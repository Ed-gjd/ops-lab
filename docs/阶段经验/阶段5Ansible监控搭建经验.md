# 阶段 5：Ansible + 监控搭建——经验总结（2026-08-02）

> 从"会写脚本"到"自动化管多台机器"的第二个分水岭。控制端 `.133` 一控两管（node1/node2），Prometheus 采集、Grafana 出图。
> 配合《运维学习计划.md》阶段5 使用。

---

## 一、最终架构（当前监控栈）

```
控制端 .133 (<practice-vm>, 192.168.x.x)
├── Ansible 2.16.3          → 管 node1/node2（免密+become）
├── Prometheus 2.45.3       → 9090 端口，抓取 node1/2 的 :9100
└── Grafana 13.1.1          → 3000 端口（默认 admin/admin）

被管端：
├── node1 (192.168.56.20) → prometheus-node-exporter :9100
└── node2 (192.168.56.30) → prometheus-node-exporter :9100
```

**节点职责**：node1/node2 只当"被管端"装 exporter；控制端 .133 是"指挥中心"。node3 本阶段未参与（无网关依赖）。

---

## 二、完整操作链

### 1. 开机被管端
```bash
vmrun start "D:\VM\node1\node1.vmx" nogui
vmrun start "D:\VM\node2\node2.vmx" nogui
# 等 ~50 秒，静态 IP 不担心变化
```

### 2. 打通 SSH 免密（控制端 → 被管端）
```bash
# .133 上：
echo <VM密码> | sudo -S apt-get install -y sshpass    # 装 sshpass 非交互传密码
ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519       # 生成密钥
sshpass -p <VM密码> ssh-copy-id -o StrictHostKeyChecking=no user@192.168.x.x
sshpass -p <VM密码> ssh-copy-id -o StrictHostKeyChecking=no user@192.168.x.x
# 验证：
ssh -o BatchMode=yes user@192.168.x.x hostname
```
> **教训**：`.133` 的 sudo 没配免密，靠 `echo 密码 | sudo -S` 解决交互卡死（防兜圈）。

### 3. 装 Ansible + inventory
```bash
echo <VM密码> | sudo -S apt-get install -y ansible
mkdir -p ~/ansible && cd ~/ansible
# inventory.ini:
# [webservers]
# node1 ansible_host=192.168.x.x
# node2 ansible_host=192.168.x.x
# [all:vars]
# ansible_user=pc
# ansible_python_interpreter=/usr/bin/python3
ansible -i inventory.ini all -m ping    # → node1/node2 都 pong
```

### 4. playbook 装 node_exporter（幂等演示）
```yaml
# install-node-exporter.yml
---
- name: 给所有被管端装 node_exporter
  hosts: all
  become: yes
  tasks:
    - name: 确保 node_exporter 已安装
      apt:
        name: prometheus-node-exporter
        state: present
        update_cache: yes
    - name: 确保 node_exporter 在运行
      service:
        name: prometheus-node-exporter
        state: started
        enabled: yes
```
```bash
ansible-playbook -i inventory.ini install-node-exporter.yml
# 第1次: changed=1（真装）→ 第2次: changed=0（幂等）
```

### 5. Prometheus
```bash
echo <VM密码> | sudo -S apt-get install -y prometheus
sudo cp /etc/prometheus/prometheus.yml /etc/prometheus/prometheus.yml.bak   # 改前备份
# prometheus.yml:
# global: {scrape_interval: 15s}
# scrape_configs:
#   - job_name: nodes
#     static_configs:
#       - targets: ['192.168.x.x:9100', '192.168.x.x:9100']
sudo systemctl restart prometheus
curl -s 'http://127.0.0.1:9090/api/v1/targets' | jq '.data.activeTargets | length'   # → 2
```

### 6. Grafana（换阿里源是关键！）
```bash
# 官方源直连 25KB/s 慢到卡死 → 换阿里镜像：
sudo cp /etc/apt/sources.list.d/grafana.list /etc/apt/sources.list.d/grafana.list.bak
echo "deb [signed-by=/usr/share/keyrings/grafana.gpg] https://mirrors.aliyun.com/grafana/apt/ stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt-get update && sudo apt-get install -y grafana   # 阿里源 1 秒拉包
sudo systemctl start grafana-server && sudo systemctl enable grafana-server
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000   # → 302（登录页）
```

---

## 三、踩坑与教训（重点）

### 坑 1：grafana 官方源直连国内慢到死（25KB/s）
- **教训**：国内环境，grafana/其他国外源先测速再等。**直接换阿里镜像**（`mirrors.aliyun.com/grafana/apt`），1 秒拉到 500KB 包。
- **验证技巧**：`curl -sI https://镜像/dists/stable/Release` 看 HTTP 200/403 再决定用哪个。

### 坑 2：`sudo tee` 把密码写进文件
- `echo 密码 | sudo tee 文件` → 密码串进了文件第一行（Malformed line）
- **正确**：`echo 密码 | sudo -S bash -c 'echo "..." > 文件'`，把重定向放 bash -c 内部

### 坑 3：`pgrep -f 'apt-get install grafana'` 误判
- grep/pgrep 会匹配到包含同字符串的**自身命令**，误报"还在下载"
- **正确**：用 `ps aux | grep -E 'apt|dpkg' | grep -v grep` 确认

### 坑 4：Grafana 启动慢，sleep 5 后看端口会误判"没起来"
- Grafana 首次启动要初始化 DB/模块（日志 "All modules healthy" 前需要几十秒）
- **正确**：`systemctl status` 看 Active 状态，或 sleep 10+ 再看端口

### 坑 5：VM 访问不到宿主机代理（127.0.0.1 隔离）
- 本机 PandaFan 只监听 127.0.0.1，VM 经 NAT 够不着宿主机 loopback
- 这次用换源绕过了；如确需代理，要 netsh 端口转发（需管理员）或改代理监听地址

---

## 四、核心概念（本阶段必须吃透）

| 概念 | 一句话 | 本次体现 |
|---|---|---|
| 控制端/被管端/inventory | 指挥员/士兵/点名册 | `.133` + node1/2 + inventory.ini |
| 幂等性 | 跑 N 遍结果一样，只补差异 | 第1次 changed → 第2次 ok |
| 声明式 vs 命令式 | 说"要什么状态" vs "执行什么动作" | playbook vs 手动 apt install |
| 采集→出图闭环 | 采集/存储/展示三段 | exporter → Prometheus → Grafana |

---

## 五、遗留 / 待办

- [ ] Grafana 里加 Prometheus 数据源 + 建一个仪表盘（出图还没配，只到"可达"）
- [ ] Alertmanager 告警未配（宕机告警 = 阶段5验收的最后一个缺口）
- [ ] node3 未参与本阶段（如要练"跨网关被管"可加 node3，需 node1 网关开着）
- [ ] 控制端 .133 建议打 L1 快照（现在它上面装了整套监控栈，是重要资产）

---

## 六、给未来的一句话

**自动化 = 让机器替我重复，监控 = 让机器替我看。** Ansible 记住"幂等"两个字：声明要什么、别管怎么到。Prometheus 记住"采集→出图"闭环：数据从哪来、存到哪、怎么画出来。这两条线就是运维的左右手。
