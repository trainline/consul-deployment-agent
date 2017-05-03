param (
    [string]$BuildTarget
)

if(-not($BuildTarget)) { Throw "You must supply a value for -BuildTarget"}

function BundleIntoSingleExe {
    param(
        [string] $ExeName,
        [string] $ScriptPath,
        [string] $AdditionalPaths,
        [string] $ExeOutputDirectory
    )
    $LogLevel = "ERROR"
    $PyInstallerPath = "$TempDirectory\pyinstaller"

    & pyinstaller.exe --noconfirm --clean --log-level=$LogLevel `
        --workpath=$PyInstallerPath `
        --distpath=$ExeOutputDirectory `
        --specpath=$PyInstallerPath `
        --name=$ExeName `
        --paths=$AdditionalPaths `
        --onefile $ScriptPath
    if ($LASTEXITCODE -ne 0) {
        throw "Error creating single executable from $ScriptPath using PyInstaller."
    }
}

function CreateChocolateyPackage {
    param(
        [string] $PackageId,
        [string] $Version
    )
    $OutputDirectory = "$TempDirectory\output"
    $DataDirectory = "$OutputDirectory\data"

    Write-Host "Setting up $OutputDirectory for package staging..."
    New-Item $OutputDirectory -type directory

    Write-Host "Copying content of $RootDirectory\windows\chocolatey to temporary directory..."
    Copy-Item $RootDirectory\windows\chocolatey\* $OutputDirectory -Recurse

    Write-Host "Updating version in $OutputDirectory\package.nuspec to $Version..."
    $NuspecFile = @(Get-Item $OutputDirectory\package.nuspec)
    $Nuspec = [xml] (Get-Content $NuspecFile)
    $Nuspec.package.metadata.version = $Version
    $Nuspec.package.metadata.id = $PackageId
    $Nuspec.package.metadata.title = $PackageId
    $Nuspec.package.metadata.summary = $PackageId
    $Nuspec.package.metadata.tags = $PackageId
    $Nuspec.Save($NuspecFile)

    Write-Host "Packaging deployment agent code into a single executable..."
    BundleIntoSingleExe "consul-deployment-agent" "$RootDirectory\agent\core.py" "$RootDirectory\agent" $DataDirectory

    # Write-Host "Copying configuration file..."
    # Copy-Item $RootDirectory\config\config-logging-windows.yml $DataDirectory\config-logging.yml -Recurse

    Write-Host "Adding ignore files to all .exe files in $DataDirectory to avoid Chocolatey shimming..."
    $Files = get-childitem $DataDirectory -include *.exe -recurse
    foreach ($File in $Files) {
        New-Item "$File.ignore" -type file -force | Out-Null
    }

    Write-Host "Making sure Chocolatey is installed..."
    if ((Test-Path env:\CHOCOLATEYINSTALL) -and (Test-Path $env:CHOCOLATEYINSTALL)) {
        $ChocolateyPath = $env:CHOCOLATEYINSTALL
    }
    else {
        throw "Chocolatey is not installed."
    }

    Write-Host "Creating Chocolatey package with choco.exe..."
    Set-Location $OutputDirectory
    & choco pack package.nuspec
    if ($LASTEXITCODE -ne 0) {
        throw "Error creating Chocolatey package."
    }
    Set-Location $RootDirectory
}

try {
    Write-Host "Cleaning up temporary directory..."
    $RootDirectory = (Get-Item -Path ".\" -Verbose).FullName
    $TempDirectory = "$RootDirectory\temp"
    if (Test-Path $TempDirectory) {
        Remove-Item $TempDirectory -Recurse -Force
    }

    $PackageId = "ttl-consul-deployment-agent-" + $BuildTarget
    $Version = $env:BUILD_NUMBER
    if ($Version -eq $null) {
        Throw "Could not determine build version"
    }

    Write-Host "Creating Chocolatey package..."
    CreateChocolateyPackage $PackageId $Version
    Write-Host "Publishing disabled..."
}
catch {
    Write-Host "FATAL EXCEPTION: $_"
    exit 1
}
