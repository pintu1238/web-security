param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8501,
    [string]$BindAddress = '0.0.0.0'
)

$projectPythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPythonPath)) {
    throw 'The project environment is missing. Create .venv and install Backend/requirements-web.txt first.'
}

$previousProjectPort = $env:PORT
$previousProjectHost = $env:NITISHIELD_HOST
try {
    $env:PORT = [string]$Port
    $env:NITISHIELD_HOST = $BindAddress
    Write-Host "Starting NitiShield at http://localhost:$Port/#dashboard (also available on this computer's network address)."
    & $projectPythonPath (Join-Path $PSScriptRoot 'Backend\app.py')
} finally {
    $env:PORT = $previousProjectPort
    $env:NITISHIELD_HOST = $previousProjectHost
}
