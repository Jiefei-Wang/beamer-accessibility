$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$buildRoot = Join-Path $repoRoot "build/tests"
$fixtures = Join-Path $repoRoot "tests/fixtures"
New-Item -ItemType Directory -Force $buildRoot | Out-Null
$outputArgument = "-output-directory=$buildRoot"

$documents = @(
    "frame-paragraph-baseline",
    "frame-paragraph-tagged",
    "unsupported-list-baseline",
    "unsupported-list-tagged",
    "package-only"
)

Push-Location $repoRoot
try {
    foreach ($document in $documents) {
        $source = Join-Path $fixtures "$document.tex"
        & pdflatex -interaction=nonstopmode -halt-on-error $outputArgument $source | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "First LaTeX pass failed: $document" }
        & pdflatex -interaction=nonstopmode -halt-on-error $outputArgument $source | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Second LaTeX pass failed: $document" }
    }
    & python (Join-Path $repoRoot "tests/verify.py") $buildRoot
    if ($LASTEXITCODE -ne 0) { throw "PDF verification failed" }
}
finally {
    Pop-Location
}
