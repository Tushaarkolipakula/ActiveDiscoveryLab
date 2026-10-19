$ErrorActionPreference = 'Stop'
$dataDirectory = Join-Path $PSScriptRoot 'data\silverbox'
New-Item -ItemType Directory -Force -Path $dataDirectory | Out-Null
$archivePath = Join-Path $dataDirectory 'SilverboxFiles.zip'
if (-not (Test-Path -LiteralPath $archivePath)) {
    Invoke-WebRequest -Uri 'https://drive.google.com/uc?export=download&id=17iS-6oBUUgrmiAcrZoG9S5sOaljZnDSy' -OutFile $archivePath
}
$rawDirectory = Join-Path $dataDirectory 'raw'
if (-not (Test-Path -LiteralPath $rawDirectory)) {
    Expand-Archive -LiteralPath $archivePath -DestinationPath $rawDirectory
}
Write-Output 'Silverbox data downloaded. See docs/REAL_DATA.md for attribution and evaluation scope.'
