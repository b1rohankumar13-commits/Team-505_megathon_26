$ErrorActionPreference = 'Stop'
$settingsPath = Join-Path $PSScriptRoot '.runtime/local.json'
if (-not (Test-Path -LiteralPath $settingsPath)) { throw 'Configure .runtime/local.json or run python run_integrated.py in your environment. See docs/LIVE_INTEGRATION.md.' }
$settings = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
& $settings.python (Join-Path $PSScriptRoot 'run_integrated.py')
exit $LASTEXITCODE
