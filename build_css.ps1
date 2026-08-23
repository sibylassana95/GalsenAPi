# Build du CSS Tailwind pour GalsenAPI 2.0
# Usage : .\build_css.ps1
# Prerequis : tools/tailwindcss.exe (CLI standalone v3, voir .gitignore)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

& (Join-Path $root 'tools\tailwindcss.exe') `
    -i (Join-Path $root 'static\css\src\app.css') `
    -o (Join-Path $root 'static\css\galsenapi.css') `
    --minify

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$out = Get-Item (Join-Path $root 'static\css\galsenapi.css')
Write-Host ("OK : {0} ({1:N1} Ko)" -f $out.FullName, ($out.Length / 1KB))
