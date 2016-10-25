$PackageName = $env:chocolateyPackageName
$ServiceName = "consul-deployment-agent"
$InstallDirectory = "C:\TTLApps\consul-deployment-agent"


try {
    Write-Host "Checking if $ServiceName Windows service is already running..."
    $Service = Get-WmiObject -Class Win32_Service -Filter "Name='$ServiceName'"
    if ($Service) {
        Write-Host "$ServiceName Windows service is running, attempting to stop..."
        $Service.StopService()
        Sleep 5
        Write-Host "$ServiceName Windows service is stopped, attempting to delete..."
        $Service.Delete()
        Sleep 5
    }

    Write-Host "Deleting install directory $InstallDirectory..."
    Remove-Item $InstallDirectory -Recurse
}
catch {
  throw $_.Exception
}