. "$PSScriptRoot\funcs.ps1"
$ErrorActionPreference = "Stop"
LoadServiceEnvVariables

Start-Service $env:TTL_WINDOWS_SERVICE_NAME
Write-Output "Service started..."