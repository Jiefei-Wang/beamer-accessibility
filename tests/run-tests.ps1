$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$buildRoot = Join-Path $repoRoot "build/tests"
$fixtures = Join-Path $repoRoot "tests/fixtures"
New-Item -ItemType Directory -Force $buildRoot | Out-Null
$outputArgument = "-output-directory=$buildRoot"

$fixtureFiles = Get-ChildItem -Path $fixtures -Filter "*.tex" | Sort-Object Name

Push-Location $repoRoot
try {
    foreach ($file in $fixtureFiles) {
        $document = $file.BaseName
        $source = $file.FullName
        Write-Host "Compiling $document..."
        $expectedFailure = $document -like '*-failure'
        & pdflatex -interaction=nonstopmode -halt-on-error $outputArgument $source | Out-Null
        if ($expectedFailure) {
            if ($LASTEXITCODE -eq 0) { throw "Expected LaTeX failure did not occur: $document" }
            continue
        }
        if ($LASTEXITCODE -ne 0) { throw "First LaTeX pass failed: $document" }
        & pdflatex -interaction=nonstopmode -halt-on-error $outputArgument $source | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Second LaTeX pass failed: $document" }
    }
    & python (Join-Path $repoRoot "tests/verify.py") $buildRoot
    if ($LASTEXITCODE -ne 0) { throw "PDF verification failed" }
    & python (Join-Path $repoRoot "tests/verify_at.py") $buildRoot
    if ($LASTEXITCODE -ne 0) { throw "AT accessibility validation failed" }
}
finally {
    Pop-Location
}
