$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repoRoot "apps\backend"
$tauriLauncher = Join-Path $PSScriptRoot "run-tauri.ps1"
$developmentDatabaseUrl = "postgresql+psycopg://orbit:orbit@localhost:5432/orbit"
$originalDatabaseUrl = $env:ORBIT_DATABASE_URL
$runtimeRoot = Join-Path ([System.IO.Path]::GetTempPath()) (
    "orbit-runtime-" + [guid]::NewGuid().ToString("N")
)
$ownedBackend = $null
$ownedOllama = $null
$failed = $false

function Require-Command {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$InstallHint
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Required command '$Name' was not found. $InstallHint"
    }
    return $command
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][string]$Command,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$WorkingDirectory
    )

    Write-Host ([Environment]::NewLine + "==> $Label") -ForegroundColor Cyan
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

function Wait-Until {
    param(
        [Parameter(Mandatory)][scriptblock]$Condition,
        [Parameter(Mandatory)][string]$FailureMessage,
        [int]$Attempts = 30
    )

    foreach ($attempt in 1..$Attempts) {
        if (& $Condition) {
            return
        }
        Start-Sleep -Seconds 1
    }
    throw $FailureMessage
}

function Get-OllamaTags {
    try {
        return Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 2
    }
    catch {
        return $null
    }
}

function Test-OrbitApi {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -TimeoutSec 2
        return $response.message -eq "Orbit AI is running"
    }
    catch {
        return $false
    }
}

