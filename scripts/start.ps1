param(
  [string]$DatabaseUrl = "postgresql+psycopg://postgres@localhost:5432/ai_novel_screenplay",
  [switch]$SkipDatabaseInit
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$BackendEnv = Join-Path $Backend ".env"
$BackendEnvExample = Join-Path $Backend ".env.example"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (!(Test-Path $BackendEnv)) {
  Copy-Item $BackendEnvExample $BackendEnv
  (Get-Content $BackendEnv) `
    -replace '^DATABASE_URL=.*$', "DATABASE_URL=$DatabaseUrl" `
    -replace '^SECRET_KEY=.*$', "SECRET_KEY=change-this-local-secret-before-sharing" |
    Set-Content -Encoding UTF8 $BackendEnv
  Write-Host "Created backend\.env. Edit it if your local database URL is different."
}

if (!(Test-Path $Python)) {
  $PythonLauncher = Get-Command py -ErrorAction SilentlyContinue
  if ($PythonLauncher) {
    py -3.12 -m venv (Join-Path $Backend ".venv")
  } else {
    python -m venv (Join-Path $Backend ".venv")
  }
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $Backend "requirements.txt")

Push-Location $Frontend
npm install
Pop-Location

if (!$SkipDatabaseInit) {
  $Psql = Get-Command psql -ErrorAction SilentlyContinue
  if ($Psql) {
    $ExistingDb = (& psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='ai_novel_screenplay';").Trim()
    if ($ExistingDb -ne "1") {
      Write-Host "Initializing PostgreSQL database ai_novel_screenplay..."
      & psql -U postgres -f (Join-Path $Root "sql\init.sql")
    }
  } else {
    Write-Host "psql was not found. Run manually: psql -U postgres -f sql\init.sql"
  }
}

$Npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (!$Npm) {
  $Npm = Get-Command npm -ErrorAction Stop
}

Write-Host "Starting backend: http://127.0.0.1:8000"
Start-Process -FilePath $Python -ArgumentList "run.py" -WorkingDirectory $Backend

Write-Host "Starting frontend: http://127.0.0.1:5173"
Start-Process -FilePath $Npm.Source -ArgumentList "run dev" -WorkingDirectory $Frontend
