param(
    [Parameter(Mandatory, Position=0)]
    [string]$FileName
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$InputPath = "$ProjectRoot\input\$FileName"

if (-not (Test-Path -LiteralPath $InputPath)) {
    Write-Host "Error: файл не найден в $ProjectRoot\input"
    Write-Host ""
    Write-Host "Поместите .md файл в папку input/ и укажите только имя:"
    Write-Host "  .\run.ps1 requirements.md"
    exit 1
}

docker compose -p quasai up -d ollama

docker compose -p quasai run --rm --entrypoint quasai app /input/$FileName

docker compose -p quasai down

$Stem = $FileName -replace '\.md$', ''
Write-Host ""
Write-Host "Результаты сохранены в:"
Write-Host "  .\output\$Stem.json"
Write-Host "  .\output\$Stem.csv"
