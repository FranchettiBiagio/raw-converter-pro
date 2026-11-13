<#
    Scarica il client dlib di Azure Artifact Signing (ex Trusted Signing).

    Il pacchetto NuGet Microsoft.ArtifactSigning.Client contiene
    bin\x64\Azure.CodeSigning.Dlib.dll, il plugin che permette a signtool.exe
    di firmare usando il certificato gestito da Azure (la chiave privata non
    lascia mai il servizio).

    Uso:
      .\tools\get-artifact-signing-client.ps1                # ultima versione
      .\tools\get-artifact-signing-client.ps1 -Version 1.0.151

    Destinazione: tools\artifactsigning\<versione>\  (ignorata da git)
#>

[CmdletBinding()]
param(
    [string]$Version
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $root "tools\artifactsigning"

if (-not $Version) {
    $index = Invoke-RestMethod "https://api.nuget.org/v3-flatcontainer/microsoft.artifactsigning.client/index.json"
    $Version = ($index.versions | Sort-Object { [version]$_ } | Select-Object -Last 1)
    Write-Host "Ultima versione disponibile: $Version"
}

$versionDir = Join-Path $dest $Version
$dll = Join-Path $versionDir "bin\x64\Azure.CodeSigning.Dlib.dll"
if (Test-Path $dll) {
    Write-Host "Gia presente: $dll" -ForegroundColor Green
    return
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null
$url = "https://api.nuget.org/v3-flatcontainer/microsoft.artifactsigning.client/$Version/microsoft.artifactsigning.client.$Version.nupkg"
$pkg = Join-Path $env:TEMP "microsoft.artifactsigning.client.$Version.nupkg"

Write-Host "Download: $url"
$ProgressPreference = "SilentlyContinue"
Invoke-WebRequest -Uri $url -OutFile $pkg -UseBasicParsing

Write-Host "Estrazione in $versionDir"
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($pkg, $versionDir)
Remove-Item $pkg -Force

if (-not (Test-Path $dll)) { throw "Dlib non trovata dopo l'estrazione: $dll" }
Write-Host "`nPronto: $dll" -ForegroundColor Green
Write-Host "Ora puoi eseguire:" -ForegroundColor Cyan
Write-Host "  .\tools\sign_and_build.ps1 -Mode Azure -Account <account> -Profile <profilo>"
