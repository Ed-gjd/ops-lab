Write-Host "=== 1. 创建外部虚拟交换机 (桥接到 USB 有线网卡) ===" -ForegroundColor Cyan

# 获取 USB 有线网卡
$adapter = Get-NetAdapter | Where-Object { $_.Name -like "*USB*Ethernet*" -or $_.InterfaceDescription -like "*USB*Ethernet*" -or $_.Name -eq "以太网 2" }

if (-not $adapter) {
    # 试试找 192.168.10.x 的物理网卡
    $adapter = Get-NetAdapter | Where-Object { $_.Status -eq "Up" -and $_.MacAddress -eq "6C-1F-F7-EA-AE-A6" }
}

if (-not $adapter) {
    Write-Host "没找到 USB 有线网卡，列出所有已连接的网卡:" -ForegroundColor Yellow
    Get-NetAdapter | Where-Object Status -eq Up | Select-Object Name, InterfaceDescription, MacAddress, LinkSpeed | Format-Table -AutoSize
    exit 1
}

Write-Host "找到网卡: $($adapter.Name) - $($adapter.InterfaceDescription)" -ForegroundColor Green

# 检查是否已存在
$existing = Get-VMSwitch -Name "WSL-Bridge" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "虚拟交换机 WSL-Bridge 已存在，先删除..." -ForegroundColor Yellow
    Remove-VMSwitch -Name "WSL-Bridge" -Force
}

# 创建外部交换机 (这会断网一下，会自动恢复)
Write-Host "创建外部虚拟交换机 WSL-Bridge ..." -ForegroundColor Yellow
New-VMSwitch -Name "WSL-Bridge" -NetAdapterName $adapter.Name -AllowManagementOS $true -Notes "WSL2 桥接用"
Write-Host "虚拟交换机创建成功!" -ForegroundColor Green

Write-Host "`n=== 2. 查看新的 vEthernet (WSL-Bridge) IP ===" -ForegroundColor Cyan
Start-Sleep -Seconds 3
Get-NetIPAddress -InterfaceAlias "vEthernet (WSL-Bridge)" -AddressFamily IPv4 | Select-Object IPAddress, PrefixLength, InterfaceAlias

Write-Host "`n=== 3. 验证网络连通性 ===" -ForegroundColor Cyan
Test-Connection 192.168.10.21 -Count 1 -Quiet

Write-Host "`n=== 完成! ===" -ForegroundColor Green
Write-Host "接下来需要修改 .wslconfig 并重启 WSL，请继续下一步。" -ForegroundColor Cyan
