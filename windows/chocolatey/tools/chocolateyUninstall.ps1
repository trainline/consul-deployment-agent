$PackageName = $env:chocolateyPackageName
$ServiceName = "consul-deployment-agent"
$InstallDirectory = "C:\TTLApps\consul-deployment-agent"
$LogFile = "C:\TTLLogs\consul-deployment-agent-uninstall.log"
$Start = Get-Date

Add-Content $LogFile "---- Consul Deployment Agent Uninstall ----"
Add-Content $LogFile "Process started at $Start"

try {
    Write-Host "Checking if $ServiceName Windows service is already running..."
    Add-Content $LogFile "Checking if $ServiceName Windows service is already running..."
    $Service = Get-WmiObject -Class Win32_Service -Filter "Name='$ServiceName'"
    if ($Service) {
        Write-Host "$ServiceName Windows service is running, attempting to stop..."
        Add-Content $LogFile "$ServiceName Windows service is running, attempting to stop..."
        $Service.StopService()
        Sleep 5
        Write-Host "$ServiceName Windows service is stopped, attempting to delete..."
        Add-Content $LogFile "$ServiceName Windows service is stopped, attempting to delete..."
        $Service.Delete()
        Sleep 5
    }

    Write-Host "Deleting install directory $InstallDirectory..."
    Add-Content $LogFile "Deleting install directory $InstallDirectory..."
    Remove-Item $InstallDirectory -Recurse
}
catch {
  throw $_.Exception
  Add-Content $LogFile "ERROR: $($_.Exception)"
}

$End = Get-Date
Add-Content $LogFile "Process completed at $End"