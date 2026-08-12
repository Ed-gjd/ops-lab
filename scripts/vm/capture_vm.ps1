Add-Type -AssemblyName System.Drawing
$src = @"
using System;
using System.Runtime.InteropServices;
public class W {
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint f);
    public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
Add-Type -TypeDefinition $src
$p = Get-Process vmware -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*Ubuntu24*" } | Select-Object -First 1
if (-not $p) { Write-Output "NO_WINDOW"; exit 1 }
$r = New-Object W+RECT
[W]::GetWindowRect($p.MainWindowHandle, [ref]$r) | Out-Null
$w = $r.Right - $r.Left
$h = $r.Bottom - $r.Top
if ($w -le 0 -or $h -le 0) { Write-Output "BAD_RECT $w $h"; exit 1 }
$bmp = New-Object System.Drawing.Bitmap($w, $h)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
[W]::PrintWindow($p.MainWindowHandle, $hdc, 2) | Out-Null
$g.ReleaseHdc($hdc)
$g.Dispose()
$bmp.Save("C:\Users\<USER>\cc\vm_screen.png")
$bmp.Dispose()
Write-Output "SAVED ${w}x${h}"