function Test-LocalPort {
    param([Parameter(Mandatory)][int]$Port)

    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync("127.0.0.1", $Port)
        return $connection.Wait(500) -and $client.Connected
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Test-OrbitDesktopProcess {
    $expectedPath = Join-Path $repoRoot (
        "apps\desktop\src-tauri\target\debug\app.exe"
    )
    $expectedPath = [System.IO.Path]::GetFullPath($expectedPath)
    $candidates = Get-Process -Name "app" -ErrorAction SilentlyContinue
    foreach ($candidate in $candidates) {
        try {
            if (
                [System.IO.Path]::GetFullPath($candidate.Path) -eq
                $expectedPath
            ) {
                return $true
            }
        }
        catch {
            continue
        }
    }
    return $false
}

function Show-LogTail {
    param(
        [Parameter(Mandatory)][string]$Label,
        [Parameter(Mandatory)][string]$Path
    )

    if (Test-Path -LiteralPath $Path) {
        Write-Host ([Environment]::NewLine + $Label) -ForegroundColor Yellow
        Get-Content -LiteralPath $Path -Tail 30
    }
}

New-Item -ItemType Directory -Path $runtimeRoot | Out-Null
$backendOut = Join-Path $runtimeRoot "backend.stdout.log"
$backendErr = Join-Path $runtimeRoot "backend.stderr.log"
$ollamaOut = Join-Path $runtimeRoot "ollama.stdout.log"
$ollamaErr = Join-Path $runtimeRoot "ollama.stderr.log"

try {
    $docker = Require-Command "docker" "Install Docker Desktop and ensure its CLI is on PATH."
    $conda = Require-Command "conda" "Install Miniconda/Conda and create the 'orbit-ai' environment."
    $ollama = Require-Command "ollama" "Install Ollama and ensure its CLI is on PATH."
    Require-Command "node" "Install Node.js and ensure it is on PATH." | Out-Null
    Require-Command "npx.cmd" "Install npm and ensure it is on PATH." | Out-Null

    $env:ORBIT_DATABASE_URL = $developmentDatabaseUrl

    $postgresArguments = @("compose", "up", "-d", "postgres")
    Invoke-CheckedCommand -Label "Start PostgreSQL" -Command $docker.Source -Arguments $postgresArguments -WorkingDirectory $repoRoot

    Write-Host ([Environment]::NewLine + "==> Wait for PostgreSQL") -ForegroundColor Cyan
    Wait-Until -FailureMessage "PostgreSQL did not become ready. Check Docker Desktop and run 'docker compose logs postgres'." -Condition {
        & $docker.Source compose --project-directory $repoRoot exec -T postgres pg_isready -U orbit -d orbit *> $null
        return $LASTEXITCODE -eq 0
    }

    Write-Host ([Environment]::NewLine + "==> Locate Orbit Python environment") -ForegroundColor Cyan
    $environmentJson = (& $conda.Source env list --json) -join [Environment]::NewLine
    if ($LASTEXITCODE -ne 0) {
        throw "The 'orbit-ai' Conda environment is unavailable."
    }
    $environments = ($environmentJson | ConvertFrom-Json).envs
    $environmentPath = $environments | Where-Object {
        (Split-Path -Leaf $_) -eq "orbit-ai"
    } | Select-Object -First 1
    if (-not $environmentPath) {
        throw "The 'orbit-ai' Conda environment is unavailable."
    }
    $python = Join-Path $environmentPath "python.exe"
    if (-not (Test-Path -LiteralPath $python)) {
        throw "Could not locate Python in the 'orbit-ai' Conda environment."
    }

    $migrationArguments = @("-m", "alembic", "-c", "alembic.ini", "upgrade", "head")
    Invoke-CheckedCommand -Label "Apply development database migrations" -Command $python -Arguments $migrationArguments -WorkingDirectory $backendRoot

    $tags = Get-OllamaTags
    if (-not $tags) {
        Write-Host ([Environment]::NewLine + "==> Start Ollama") -ForegroundColor Cyan
        $ollamaParameters = @{
            FilePath = $ollama.Source
            ArgumentList = @("serve")
            WorkingDirectory = $repoRoot
            WindowStyle = "Hidden"
            RedirectStandardOutput = $ollamaOut
            RedirectStandardError = $ollamaErr
            PassThru = $true
        }
        $ownedOllama = Start-Process @ollamaParameters
        Wait-Until -Condition { return $null -ne (Get-OllamaTags) } -FailureMessage "Ollama did not become ready."
        $tags = Get-OllamaTags
    }

    $modelNames = @($tags.models | ForEach-Object { $_.name })
    $gemmaAvailable = @(
        $modelNames | Where-Object { $_ -eq "gemma3" -or $_ -like "gemma3:*" }
    ).Count -gt 0
    if (-not $gemmaAvailable) {
        throw "The gemma3 model is not installed. Run 'ollama pull gemma3' and retry."
    }
    Write-Host "Ollama ready with gemma3." -ForegroundColor Green

    if (-not (Test-OrbitApi)) {
        if (Test-LocalPort -Port 8000) {
            throw "Port 8000 is occupied by a service that is not Orbit. Stop that service or configure Orbit to use another port."
        }

        Write-Host ([Environment]::NewLine + "==> Start FastAPI") -ForegroundColor Cyan
        $backendParameters = @{
            FilePath = $python
            ArgumentList = @("-m", "uvicorn", "app.main:app")
            WorkingDirectory = $backendRoot
            WindowStyle = "Hidden"
            RedirectStandardOutput = $backendOut
            RedirectStandardError = $backendErr
            PassThru = $true
        }
        $ownedBackend = Start-Process @backendParameters
        Wait-Until -Condition { return Test-OrbitApi } -FailureMessage "FastAPI did not become ready on http://127.0.0.1:8000/."
    }
    Write-Host "Orbit API ready." -ForegroundColor Green

    if (Test-OrbitDesktopProcess) {
        throw "Orbit desktop is already running. Close it before starting another session."
    }
    if (Test-LocalPort -Port 5173) {
        throw (
            "Port 5173 is already in use. Close the existing Vite or Orbit " +
            "desktop process before starting a new desktop session."
        )
    }

    Write-Host ([Environment]::NewLine + "==> Start Orbit desktop") -ForegroundColor Cyan
    & $tauriLauncher
    if ($LASTEXITCODE -ne 0) {
        throw "Orbit desktop exited with code $LASTEXITCODE."
    }
}
catch {
    $failed = $true
    Write-Host ([Environment]::NewLine + "Orbit startup failed: $($_.Exception.Message)") -ForegroundColor Red
    Show-LogTail -Label "FastAPI error log:" -Path $backendErr
    Show-LogTail -Label "Ollama error log:" -Path $ollamaErr
}
finally {
    if ($ownedBackend -and -not $ownedBackend.HasExited) {
        Stop-Process -Id $ownedBackend.Id -Force
        $ownedBackend.WaitForExit()
    }
    if ($ownedOllama -and -not $ownedOllama.HasExited) {
        Stop-Process -Id $ownedOllama.Id -Force
        $ownedOllama.WaitForExit()
    }
    $env:ORBIT_DATABASE_URL = $originalDatabaseUrl

    $temporaryRoot = [System.IO.Path]::GetFullPath(
        [System.IO.Path]::GetTempPath()
    ).TrimEnd([System.IO.Path]::DirectorySeparatorChar) +
        [System.IO.Path]::DirectorySeparatorChar
    $resolvedRuntimeRoot = [System.IO.Path]::GetFullPath($runtimeRoot)
    $isSafeRuntimePath = $resolvedRuntimeRoot.StartsWith(
        $temporaryRoot,
        [System.StringComparison]::OrdinalIgnoreCase
    ) -and (Split-Path -Leaf $resolvedRuntimeRoot).StartsWith("orbit-runtime-")
    if ($isSafeRuntimePath) {
        Remove-Item -LiteralPath $resolvedRuntimeRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if ($failed) {
    exit 1
}
