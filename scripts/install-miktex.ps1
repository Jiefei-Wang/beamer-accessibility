$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$userRoot = (initexmf --report | Select-String '^Root0:' | ForEach-Object { $_.Line.Substring(6).Trim() })
if (-not $userRoot) { throw "Could not determine the MiKTeX user root." }

$destination = Join-Path $userRoot "tex/latex/beamer-accessibility"
New-Item -ItemType Directory -Force $destination | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot "beamer-accessibility.sty") -Destination $destination -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "beamer-accessibility.cls") -Destination $destination -Force

initexmf --update-fndb | Out-Null

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
    throw "MiKTeX could not find the installed files after refreshing its database."
}
Write-Output $installedStyle
Write-Output $installedClass

