. "$PSScriptRoot\funcs.ps1"
$ErrorActionPreference = "Stop"
LoadServiceEnvVariables

function create_healthchecks($checkType)
{
    $defaultsDir="${env:TTL_DEPLOYMENT_DIR}\..\defaults\healthchecks\$checkType"
    $workDir="${env:TTL_DEPLOYMENT_DIR}\..\work"
    $userDir="${env:TTL_DEPLOYMENT_DIR}\healthchecks\$checkType"

    $defaultYml = "$defaultsDir\healthchecks.yml"
    $userYml = "$userDir\healthchecks.yml"
    $workYml = "$workDir\healthchecks.yml"

    # Copy to work dir
    rm -Recurse $workDir -ErrorAction SilentlyContinue
    cp -Recurse $defaultsDir $workDir
    if (Test-Path $userDir){ cp -Recurse "$userDir\*" $workDir }

    # merge yaml
    [string[]] $lines = Get-Content $defaultYml
    $userLines = (LoadFileIfExists $userYml) -split "\r\n"

    $inBlock=$false;
    foreach($line in $userLines)
    {
        if((-not $inBlock) -and ($line.StartsWith("$($checkType)_healthchecks:"))) # entering block
        {
            $inBlock = $true;
        }
        elseif ($inBlock -and (-not $line.StartsWith(" "))) # leaving block
        {
            break;
        }
        elseif ($inBlock) # merging
        {
            $lines += $line;
        }
    }

    Set-Content -Path $workYml -Value $lines

    # Replace env variables
    Get-ChildItem -Recurse -File -Path $workDir | %{
        ReplaceEnvVarsInFile $_.FullName
    }

    # Apply changes
    rm -Recurse $userDir -ErrorAction SilentlyContinue
    mkdir "$userDir\.." -ErrorAction SilentlyContinue | Out-null
    mv $workDir $userDir
}

## Copy bin
$targetDir = $env:TTL_INSTALL_DIR
Write-Output "Copying source files to $targetDir..."
rm -Recurse -Force $targetDir -ErrorAction SilentlyContinue
mkdir $targetDir | Out-null
cp -Recurse "${env:DEPLOYMENT_BASE_DIR}\*" $targetDir

## Generate health checks
Write-Output "Generating health checks..."
create_healthchecks "sensu"
create_healthchecks "consul"

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
