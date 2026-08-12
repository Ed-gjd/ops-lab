# setup-key.ps1 - 把 VM 的隧道公钥安装到 Windows 管理员的 authorized_keys（需管理员）
$ErrorActionPreference = 'Stop'
Start-Transcript -Path 'C:\Users\<USER>\cc\key-setup.log' -Force

$keyFile = 'C:\Users\<USER>\cc\vm_key.pub'
$dest    = 'C:\ProgramData\ssh\administrators_authorized_keys'

if (-not (Test-Path $keyFile)) { Write-Output 'ERROR: vm_key.pub not found'; Stop-Transcript; exit 1 }

$key = (Get-Content $keyFile -Raw).Trim()
if (Test-Path $dest) { Remove-Item $dest -Force }
Set-Content -Path $dest -Value $key
icacls.exe $dest /inheritance:r /grant "Administrators:F" /grant "System:F"

Restart-Service sshd
Start-Sleep -Seconds 1
Write-Output "sshd: $((Get-Service sshd).Status)"
Write-Output 'KEY_INSTALLED'
Stop-Transcript
