$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Python environment missing. Follow the setup instructions in README.md.'
}
$runName = 'results/pilot-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
& $projectPython -m active_discovery.benchmark --budget 4 --seeds 0 1 --systems linear nonlinear_spring quadratic_drag combined --out $runName
if ($LASTEXITCODE -ne 0) { throw 'Pilot failed. Inspect the terminal output and saved run files.' }
Write-Output "Open $runName/report.html to inspect the results."
