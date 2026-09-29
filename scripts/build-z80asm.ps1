param([switch]$Download)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$checkout = Join-Path $root '.tools\source\z80asm'
$expectedCommit = 'dc2406f5b920484025242d9896985744643eeb57'
$upstream = 'https://github.com/lvitals/z80asm.git'

if (-not (Test-Path -LiteralPath $checkout)) {
    if (-not $Download) { throw "Missing $checkout; rerun with -Download." }
    New-Item -ItemType Directory -Force (Split-Path $checkout) | Out-Null
    & git clone --filter=blob:none $upstream $checkout
    if ($LASTEXITCODE -ne 0) { throw 'git clone failed.' }
    & git -C $checkout checkout --detach $expectedCommit
    if ($LASTEXITCODE -ne 0) { throw "Could not check out pinned z80asm commit $expectedCommit." }
}

$actualCommit = (& git -C $checkout rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $actualCommit -ne $expectedCommit) {
    throw "Expected z80asm commit $expectedCommit, found $actualCommit. Inspect the checkout before building."
}
$sourceChanges = & git -C $checkout status --porcelain
if ($LASTEXITCODE -ne 0 -or $sourceChanges) { throw 'z80asm checkout has local changes; inspect them before building.' }

$vsRoot = 'C:\Program Files\Microsoft Visual Studio\2022\Community'
$vcvars = Join-Path $vsRoot 'VC\Auxiliary\Build\vcvars64.bat'
if (-not (Test-Path -LiteralPath $vcvars)) { throw "Missing VS 2022 x64 environment: $vcvars" }

New-Item -ItemType Directory -Force (Join-Path $root 'build\tools') | Out-Null
Push-Location $root
try {
    & cmd.exe /d /s /c "call `"$vcvars`" >nul && nmake /f tooling\z80asm-msvc\Makefile.nmake"
    if ($LASTEXITCODE -ne 0) { throw "nmake failed with exit code $LASTEXITCODE" }
    & (Join-Path $root 'build\tools\z80asm.exe') -V | Select-Object -First 1
    if ($LASTEXITCODE -ne 0) { throw 'z80asm version smoke failed.' }
} finally {
    Pop-Location
}
