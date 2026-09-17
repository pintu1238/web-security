param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8501,
    [string]$BindAddress = '0.0.0.0',
    [ValidateSet('part_a', 'full')]
    [string]$ProjectStage = 'part_a',
    [switch]$NoBrowser
)

$projectPythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPythonPath)) {
    throw 'The project environment is missing. Create .venv and install Backend/requirements-web.txt first.'
}

$previousProjectPort = $env:PORT
$previousProjectHost = $env:NITISHIELD_HOST
$previousProjectStage = $env:NITISHIELD_PROJECT_STAGE
$serverProcess = $null
try {
    $env:PORT = [string]$Port
    $env:NITISHIELD_HOST = $BindAddress
    $env:NITISHIELD_PROJECT_STAGE = $ProjectStage
    $dashboardUrl = "http://localhost:$Port/#dashboard"
    $healthUrl = "http://127.0.0.1:$Port/api/health"
    Write-Host "Starting NitiShield at $dashboardUrl in $ProjectStage mode (also available on this computer's network address)."
    $serverProcess = Start-Process -FilePath $projectPythonPath `
        -ArgumentList @('-u', (Join-Path $PSScriptRoot 'Backend\app.py')) `
        -WorkingDirectory $PSScriptRoot -NoNewWindow -PassThru

    $ready = $false
    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        if ($serverProcess.HasExited) {
            throw "NitiShield stopped before it became ready (exit code $($serverProcess.ExitCode))."
        }
        try {
            $health = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 1
            if ($health.StatusCode -eq 200) {
                $ready = $true
                break
            }
        } catch {
            # Flask needs a moment to bind the port.
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $ready) {
        throw "NitiShield did not become ready within 30 seconds."
    }
    if (-not $NoBrowser) {
        Write-Host "Opening $dashboardUrl in your default browser."
        Start-Process $dashboardUrl | Out-Null
    }
    Wait-Process -Id $serverProcess.Id
} finally {
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
    }
    $env:PORT = $previousProjectPort
    $env:NITISHIELD_HOST = $previousProjectHost
    $env:NITISHIELD_PROJECT_STAGE = $previousProjectStage
}
