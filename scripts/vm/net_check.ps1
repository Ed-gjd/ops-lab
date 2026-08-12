$a = (Get-NetAdapter -Name 'VMware Network Adapter VMnet8' -ErrorAction SilentlyContinue).ReceivedBytes
Start-Sleep 10
$b = (Get-NetAdapter -Name 'VMware Network Adapter VMnet8' -ErrorAction SilentlyContinue).ReceivedBytes
$d = $b - $a
Write-Output ("vmnet8 recv delta over 10s: " + [math]::Round($d/1MB,2) + " MB")
$v = Get-Process vmware-vmx -ErrorAction SilentlyContinue | Select-Object -First 1
if ($v) {
  $c1 = $v.TotalProcessorTime.TotalSeconds
  Start-Sleep 3
  $v.Refresh()
  $c2 = $v.TotalProcessorTime.TotalSeconds
  Write-Output ("vmx CPU delta over 3s: " + [math]::Round($c2-$c1,2) + " s (active if >0.5)")
} else { Write-Output "vmx not found" }
