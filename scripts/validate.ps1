[CmdletBinding()]
param(
    [ValidateSet("Backend", "Desktop", "Tauri", "All")]
    [string]$Scope = "All",

    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$TaskFile
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repoRoot "apps\backend"
$desktopRoot = Join-Path $repoRoot "apps\desktop"
$testDatabaseUrl = "postgresql+psycopg://orbit:orbit@localhost:5432/orbit_test"
$originalDatabaseUrl = $env:ORBIT_DATABASE_URL
$initialTrackedState = @()

function Require-Command {
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [string]$InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found. $InstallHint"
    }
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory)]
        [string]$Label,

        [Parameter(Mandatory)]
        [string]$Command,

        [Parameter(Mandatory)]
        [string[]]$Arguments,

        [Parameter(Mandatory)]
        [string]$WorkingDirectory
    )

    Write-Host "`n==> $Label" -ForegroundColor Cyan
    Push-Location $WorkingDirectory
    try {
        & $Command @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$Label failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

function Get-RepositorySnapshot {
    $trackedFiles = & git -C $repoRoot ls-files --cached
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to list tracked files in the Git worktree."
    }
    $trackedSet = @{}
    foreach ($trackedFile in $trackedFiles) {
        $trackedSet[$trackedFile] = $true
    }

    $repositoryFiles = & git -C $repoRoot ls-files `
        --cached --others --exclude-standard
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to list versioned and local files in the Git worktree."
    }

    $snapshot = foreach ($file in $repositoryFiles) {
        $fullPath = Join-Path $repoRoot $file
        if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
            $worktreeHash = & git -C $repoRoot hash-object -- $file
            if ($LASTEXITCODE -ne 0) {
                throw "Unable to hash repository file '$file'."
            }
        }
        else {
            $worktreeHash = "<deleted>"
        }

        if ($trackedSet.ContainsKey($file)) {
            $indexHash = & git -C $repoRoot rev-parse ":$file"
            if ($LASTEXITCODE -ne 0) {
                throw "Unable to inspect the index state for '$file'."
            }
        }
        else {
            $indexHash = "<not-in-index>"
        }

        "$file`t$indexHash`t$worktreeHash"
    }
    return @($snapshot | Sort-Object)
}

function Assert-TaskSpec {
    param([Parameter(Mandatory)][string]$Path)

    $resolvedPath = Resolve-Path -LiteralPath $Path -ErrorAction Stop
    $taskRoot = [System.IO.Path]::GetFullPath(
        (Join-Path $repoRoot "dev-workflow\tasks")
    ).TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
        [System.IO.Path]::DirectorySeparatorChar
    $resolvedTaskPath = [System.IO.Path]::GetFullPath($resolvedPath.Path)
    if (-not $resolvedTaskPath.StartsWith(
        $taskRoot,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Task specs must be stored under '$taskRoot'."
    }

    $content = Get-Content -LiteralPath $resolvedPath -Raw
    $frontMatterMatch = [regex]::Match(
        $content,
        "(?s)\A---\s*\r?\n(?<metadata>.*?)\r?\n---\s*\r?\n"
    )
    if (-not $frontMatterMatch.Success) {
        throw "Task spec '$resolvedPath' must begin with YAML front matter."
    }

    $metadata = @{}
    foreach ($line in ($frontMatterMatch.Groups["metadata"].Value -split "\r?\n")) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        if ($line -notmatch "^([a-z_]+):\s*(\S.*)$") {
            throw "Task spec '$resolvedPath' has invalid metadata line '$line'."
        }
        $key = $Matches[1]
        $value = $Matches[2].Trim()
        if ($metadata.ContainsKey($key)) {
            throw "Task spec '$resolvedPath' contains duplicate '$key' metadata."
        }
        $metadata[$key] = $value
    }

    $requiredMetadata = @("schema_version", "task_id", "title", "status")
    $requiredSections = @(
        "Objective",
        "Motivation",
        "Acceptance criteria",
        "Non-goals",
        "Constraints and relevant decisions",
        "Affected product behaviour",
        "Validation requirements",
        "Approval questions",
        "Approved implementation plan",
        "Final handoff notes"
    )

    foreach ($field in $requiredMetadata) {
        if (-not $metadata.ContainsKey($field)) {
            throw "Task spec '$resolvedPath' is missing a value for '$field'."
        }
    }

    if ($metadata["schema_version"] -ne "1") {
        throw "Task spec '$resolvedPath' uses an unsupported schema version."
    }

    $readyStatuses = @(
        "approved", "implementing", "validating", "review", "ready", "completed"
    )
    if ($metadata["status"] -notin $readyStatuses) {
        throw "Task spec '$resolvedPath' is not approved for implementation."
    }

    foreach ($section in $requiredSections) {
        $escapedSection = [regex]::Escape($section)
        $match = [regex]::Match(
            $content,
            "(?ms)^## $escapedSection\s*\r?\n(.+?)(?=^## |\z)"
        )
        if (-not $match.Success -or [string]::IsNullOrWhiteSpace($match.Groups[1].Value)) {
            throw "Task spec '$resolvedPath' has an empty or missing '$section' section."
        }
    }

    Write-Host "Task spec accepted: $resolvedPath" -ForegroundColor Green
}

function Initialize-TestDatabase {
    Require-Command "docker" "Install Docker Desktop and ensure its CLI is on PATH."

    Invoke-CheckedCommand `
        -Label "Start PostgreSQL" `
        -Command "docker" `
        -Arguments @("compose", "up", "-d", "postgres") `
        -WorkingDirectory $repoRoot

    Write-Host "`n==> Wait for PostgreSQL" -ForegroundColor Cyan
    $ready = $false
    foreach ($attempt in 1..30) {
        & docker compose --project-directory $repoRoot exec -T postgres `
            pg_isready -U orbit -d orbit *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) {
        throw "PostgreSQL did not become ready within 30 seconds. Check Docker Desktop and the 'postgres' service logs."
    }

    $databaseExists = & docker compose --project-directory $repoRoot exec -T `
        postgres psql -U orbit -d postgres -tAc `
        "SELECT 1 FROM pg_database WHERE datname = 'orbit_test'"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect PostgreSQL databases in the local container."
    }

    if (($databaseExists | Out-String).Trim() -ne "1") {
        Invoke-CheckedCommand `
            -Label "Create isolated test database" `
            -Command "docker" `
            -Arguments @(
                "compose", "exec", "-T", "postgres",
                "createdb", "-U", "orbit", "orbit_test"
            ) `
            -WorkingDirectory $repoRoot
    }
}

function Invoke-BackendValidation {
    Require-Command "conda" "Install Miniconda/Conda and create the 'orbit-ai' environment."
    Initialize-TestDatabase
    $env:ORBIT_DATABASE_URL = $testDatabaseUrl

    Invoke-CheckedCommand `
        -Label "Apply migrations to orbit_test" `
        -Command "conda" `
        -Arguments @(
            "run", "--no-capture-output", "-n", "orbit-ai",
            "python", "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"
        ) `
        -WorkingDirectory $backendRoot

    Invoke-CheckedCommand `
        -Label "Run deterministic backend tests" `
        -Command "conda" `
        -Arguments @(
            "run", "--no-capture-output", "-n", "orbit-ai",
            "python", "-m", "pytest"
        ) `
        -WorkingDirectory $backendRoot
}

function Invoke-DesktopValidation {
    Require-Command "npm" "Install Node.js/npm and ensure npm is on PATH."
    $temporaryRoot = [System.IO.Path]::GetFullPath(
        [System.IO.Path]::GetTempPath()
    ).TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
        [System.IO.Path]::DirectorySeparatorChar
    $validationRoot = Join-Path $temporaryRoot (
        "orbit-desktop-validation-" + [guid]::NewGuid().ToString("N")
    )

    New-Item -ItemType Directory -Path $validationRoot | Out-Null
    try {
        $filesToCopy = @(
            "package.json",
            "package-lock.json",
            "eslint.config.js",
            "vite.config.ts",
            "tsconfig.json",
            "tsconfig.app.json",
            "tsconfig.node.json",
            "index.html"
        )
        foreach ($file in $filesToCopy) {
            Copy-Item -LiteralPath (Join-Path $desktopRoot $file) `
                -Destination $validationRoot
        }
        Copy-Item -LiteralPath (Join-Path $desktopRoot "src") `
            -Destination $validationRoot -Recurse
        Copy-Item -LiteralPath (Join-Path $desktopRoot "public") `
            -Destination $validationRoot -Recurse

        Invoke-CheckedCommand `
            -Label "Install locked desktop dependencies" `
            -Command "npm" `
            -Arguments @("ci") `
            -WorkingDirectory $validationRoot

        Invoke-CheckedCommand `
            -Label "Lint desktop" `
            -Command "npm" `
            -Arguments @("run", "lint") `
            -WorkingDirectory $validationRoot
        Invoke-CheckedCommand `
            -Label "Build desktop" `
            -Command "npm" `
            -Arguments @("run", "build") `
            -WorkingDirectory $validationRoot
    }
    finally {
        $resolvedValidationRoot = [System.IO.Path]::GetFullPath($validationRoot)
        $safeLeaf = Split-Path -Leaf $resolvedValidationRoot
        if (
            $resolvedValidationRoot.StartsWith(
                $temporaryRoot,
                [System.StringComparison]::OrdinalIgnoreCase
            ) -and
            $safeLeaf.StartsWith("orbit-desktop-validation-")
        ) {
            try {
                Remove-Item -LiteralPath $resolvedValidationRoot `
                    -Recurse -Force -ErrorAction Stop
            }
            catch {
                Write-Warning "Could not remove desktop validation workspace '$resolvedValidationRoot': $($_.Exception.Message)"
                throw
            }
        }
        else {
            throw "Refusing to remove unexpected validation path '$resolvedValidationRoot'."
        }
    }
}

function Invoke-TauriValidation {
    if ($env:OS -eq "Windows_NT" -and $env:LOCALAPPDATA) {
        # Keep the validation cache on the local Windows filesystem. Cargo can
        # fail to preserve crate mtimes when its shared cache is on some
        # secondary or mounted filesystems.
        $env:CARGO_HOME = Join-Path $env:LOCALAPPDATA "orbit-cargo"
        New-Item -ItemType Directory -Path $env:CARGO_HOME -Force | Out-Null
    }

    $cargoCommand = $null
    if ($env:RUSTUP_HOME) {
        $toolchainBin = Join-Path $env:RUSTUP_HOME `
            "toolchains\stable-x86_64-pc-windows-msvc\bin"
        $directCargo = Join-Path $toolchainBin "cargo.exe"
        $directRustc = Join-Path $toolchainBin "rustc.exe"
        if ((Test-Path $directCargo) -and (Test-Path $directRustc)) {
            $cargoCommand = $directCargo
            $env:RUSTC = $directRustc
        }
    }
    if (-not $cargoCommand) {
        Require-Command "cargo" "Install the stable Rust MSVC toolchain."
        $cargoCommand = (Get-Command cargo).Source
    }

    if (
        $env:OS -eq "Windows_NT" -and
        -not (Get-Command link.exe -ErrorAction SilentlyContinue)
    ) {
        $vswhere = Join-Path ${env:ProgramFiles(x86)} `
            "Microsoft Visual Studio\Installer\vswhere.exe"
        if (-not (Test-Path $vswhere)) {
            throw "MSVC linker environment is unavailable. Install Visual Studio Build Tools with the C++ workload."
        }

        $visualStudioRoot = & $vswhere -latest -products * `
            -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 `
            -property installationPath
        $vsDevCmd = Join-Path $visualStudioRoot "Common7\Tools\VsDevCmd.bat"
        if (-not $visualStudioRoot -or -not (Test-Path $vsDevCmd)) {
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

    Invoke-CheckedCommand `
        -Label "Check Tauri shell" `
        -Command $cargoCommand `
        -Arguments @("check", "--locked") `
        -WorkingDirectory (Join-Path $desktopRoot "src-tauri")
}

try {
    Require-Command "git" "Install Git and ensure it is on PATH."
    $initialTrackedState = Get-RepositorySnapshot
    Assert-TaskSpec -Path $TaskFile

    if ($Scope -in @("Backend", "All")) {
        Invoke-BackendValidation
    }
    if ($Scope -in @("Desktop", "All")) {
        Invoke-DesktopValidation
    }
    if ($Scope -in @("Tauri", "All")) {
        Invoke-TauriValidation
    }

    $finalTrackedState = Get-RepositorySnapshot
    $worktreeDifference = Compare-Object $initialTrackedState $finalTrackedState
    if ($worktreeDifference) {
        throw "Validation changed tracked files. Inspect 'git status' and restore generated changes before handoff."
    }

    Write-Host "`nValidation passed for scope '$Scope'." -ForegroundColor Green
}
catch {
    Write-Error $_
    exit 1
}
finally {
    $env:ORBIT_DATABASE_URL = $originalDatabaseUrl
}
