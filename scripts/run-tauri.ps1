$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopRoot = Join-Path $repoRoot "apps\desktop"

if (-not $env:LOCALAPPDATA) {
    throw "LOCALAPPDATA is required to configure Cargo's local cache."
}

# Cargo can fail to preserve crate mtimes when its registry cache is located
# on the repository's secondary filesystem. Keep the cache on the local
# Windows filesystem, matching the validated Tauri build configuration.
$env:CARGO_HOME = Join-Path $env:LOCALAPPDATA "orbit-cargo"
New-Item -ItemType Directory -Path $env:CARGO_HOME -Force | Out-Null

function Find-RustToolchainBin {
    $rustupHomes = @(
        $env:RUSTUP_HOME
        (Join-Path $env:USERPROFILE ".rustup")
        "E:\Rust\rustup"
    ) | Where-Object { $_ } | Select-Object -Unique

    foreach ($rustupHome in $rustupHomes) {
        $candidate = Join-Path $rustupHome `
            "toolchains\stable-x86_64-pc-windows-msvc\bin"
        if (
            (Test-Path (Join-Path $candidate "cargo.exe")) -and
            (Test-Path (Join-Path $candidate "rustc.exe"))
        ) {
            return $candidate
        }
    }

    throw "The stable Rust MSVC toolchain was not found. Install it with rustup before running the desktop app."
}

function Import-VisualStudioEnvironment {
    if (Get-Command link.exe -ErrorAction SilentlyContinue) {
        return
    }

    $vsDevCmd = $null
    $vswhere = Join-Path ${env:ProgramFiles(x86)} `
        "Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $visualStudioRoot = & $vswhere -latest -products * `
            -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
            -property installationPath
        if ($visualStudioRoot) {
            $candidate = Join-Path $visualStudioRoot "Common7\Tools\VsDevCmd.bat"
            if (Test-Path $candidate) {
                $vsDevCmd = $candidate
            }
        }
    }

    if (-not $vsDevCmd) {
        $candidate = "E:\VS\Product\Common7\Tools\VsDevCmd.bat"
        if (Test-Path $candidate) {
            $vsDevCmd = $candidate
        }
    }

    if (-not $vsDevCmd) {
        throw "Visual Studio C++ build tools were not found. Install the Desktop development with C++ workload."
    }

    $environmentLines = & cmd.exe /d /s /c `
        "`"$vsDevCmd`" -arch=x64 -host_arch=x64 >nul && set"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to initialize the Visual Studio C++ build environment."
    }

    foreach ($line in $environmentLines) {
        if ($line -match "^([^=]+)=(.*)$") {
            [Environment]::SetEnvironmentVariable(
                $Matches[1],
                $Matches[2],
                "Process"
            )
        }
    }
}

function Stop-ProcessTree {
    param([Parameter(Mandatory)][int]$ProcessId)

    $children = Get-CimInstance Win32_Process -Filter (
        "ParentProcessId = $ProcessId"
    ) -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId $child.ProcessId
    }

    if (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue) {
        Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    }
}

$toolchainBin = Find-RustToolchainBin
$env:PATH = "$toolchainBin;$env:PATH"
$env:RUSTC = Join-Path $toolchainBin "rustc.exe"

Import-VisualStudioEnvironment

Push-Location $desktopRoot
$tauriProcess = $null
try {
    $tauriParameters = @{
        FilePath = "npx.cmd"
        ArgumentList = @("tauri", "dev")
        WorkingDirectory = $desktopRoot
        NoNewWindow = $true
        PassThru = $true
    }
    $tauriProcess = Start-Process @tauriParameters
    $tauriProcess.WaitForExit()
    if ($tauriProcess.ExitCode -ne 0) {
        throw "Tauri development process exited with code $($tauriProcess.ExitCode)."
    }
}
finally {
    if ($tauriProcess -and -not $tauriProcess.HasExited) {
        Stop-ProcessTree -ProcessId $tauriProcess.Id
        $tauriProcess.WaitForExit()
    }
    Pop-Location
}
