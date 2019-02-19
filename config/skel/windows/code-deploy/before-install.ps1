. "$PSScriptRoot\funcs.ps1"
$ErrorActionPreference = "Stop"

. "$PSScriptRoot\capture_em_env.ps1"
## Generate service.env file
Write-Output "Generating ${env:TTL_DEPLOYMENT_DIR}\service.env file..."
[string[]] $content = ReplaceEnvVars (Get-Content -Raw "${env:TTL_DEPLOYMENT_DIR}\misc\service.env")
$content += LoadFileIfExists "${env:TTL_DEPLOYMENT_DIR}\config\defaults.env"
$content += LoadFileIfExists "${env:TTL_DEPLOYMENT_DIR}\config\${env:TTL_ENVIRONMENT_TYPE}.env"
$content += LoadFileIfExists "${env:TTL_DEPLOYMENT_DIR}\config\${env:TTL_ENVIRONMENT}.env"
Set-Content -Path "${env:TTL_DEPLOYMENT_DIR}\service.env" -Value $content
cat ${env:TTL_DEPLOYMENT_DIR}\service.env

LoadServiceEnvVariables

## Preparing to install
Write-Output "Preparing to install $($env:TTL_SERVICE_NAME) ver. $($env:TTL_SERVICE_VERSION) on slice $($env:TTL_SERVICE_SLICE) (port $($env:TTL_SERVICE_PORT)) @ $($env:TTL_ENVIRONMENT)"

Write-Output "Deleting old version of the service, if any..."
Get-Service | Where-Object {$_.Name -eq $env:TTL_WINDOWS_SERVICE_NAME} | Stop-Service -PassThru | %{
  & sc.exe delete $_.Name
  if ($LastExitCode -ne 0) { throw "SC failed with code: $LASTEXITCODE." }
}
