param([switch]$Download)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$toolsRoot = Join-Path $repo '.tools'
$packages = @(
    @{
        Name = 'Gearsystem'
        Version = '3.9.18'
        Archive = 'Gearsystem-3.9.18-desktop-windows-x64.zip'
        Sha256 = '08e30d06a9c456da0cc6d75597cc59b57bfac7f2549c48c407b93354f1fd8162'
        Url = 'https://github.com/drhelius/Gearsystem/releases/download/3.9.18/Gearsystem-3.9.18-desktop-windows-x64.zip'
        Exe = 'gearsystem.exe'
    },
    @{
        Name = 'Copperline'
        Version = '1.0.0-rc.1'
        Archive = 'Copperline-1.0.0-rc.1-win-x64.zip'
        Sha256 = '03425ddaf18c5e6dc4fcdaa87b777551b868356c7cd9d3c2e96c870de5a997b2'
        Url = 'https://github.com/CopperlineHQ/Copperline/releases/download/v1.0.0-rc.1/Copperline-1.0.0-rc.1-win-x64.zip'
        Exe = 'copperline.exe'
    }
)

New-Item -ItemType Directory -Force -Path $toolsRoot | Out-Null
foreach ($package in $packages) {
    $archive = Join-Path $toolsRoot $package.Archive
    $destination = Join-Path $toolsRoot ($package.Name.ToLowerInvariant() + '-' + $package.Version)
    if (-not (Test-Path -LiteralPath $archive)) {
        if (-not $Download) {
            throw "Missing $archive. Rerun with -Download to fetch the pinned release."
        }
        $temporary = "$archive.partial"
        Invoke-WebRequest -Uri $package.Url -OutFile $temporary
        Move-Item -LiteralPath $temporary -Destination $archive
    }
    $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $package.Sha256) {
        throw "SHA-256 mismatch for $archive`: expected $($package.Sha256), got $actual"
    }
    if (-not (Test-Path -LiteralPath $destination)) {
        Expand-Archive -LiteralPath $archive -DestinationPath $destination
    }
    $executables = @(Get-ChildItem -LiteralPath $destination -Filter $package.Exe -File -Recurse)
    if ($executables.Count -ne 1) {
        throw "Expected one $($package.Exe) under $destination; found $($executables.Count)"
    }
    Write-Output "$($package.Name) $($package.Version): $($executables[0].FullName) (archive SHA-256 $actual)"
}
