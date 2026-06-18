param()

$Repo = "xzule/quasai"
$Ghcr = "ghcr.io/$Repo"

Write-Host "=== Quasai Installer ==="

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Desktop не найден."
    Write-Host "Установите Docker Desktop вручную: https://docs.docker.com/desktop/setup/install/windows-install/"
    Write-Host "После установки запустите install.ps1 снова."
    exit 1
}

Write-Host "Загружаю образ $Ghcr :latest..."
docker pull "$Ghcr`:latest"

Write-Host ""
Write-Host "Установка завершена."
Write-Host "Запуск: docker compose up"
Write-Host "Генерация: quasai input.md -o output.json"