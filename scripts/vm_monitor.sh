#!/bin/bash
VMRUN="/c/Program Files (x86)/VMware/VMware Workstation/vmrun.exe"
LOG="/d/VM/Ubuntu24/install_monitor.log"
START=$(date +%s)
MAX_MIN=120
: > "$LOG"
echo "$(date '+%H:%M:%S') monitor started" >> "$LOG"
while true; do
  NOW=$(date +%s)
  ELAPSED=$(( (NOW-START)/60 ))
  if ! "$VMRUN" list 2>/dev/null | grep -q "ubuntu24.vmx"; then
    echo "$(date '+%H:%M:%S') VM_POWERED_OFF after ~${ELAPSED} min" >> "$LOG"
    exit 0
  fi
  SIZE=$(stat -c %s "/d/VM/Ubuntu24/ubuntu24.vmdk" 2>/dev/null)
  echo "$(date '+%H:%M:%S') running ${ELAPSED}min vmdk=$((SIZE/1048576))MB" >> "$LOG"
  if [ "$ELAPSED" -ge "$MAX_MIN" ]; then
    echo "$(date '+%H:%M:%S') TIMEOUT after ${MAX_MIN} min" >> "$LOG"
    exit 1
  fi
  sleep 60
done
