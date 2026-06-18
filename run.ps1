param(
    [Parameter(Mandatory, Position=0)]
    [string]$InputFile,
    [Parameter(Mandatory, Position=1)]
    [string]$OutputFile
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path -LiteralPath $InputFile)) {
    Write-Host "Error: input file not found: $InputFile"
    exit 1
}

New-Item -ItemType Directory -Path "$ProjectRoot\input" -Force | Out-Null
New-Item -ItemType Directory -Path "$ProjectRoot\output" -Force | Out-Null

Copy-Item -Path $InputFile -Destination "$ProjectRoot\input\" -Force

docker compose -p quasai up -d ollama

docker compose -p quasai run --rm --entrypoint quasai app `
    /input/$(Split-Path -Leaf $InputFile) `
    -o /output/$(Split-Path -Leaf $OutputFile)

Copy-Item -Path "$ProjectRoot\output\$(Split-Path -Leaf $OutputFile)" `
          -Destination $OutputFile -Force

docker compose -p quasai down

Write-Host "Done: $OutputFile"
