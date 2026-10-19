$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Follow the setup instructions in README.md first.' }
Write-Output 'Open http://127.0.0.1:8765 in your browser. Press Ctrl+C here to stop the lab.'
& $projectPython -m active_discovery.lab --port 8765
