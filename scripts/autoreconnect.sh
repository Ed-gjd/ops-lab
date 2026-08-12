#!/bin/bash
# 反向隧道自动重连脚本（VM 上运行）
# 用法：@reboot 触发 + 循环保活
export PATH=/usr/bin:/bin
LOG=/tmp/tunnel.log
while true; do
  /usr/bin/ssh -o BatchMode=yes \
               -o ServerAliveInterval=60 \
               -o ServerAliveCountMax=3 \
               -o StrictHostKeyChecking=accept-new \
               -i ~/.ssh/id_ed25519_tun \
               -N -R 0.0.0.0:8080:127.0.0.1:8000 \
               user@192.168.x.x
  echo "[$(date +%H:%M:%S)] tunnel died, reconnect in 5s" >> "$LOG"
  sleep 5
done
