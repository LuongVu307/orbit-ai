[CmdletBinding()]
param(
    [string]$Model = "gemma3"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $repoRoot "apps\backend"
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$outputPath = Join-Path $repoRoot "artifacts\evaluations\ollama-$timestamp.json"

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Error "Required command 'conda' was not found. Install Miniconda/Conda and create the 'orbit-ai' environment."
    exit 1
}

Push-Location $backendRoot
try {
    & conda run --no-capture-output -n orbit-ai python -m evals.live_ollama `
        --model $Model --output $outputPath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Advisory Ollama evaluation did not pass. Inspect '$outputPath'; if no model output was captured, confirm Ollama is running."
        exit $LASTEXITCODE
    }
}
finally {
    Pop-Location
}

Write-Host "Ollama evaluation passed. Report: $outputPath" -ForegroundColor Green
