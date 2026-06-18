param(
    [Parameter(Position=0)]
    [string]$FileName
)

if (-not $FileName) {
    $FileName = Read-Host "Type input file name"
}

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$InputPath = "$ProjectRoot\input\$FileName"

if (-not (Test-Path -LiteralPath $InputPath)) {
    Write-Host "Error: file not found in $ProjectRoot\input"
    Write-Host ""
    Write-Host "Place your .md file in the input/ directory and run:"
    Write-Host "  .\run.ps1 requirements.md"
    exit 1
}

docker compose -p quasai up -d ollama

Start-Sleep -Seconds 5

docker compose -p quasai exec ollama ollama pull phi4-mini

docker compose -p quasai run --rm --entrypoint quasai app /input/$FileName

docker compose -p quasai down
