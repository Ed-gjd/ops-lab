# setup-ssh-server.ps1 - 反向隧道服务端配置（需管理员权限运行）
$ErrorActionPreference = 'Continue'
$log = 'C:\Users\<USER>\cc\sshd-setup.log'
Start-Transcript -Path $log -Force

# --- 1. 安装 OpenSSH Server（若未安装） ---
$cap = Get-WindowsCapability -Online | Where-Object { $_.Name -like 'OpenSSH.Server*' }
Write-Output "cap-state: $($cap.Name) = $($cap.State)"
if ($cap.State -ne 'Installed') {
    Write-Output 'installing OpenSSH.Server ...'
    Add-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0'
    Write-Output 'install done'
}

# --- 2. 服务自启 + 启动 ---
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
Write-Output "sshd service: $((Get-Service sshd).Status)"

# --- 3. sshd_config: GatewayPorts yes（在 Match 块之前插入） ---
$config = 'C:\ProgramData\ssh\sshd_config'
$lines = @(Get-Content $config)
$lines = $lines -replace '^#GatewayPorts no', 'GatewayPorts yes'
if (-not ($lines -match '^GatewayPorts\s+yes')) {
    $m = $lines | Select-String -Pattern '^Match' | Select-Object -First 1
    if ($m) {
        $i = $m.LineNumber - 1
        $lines = $lines[0..($i-1)] + 'GatewayPorts yes' + $lines[$i..($lines.Count-1)]
    } else {
        $lines = $lines + 'GatewayPorts yes'
    }
}
Set-Content -Path $config -Value $lines
Write-Output '--- GatewayPorts in sshd_config ---'
Select-String -Path $config -Pattern 'GatewayPorts'

# --- 4. 防火墙放行 22 / 8080 ---
Remove-NetFirewallRule -Name 'sshd-22' -ErrorAction SilentlyContinue
Remove-NetFirewallRule -Name 'sshd-8080' -ErrorAction SilentlyContinue
New-NetFirewallRule -Name sshd-22 -DisplayName 'OpenSSH Server (22)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
New-NetFirewallRule -Name sshd-8080 -DisplayName 'OpenSSH tunnel (8080)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 8080
Write-Output 'firewall rules: done'

# --- 5. 重启 sshd 使 GatewayPorts 生效 ---
Restart-Service sshd
Start-Sleep -Seconds 2
Write-Output "sshd after restart: $((Get-Service sshd).Status)"

Write-Output 'ALL_DONE'
