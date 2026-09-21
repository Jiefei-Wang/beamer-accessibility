$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$userRoot = (kpsewhich -var-value TEXMFHOME).Trim()
if (-not $userRoot) { throw "Could not determine TEXMFHOME." }

$destination = Join-Path $userRoot "tex/latex/beamer-accessibility"
New-Item -ItemType Directory -Force $destination | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot "beamer-accessibility.sty") -Destination $destination -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "beamer-accessibility.cls") -Destination $destination -Force

try {
    texhash $userRoot | Out-Null
} catch {}

Write-Output "Installed beamer-accessibility in $destination"
Push-Location ([IO.Path]::GetTempPath())
try {
    $installedStyle = kpsewhich beamer-accessibility.sty
    $installedClass = kpsewhich beamer-accessibility.cls
}
finally {
    Pop-Location
}
if (-not $installedStyle -or -not $installedClass) {
    throw "TeX Live could not find the installed files after installation."
}
Write-Output $installedStyle
Write-Output $installedClass
