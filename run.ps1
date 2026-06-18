param(
    [Parameter(Mandatory, Position=0)]
    [string]$InputFile,
    [Parameter(Mandatory, Position=1)]
    [string]$OutputFile
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path -LiteralPath $InputFile)) {
    Write-Host "Error: input file not found: $InputFile"
    Write-Host ""
    Write-Host "Usage: .\run.ps1 -InputFile <path> -OutputFile <path>"
    Write-Host ""
    Write-Host "  Examples:"
    Write-Host "    .\run.ps1 -InputFile .\input\test.md -OutputFile .\output\test.json"
    Write-Host "    .\run.ps1 -InputFile C:\full\path\test.md -OutputFile C:\full\path\test.json"
    exit 1
}

New-Item -ItemType Directory -Path "$ProjectRoot\input" -Force | Out-Null
New-Item -ItemType Directory -Path "$ProjectRoot\output" -Force | Out-Null

$InputLeaf = Split-Path -Leaf $InputFile
$InputDest = "$ProjectRoot\input\$InputLeaf"
if ((Resolve-Path $InputFile -ErrorAction SilentlyContinue).Path -ne (Resolve-Path $InputDest -ErrorAction SilentlyContinue).Path) {
    Copy-Item -Path $InputFile -Destination $InputDest -Force
}

docker compose -p quasai up -d ollama

docker compose -p quasai run --rm --entrypoint quasai app `
    /input/$InputLeaf `
    -o /output/$(Split-Path -Leaf $OutputFile)

$OutputLeaf = Split-Path -Leaf $OutputFile
$OutputTemp = "$ProjectRoot\output\$OutputLeaf"
if ((Resolve-Path $OutputFile -ErrorAction SilentlyContinue).Path -ne (Resolve-Path $OutputTemp -ErrorAction SilentlyContinue).Path) {
    Copy-Item -Path $OutputTemp -Destination $OutputFile -Force
}

docker compose -p quasai down

Write-Host "Done: $OutputFile"
