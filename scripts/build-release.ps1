# build-release.ps1 - Automated release packaging for beamer-accessibility v1.0
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$releaseDir = Join-Path $repoRoot "build/release"
$pkgDir = Join-Path $releaseDir "beamer-accessibility"

Write-Host "Creating release package directory..."
if (Test-Path $releaseDir) {
    Remove-Item -Recurse -Force $releaseDir
}
New-Item -ItemType Directory -Force $pkgDir | Out-Null
New-Item -ItemType Directory -Force (Join-Path $pkgDir "doc") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $pkgDir "examples") | Out-Null

Write-Host "Copying package files..."
Copy-Item (Join-Path $repoRoot "beamer-accessibility.sty") $pkgDir
Copy-Item (Join-Path $repoRoot "beamer-accessibility.cls") $pkgDir
Copy-Item (Join-Path $repoRoot "README.md") $pkgDir
Copy-Item (Join-Path $repoRoot "CHANGELOG.md") $pkgDir
Copy-Item (Join-Path $repoRoot "LICENSE") $pkgDir

Write-Host "Copying documentation..."
Copy-Item (Join-Path $repoRoot "docs/*.md") (Join-Path $pkgDir "doc")
Copy-Item (Join-Path $repoRoot "examples/*.tex") (Join-Path $pkgDir "examples")

Write-Host "Creating release archive..."
$zipPath = Join-Path $releaseDir "beamer-accessibility-1.0.zip"
Compress-Archive -Path $pkgDir -DestinationPath $zipPath -Force

Write-Host "Release package successfully created at: $zipPath"
