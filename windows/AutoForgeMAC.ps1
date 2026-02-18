if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$TargetName = "以太网" # 目标网卡名称

# 1. 获取网卡的驱动描述 (用于匹配注册表)
$adapter = Get-NetAdapter -Name $TargetName
$driverDesc = $adapter.InterfaceDescription

# 2. 生成随机 MAC (第二位为 2,6,A,E)
$secondChar = ("2", "6", "A", "E" | Get-Random)
$rest = (1..10 | ForEach-Object { "{0:X}" -f (Get-Random -Min 0 -Max 16) }) -join ""
$newMac = "0" + $secondChar + $rest

Write-Host "网卡: $TargetName" -ForegroundColor Cyan
Write-Host "驱动: $driverDesc" -ForegroundColor Gray
Write-Host "新 MAC: $newMac" -ForegroundColor Yellow

# 3. 遍历注册表找到匹配驱动描述的路径
$basePath = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"
$subKeys = Get-ChildItem -Path $basePath | Where-Object { $_.PSChildName -match "^\d{4}$" }

$found = $false
foreach ($key in $subKeys) {
    $desc = Get-ItemPropertyValue -Path $key.PSPath -Name "DriverDesc" -ErrorAction SilentlyContinue
    if ($desc -eq $driverDesc) {
        # 找到匹配路径，写入新 MAC
        Set-ItemProperty -Path $key.PSPath -Name "NetworkAddress" -Value $newMac
        $found = $true
        Write-Host "已更新注册表路径: $($key.PSPath)" -ForegroundColor Green
        break
    }
}

if (-not $found) {
    Write-Error "未能在注册表中找到该网卡的配置路径。"
    pause; exit
}

# 4. 重启网卡
Write-Host "正在重启网卡以应用更改..."
Disable-NetAdapter -Name $TargetName -Confirm:$false
Enable-NetAdapter -Name $TargetName -Confirm:$false

Write-Host "修改完成！当前 MAC 状态：" -ForegroundColor Green
Get-NetAdapter -Name $TargetName | Select-Object Name, MacAddress, Status | Format-Table
pause
