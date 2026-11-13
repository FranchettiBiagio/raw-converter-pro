<#
    Firma Authenticode + build dell'installer per il Microsoft Store.

    Lo Store accetta installer EXE/MSI solo se il file e TUTTI i PE che
    contiene sono firmati con un certificato che catena al Microsoft Trusted
    Root Program. Questo script:
      1. firma dist\FranchettiRawConverterPro.exe (SHA-256 + timestamp);
      2. genera sign_tool.iss con il comando signtool per Inno Setup;
      3. compila setup.iss con /DSIGN, firmando installer e uninstaller;
      4. verifica le firme e stampa gli SHA-256.

    Esempi:
      .\tools\sign_and_build.ps1 -Mode Pfx -PfxPath C:\certs\frc.pfx -PfxPassword "***"
      .\tools\sign_and_build.ps1 -Mode Store -Thumbprint ABC123...
      .\tools\sign_and_build.ps1 -Mode Azure -Dlib "C:\...\Azure.CodeSigning.Dlib.dll" -Metadata "C:\...\metadata.json"

    Prerequisiti: signtool.exe (Windows SDK -> Signing Tools), Inno Setup 7,
    certificato valido (OV/IV su token oppure Azure Artifact Signing).
    Un certificato self-signed NON e accettato dallo Store.
#>

[CmdletBinding()]
param(
    [ValidateSet("Pfx", "Store", "Azure")]
    [string]$Mode = "Store",
    [string]$PfxPath,
    [string]$PfxPassword,
    [string]$Thumbprint,
    [string]$Dlib,
    [string]$Metadata,
    [string]$TimestampUrl = "http://timestamp.digicert.com",
    [string]$Iscc = "C:\Program Files\Inno Setup 7\ISCC.exe",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$appExe = Join-Path $root "dist\FranchettiRawConverterPro.exe"
$iss = Join-Path $root "setup.iss"
$signToolIss = Join-Path $root "sign_tool.iss"
$installer = Join-Path $root "Output\Franchetti_Raw_Converter_Setup_v2.58.1.exe"

function Find-SignTool {
    $cmd = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $kits = "C:\Program Files (x86)\Windows Kits\10\bin"
    if (Test-Path $kits) {
        $found = Get-ChildItem $kits -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\x64\\' } |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($found) { return $found.FullName }
    }
    throw "signtool.exe non trovato. Installa 'Windows SDK > Signing Tools' oppure aggiungilo al PATH."
}

$signtool = Find-SignTool
Write-Host "signtool: $signtool"

# --- Argomenti di firma comuni -------------------------------------------------
$signArgs = @("sign", "/fd", "SHA256", "/tr", $TimestampUrl, "/td", "SHA256")

switch ($Mode) {
    "Pfx" {
        if (-not (Test-Path $PfxPath)) { throw "PFX non trovato: $PfxPath" }
        if (-not $PfxPassword) { throw "Specifica -PfxPassword." }
        $signArgs += @("/f", $PfxPath, "/p", $PfxPassword)
    }
    "Store" {
        if (-not $Thumbprint) { throw "Specifica -Thumbprint del certificato in CurrentUser\My." }
        $cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Thumbprint -eq $Thumbprint }
        if (-not $cert) { throw "Certificato $Thumbprint non trovato in Cert:\CurrentUser\My." }
        $signArgs += @("/sha1", $Thumbprint)
    }
    "Azure" {
        if (-not (Test-Path $Dlib)) { throw "Dlib non trovata: $Dlib" }
        if (-not (Test-Path $Metadata)) { throw "metadata.json non trovato: $Metadata" }
        $signArgs += @("/dlib", $Dlib, "/dmdf", $Metadata)
    }
}

if (-not (Test-Path $appExe)) { throw "EXE non trovato: $appExe (esegui prima la build PyInstaller)." }

# --- 1. Firma dell'EXE applicazione -------------------------------------------
Write-Host "`nFirma dell'EXE applicazione..." -ForegroundColor Cyan
& $signtool @signArgs $appExe
if ($LASTEXITCODE -ne 0) { throw "Firma EXE fallita (exit $LASTEXITCODE)." }

if ($SkipBuild) {
    Write-Host "`n-SkipBuild: installer non ricompilato." -ForegroundColor Yellow
} else {
    if (-not (Test-Path $Iscc)) { throw "ISCC.exe non trovato: $Iscc" }

    # --- 2. sign_tool.iss per Inno Setup --------------------------------------
    # Inno richiede i doppi apici per gli argomenti che contengono spazi.
    $parts = @($signtool) + $signArgs
    $quoted = @($parts | ForEach-Object {
        if ($_ -match '[\s"]' -or $_ -eq "") { '"' + ($_ -replace '"', '""') + '"' } else { $_ }
    })
    $command = ($quoted -join ' ') + ' $f'
    $content = @(
        '; File generato da tools\sign_and_build.ps1 - non modificare a mano.',
        '[SignTools]',
        'Name: frctool',
        ('Command: "' + ($command -replace '"', '""') + '"')
    ) -join "`r`n"
    Set-Content -Path $signToolIss -Value $content -Encoding UTF8
    Write-Host "Generato: $signToolIss"

    # --- 3. Build installer firmato -----------------------------------------
    Write-Host "`nBuild installer con firma di installer e uninstaller..." -ForegroundColor Cyan
    Push-Location $root
    try {
        & $Iscc "/DSIGN" $iss
        if ($LASTEXITCODE -ne 0) { throw "ISCC fallito (exit $LASTEXITCODE)." }
    }
    finally {
        Pop-Location
    }
}

# --- 4. Verifica --------------------------------------------------------------
Write-Host "`nVerifica firme:" -ForegroundColor Cyan
$targets = @($appExe, $installer)
$failed = $false
foreach ($t in $targets) {
    if (-not (Test-Path $t)) {
        Write-Host ("  MANCANTE  " + $t) -ForegroundColor Yellow
        $failed = $true
        continue
    }
    $sig = Get-AuthenticodeSignature $t
    $color = if ($sig.Status -eq "Valid") { "Green" } else { "Red" }
    if ($sig.Status -ne "Valid") { $failed = $true }
    Write-Host ("  {0,-10} {1}" -f $sig.Status, $t) -ForegroundColor $color
    if ($sig.SignerCertificate) {
        Write-Host ("             firmato da: " + $sig.SignerCertificate.Subject) -ForegroundColor DarkGray
    }
}

Write-Host "`nSHA-256:" -ForegroundColor Cyan
foreach ($t in $targets) {
    if (Test-Path $t) {
        $h = (Get-FileHash $t -Algorithm SHA256).Hash.ToLower()
        Write-Host ("  {0}  {1}" -f $h, (Split-Path -Leaf $t))
    }
}

if ($failed) {
    Write-Host "`nATTENZIONE: almeno un file non e firmato correttamente." -ForegroundColor Red
    Write-Host "Lo Store rifiuta installer EXE/MSI non firmati o con catena non attendibile." -ForegroundColor Red
    exit 1
}

Write-Host "`nFirme valide. Passi successivi:" -ForegroundColor Cyan
Write-Host "  1. carica l'installer firmato su un URL HTTPS versionato e immutabile;"
Write-Host "  2. aggiorna 'Package URL' in Partner Center (Packages);"
Write-Host "  3. aggiorna SHA256SUMS.txt e le note di rilascio (gli hash sono cambiati);"
Write-Host "  4. invia la sottomissione per la certificazione."
