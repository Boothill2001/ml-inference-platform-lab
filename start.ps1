$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Assert-Exit([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "$Step failed (exit code $LASTEXITCODE)." }
}

function Test-Dependencies([string]$Python, [string]$Check) {
    $ErrorActionPreference = 'SilentlyContinue'
    & $Python -c $Check *> $null
    return $LASTEXITCODE -eq 0
}

function Prepare-Python([string[]]$InstallArgs, [string]$Check) {
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        Write-Host 'Creating a Python 3.11 environment...'
        if (Get-Command py -ErrorAction SilentlyContinue) { & py -3.11 -m venv .venv }
        else { & python -m venv .venv }
        Assert-Exit 'Environment creation'
    }
    $demoPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    $manifest = if ($InstallArgs[-1] -eq '.') { 'pyproject.toml' } else { $InstallArgs[-1] }
    $stamp = & $demoPython -c 'from hashlib import file_digest; import sys; print(file_digest(open(sys.argv[1], ''rb''), ''sha256'').hexdigest())' $manifest
    Assert-Exit 'Dependency manifest checksum'
    $stampFile = Join-Path $PSScriptRoot '.venv\demo-requirements.sha256'
    # Reuse a compatible environment on the first run and refresh if requirements change.
    if (-not (Test-Dependencies $demoPython $Check) -or ((Test-Path $stampFile) -and (Get-Content $stampFile -Raw).Trim() -ne $stamp)) {
        Write-Host 'Installing demo dependencies...'
        & $demoPython -m pip --disable-pip-version-check install @InstallArgs | Out-Host
        Assert-Exit 'Dependency installation'
        & $demoPython -c $Check | Out-Host
        Assert-Exit 'Dependency check'
    }
    Set-Content -LiteralPath $stampFile -Value $stamp
    return $demoPython
}

function Start-Demo([int]$Port, [string]$Route, [string]$Probe, [string]$ReadyMatch,
                    [string]$Python, [string[]]$ServerArgs) {
    if ($env:DEMO_PORT) { $Port = [int]$env:DEMO_PORT }
    $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $Port)
    try { $listener.Start() }
    catch { throw "Port $Port is already in use. Close that demo window or set DEMO_PORT." }
    finally { $listener.Stop() }

    $rootUrl = "http://127.0.0.1:$Port"
    $serverArgsWithPort = $ServerArgs | ForEach-Object { $_.Replace('{port}', "$Port") }
    Write-Host "Starting $rootUrl$Route. Keep this window open. Press Ctrl+C to stop."
    $openWhenReady = if ($env:DEMO_NO_BROWSER) { 'no' } else { 'yes' }
    $watcher = Start-Job -ArgumentList ($rootUrl + $Probe), ($rootUrl + $Route), $ReadyMatch, $openWhenReady -ScriptBlock {
        param($ProbeUrl, $PageUrl, $Match, $Open)
        for ($attempt = 0; $attempt -lt 90; $attempt++) {
            try {
                $response = Invoke-WebRequest -Uri $ProbeUrl -UseBasicParsing -TimeoutSec 2
                if ($response.StatusCode -eq 200 -and ($response.Content -match $Match)) {
                    if ($Open -eq 'yes') { Start-Process $PageUrl }
                    return
                }
            } catch {}
            Start-Sleep -Seconds 1
        }
    }
    try { & $Python @serverArgsWithPort; Assert-Exit 'Demo server' }
    finally { Remove-Job -Job $watcher -Force -ErrorAction SilentlyContinue }
}

$demoPython = Prepare-Python @('-r', 'requirements.txt') 'import app.main, sklearn'
if (-not (Test-Path 'models\artifacts\churn_model_v1.joblib')) {
    Write-Host 'Training the demo models...'
    & $demoPython models/train_model.py
    Assert-Exit 'Model training'
}
Start-Demo 8000 '/' '/openapi.json' 'ML Inference Platform' $demoPython @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port','{port}')
