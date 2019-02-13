. "$PSScriptRoot\funcs.ps1"
$ErrorActionPreference = "Stop"
LoadServiceEnvVariables

Stop-Service $env:TTL_WINDOWS_SERVICE_NAME
Write-Output "Service stopped"