# Guide de demarrage du projet Fraud Detection (Windows PowerShell).
# Equivalent de setup.sh : memes etapes, syntaxe PowerShell.

$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "=== Fraud Detection - Setup ===" -ForegroundColor Cyan
Write-Host ""

# 1. Le dataset doit etre present avant toute chose : sans lui, l'entrainement
#    (etape 3) ne peut pas tourner.
if (-not (Test-Path "data\creditcard.csv")) {
    Write-Host "X data\creditcard.csv introuvable." -ForegroundColor Red
    Write-Host "  Telecharge le dataset Kaggle 'Credit Card Fraud Detection' et place-le dans data\." -ForegroundColor Yellow
    exit 1
}
Write-Host "OK data\creditcard.csv trouve" -ForegroundColor Green

# 2. "docker info" echoue si le daemon Docker ne tourne pas (Docker Desktop
#    pas demarre), independamment du fait que la commande "docker" existe.
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Docker ne repond pas. Demarre Docker Desktop puis relance ce script." -ForegroundColor Red
    exit 1
}
Write-Host "OK Docker est demarre" -ForegroundColor Green

# 3. Le modele n'est jamais commite (trop lourd pour Git, cf. .gitignore) :
#    on l'entraine automatiquement s'il manque, pour que ce script marche
#    meme sur une machine qui clone le repo pour la premiere fois.
$modelExists = (Test-Path "models\fraud_model.pkl") -and (Test-Path "models\scaler.pkl")
if (-not $modelExists) {
    Write-Host "! Modele introuvable, entrainement en cours (python -m src.train)..." -ForegroundColor Yellow
    # "-m" est necessaire (pas "python src/train.py") : train.py utilise des
    # imports de paquet ("from src.config import ..."), qui ne fonctionnent
    # que si Python est lance depuis la racine du projet avec -m.
    python -m src.train
    if ($LASTEXITCODE -ne 0) {
        Write-Host "X Echec de l'entrainement." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "OK Modele deja entraine (models\fraud_model.pkl)" -ForegroundColor Green
}

# 4. Build + lancement des 3 services en arriere-plan.
Write-Host ""
Write-Host "Lancement de docker compose up --build..." -ForegroundColor Cyan
docker compose up --build -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Echec du docker compose up." -ForegroundColor Red
    exit 1
}

# 5. db et api ont un healthcheck explicite (docker-compose.yml) ; dashboard
#    n'en a pas (nginx demarre quasi instantanement), on verifie juste qu'il
#    tourne.
function Wait-Healthy {
    param([string]$Name, [int]$MaxTries = 30)

    Write-Host -NoNewline "   $Name : "
    for ($i = 0; $i -lt $MaxTries; $i++) {
        $status = docker inspect --format='{{.State.Health.Status}}' $Name 2>$null
        if ($status -eq "healthy") {
            Write-Host "healthy" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 2
    }
    Write-Host "timeout (verifie avec 'docker compose logs $Name')" -ForegroundColor Red
    return $false
}

Write-Host "Attente que les services soient prets..." -ForegroundColor Cyan
Wait-Healthy -Name "fraud_db" | Out-Null
Wait-Healthy -Name "fraud_api" | Out-Null

Write-Host -NoNewline "   fraud_dashboard : "
for ($i = 0; $i -lt 15; $i++) {
    $status = docker inspect --format='{{.State.Status}}' fraud_dashboard 2>$null
    if ($status -eq "running") {
        Write-Host "running" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "Systeme disponible sur http://localhost:3000" -ForegroundColor Green
