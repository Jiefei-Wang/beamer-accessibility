$ErrorActionPreference = "Stop"
& python (Join-Path $PSScriptRoot "run_tests.py") @args
if ($LASTEXITCODE -ne 0) { throw "Accessibility regression tests failed" }
