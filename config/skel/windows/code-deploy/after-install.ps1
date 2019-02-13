. "$PSScriptRoot\funcs.ps1"
$ErrorActionPreference = "Stop"
LoadServiceEnvVariables

## Copy bin
$targetDir = $env:TTL_INSTALL_DIR
Write-Output "Copying source files to $targetDir..."
rm -Recurse -Force $targetDir -ErrorAction SilentlyContinue
mkdir $targetDir | Out-null
cp -Recurse "${env:DEPLOYMENT_BASE_DIR}\*" $targetDir

## Generate health checks
Write-Output "Generating health checks..."
ReplaceEnvVarsInFile "${env:TTL_DEPLOYMENT_DIR}\healthchecks\sensu\diagnostics_check.ps1"
ReplaceEnvVarsInFile "${env:TTL_DEPLOYMENT_DIR}\healthchecks\sensu\healthchecks.yml"
ReplaceEnvVarsInFile "${env:TTL_DEPLOYMENT_DIR}\healthchecks\consul\diagnostics_check.ps1"
ReplaceEnvVarsInFile "${env:TTL_DEPLOYMENT_DIR}\healthchecks\consul\healthchecks.yml"

## Installing Windows Service
Write-Output "Installing Windows Service ${env:TTL_WINDOWS_SERVICE_NAME}..."
& sc.exe create $env:TTL_WINDOWS_SERVICE_NAME "binpath=" "$targetDir\${env:TTL_SERVICE_EXE} --service" "obj=" ".\LocalSystem" "start=" "delayed-auto"
if ($LastExitCode -ne 0) { throw "SC failed with code: $LASTEXITCODE." }

& sc.exe failure $env:TTL_WINDOWS_SERVICE_NAME "reset=" "300" "actions=" "restart/0/restart/0/restart/180"
if ($LastExitCode -ne 0) { throw "SC failed with code: $LASTEXITCODE." }

## Configuring firewall
Write-Output "Creating firewall rule for ${env:TTL_WINDOWS_SERVICE_NAME} on port ${env:TTL_SERVICE_PORT}..."
& netsh advfirewall firewall add rule "name=${env:TTL_WINDOWS_SERVICE_NAME} - ${env:TTL_SERVICE_SLICE}" "dir=in" "action=allow" "protocol=TCP" "localport=${env:TTL_SERVICE_PORT}"
if ($LastExitCode -ne 0) { throw "NETSH failed with code: $LASTEXITCODE." }
