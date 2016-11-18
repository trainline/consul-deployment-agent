$PackageName = $env:chocolateyPackageName
$PackageVersion = $env:chocolateyPackageVersion
$PackageDirectory = $env:chocolateyPackageFolder
$ServiceName = "consul-deployment-agent"
$InstallDirectory = "C:\TTLApps\consul-deployment-agent"
$LogFile = "C:\TTLLogs\consul-deployment-agent-install.log"
$Start = Get-Date

Add-Content $LogFile "---- Consul Deployment Agent Install ----"
Add-Content $LogFile "Process started at $Start"

try {
    Write-Host "Checking if $ServiceName Windows service is already running..."
    Add-Content $LogFile "Checking if $ServiceName Windows service is already running..."
    $Service = Get-WmiObject -Class Win32_Service -Filter "Name='$ServiceName'"
    if ($Service) {
        Write-Host "$ServiceName Windows service is running, attempting to stop..."
        Add-Content $LogFile "$ServiceName Windows service is running, attempting to stop..."
        $Attempts = 0
        while ($Service.Started) {
          if ($Attempts -gt 5) {
            throw "Failed to stop $ServiceName Windows service after $Attempts attempts."
            Add-Content $LogFile "Failed to stop $ServiceName Windows service after $Attempts attempts."
          }
          $Service.StopService() | Out-Null
          ++$Attempts
          Write-Host "Waiting for existing $ServiceName Windows service to stop `#$($Attempts)..."
          Add-Content $LogFile "Waiting for existing $ServiceName Windows service to stop `#$($Attempts)..."
          Sleep 5
          $Service = Get-WmiObject -Class Win32_Service -Filter "Name='$ServiceName'"
        }
    }

    Write-Host "Checking if install directory $InstallDirectory exists..."
    Add-Content $LogFile "Checking if install directory $InstallDirectory exists..."
    if (-Not (Test-Path $InstallDirectory)) {
        Write-Host "Creating install directory $InstallDirectory..."
        Add-Content $LogFile "Creating install directory $InstallDirectory..."
        New-Item $InstallDirectory -type directory
    }
    else {
        Write-Host "Cleaning up install directory $InstallDirectory..."
        Add-Content $LogFile "Cleaning up install directory $InstallDirectory..."
        Remove-Item $InstallDirectory\* -Recurse
    }

    Write-Host "Copying files from $PackageDirectory to $InstallDirectory..."
    Add-Content $LogFile "Copying files from $PackageDirectory to $InstallDirectory..."
    Copy-Item $PackageDirectory\data\*.exe $InstallDirectory -Force
    Copy-Item $PackageDirectory\data\*.yml $InstallDirectory -Force

    $NssmExe = "$InstallDirectory\nssm.exe"
    if ($Service) {
        Write-Host "Deleting $ServiceName Windows service using nssm..."
        Add-Content $LogFile "Deleting $ServiceName Windows service using nssm..."
        Start-ChocolateyProcessAsAdmin "remove $ServiceName confirm" $NssmExe
        Sleep 2
    }

    Write-Host "Installing $ServiceName as a Windows service using nssm..."
    Add-Content $LogFile "Installing $ServiceName as a Windows service using nssm..."
    $ConsulDeploymentAgentExe = "$InstallDirectory\consul-deployment-agent.exe"
    Start-ChocolateyProcessAsAdmin "install $ServiceName $ConsulDeploymentAgentExe -config-dir=$InstallDirectory" $NssmExe
    Start-ChocolateyProcessAsAdmin "set $ServiceName DisplayName Consul Deployment Agent" $NssmExe
    Start-ChocolateyProcessAsAdmin "set $ServiceName Description Manages deployment of applications based on configuration found in Consul key-value store." $NssmExe
    #Start-ChocolateyProcessAsAdmin "set $ServiceName Start SERVICE_AUTO_START" $NssmExe
    #Start-ChocolateyProcessAsAdmin "set $ServiceName AppExit Default Ignore" $NssmExe
    #Start-ChocolateyProcessAsAdmin "failure $ServiceName reset= 86400 actions= restart/60000/restart/60000/none/60000" "sc.exe"

    Write-Host "Starting $ServiceName Windows service..."
    Add-Content $LogFile "Starting $ServiceName Windows service..."
    Start-Service $ServiceName
}
catch {
  throw $_.Exception
  Add-Content $LogFile "ERROR: $($_.Exception)"
}

$End = Get-Date
Add-Content $LogFile "Process completed at $End"