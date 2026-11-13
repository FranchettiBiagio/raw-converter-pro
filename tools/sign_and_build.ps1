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
      .\tools\sign_and_build.ps1 -Mode Azure -Account frcsigning -Profile frc-public
      .\tools\sign_and_build.ps1 -Mode Store -Thumbprint ABC123...
      .\tools\sign_and_build.ps1 -Mode Pfx -PfxPath C:\certs\frc.pfx -PfxPassword "***"

    Prerequisiti (vedi store_assets\AZURE_ARTIFACT_SIGNING_SETUP.md):
      - signtool.exe dal Windows SDK (Signing Tools) >= 10.0.22621.755
      - dlib Azure Artifact Signing (tools\artifactsigning\<ver>\bin\x64)
      - .NET 8/10 runtime + Visual C++ Redistributable
      - certificato valido: Artifact Signing, oppure OV/IV su token
    Un certificato self-signed NON e accettato dallo Store.
#>

[CmdletBinding()]
param(
    [ValidateSet("Azure", "Store", "Pfx")]
    [string]$Mode = "Azure",

    # --- Azure Artifact Signing ---
    [string]$Account,
    [string]$Profile,
    [string]$Endpoint = "https://weu.codesigning.azure.net",
    [string]$Metadata,
    [string]$Dlib,

    # --- Certificato locale ---
    [string]$PfxPath,
    [string]$PfxPassword,
    [string]$Thumbprint,

    # --- Build ---
    [string]$TimestampUrl,
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
    throw "signtool.exe non trovato. Installa 'Windows SDK > Signing Tools' (min. 10.0.22621.755)."
}

function Find-Dlib {
    param([string]$Explicit)

    if ($Explicit) {
        if (-not (Test-Path $Explicit)) { throw "Dlib non trovata: $Explicit" }
        return (Resolve-Path $Explicit).Path
    }

    $base = Join-Path $root "tools\artifactsigning"
    if (Test-Path $base) {
        $versions = Get-ChildItem $base -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^\d+(\.\d+)+$' } |
            Sort-Object { [version]$_.Name } -Descending
        foreach ($v in $versions) {
            $dll = Join-Path $v.FullName "bin\x64\Azure.CodeSigning.Dlib.dll"
            if (Test-Path $dll) { return $dll }
        }
    }

    $candidates = @(
        (Join-Path $env:ProgramFiles "Microsoft\Artifact Signing Client Tools\bin\x64\Azure.CodeSigning.Dlib.dll"),
        (Join-Path ${env:ProgramFiles(x86)} "Microsoft\Artifact Signing Client Tools\bin\x64\Azure.CodeSigning.Dlib.dll"),
        (Join-Path $env:ProgramFiles "Microsoft\Trusted Signing Client Tools\bin\x64\Azure.CodeSigning.Dlib.dll")
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }

    throw "Azure.CodeSigning.Dlib.dll non trovata. Esegui: .\tools\get-artifact-signing-client.ps1"
}

$signtool = Find-SignTool
Write-Host "signtool: $signtool"

# --- Argomenti di firma -------------------------------------------------------
$signArgs = @("sign", "/fd", "SHA256")

switch ($Mode) {
    "Pfx" {
        if (-not (Test-Path $PfxPath)) { throw "PFX non trovato: $PfxPath" }
        if (-not $PfxPassword) { throw "Specifica -PfxPassword." }
        $signArgs += @("/f", $PfxPath, "/p", $PfxPassword)
        if (-not $TimestampUrl) { $TimestampUrl = "http://timestamp.digicert.com" }
    }
    "Store" {
        if (-not $Thumbprint) { throw "Specifica -Thumbprint del certificato in CurrentUser\My." }
        $cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Thumbprint -eq $Thumbprint }
        if (-not $cert) { throw "Certificato $Thumbprint non trovato in Cert:\CurrentUser\My." }
        $signArgs += @("/sha1", $Thumbprint)
        if (-not $TimestampUrl) { $TimestampUrl = "http://timestamp.digicert.com" }
    }
    "Azure" {
        $dlibPath = Find-Dlib -Explicit $Dlib
        Write-Host "dlib: $dlibPath"

        if (-not $Metadata) {
            if (-not $Account -or -not $Profile) {
                throw "Per -Mode Azure servono -Account e -Profile (oppure -Metadata con un file gia pronto)."
            }
            $Metadata = Join-Path $root "tools\metadata.json"
            $payload = [ordered]@{
                Endpoint               = $Endpoint
                CodeSigningAccountName = $Account
                CertificateProfileName = $Profile
                CorrelationId          = "FranchettiRawConverterPro-2.58.1"
            }
            $json = $payload | ConvertTo-Json
            [System.IO.File]::WriteAllText($Metadata, $json, (New-Object System.Text.UTF8Encoding($false)))
            Write-Host "metadata generato: $Metadata"
        }
        if (-not (Test-Path $Metadata)) { throw "metadata.json non trovato: $Metadata" }

        $signArgs += @("/dlib", $dlibPath, "/dmdf", (Resolve-Path $Metadata).Path)
        # I certificati Artifact Signing durano 3 giorni: il timestamp e obbligatorio.
        if (-not $TimestampUrl) { $TimestampUrl = "http://timestamp.acs.microsoft.com" }
    }
}

$signArgs += @("/tr", $TimestampUrl, "/td", "SHA256")
Write-Host "timestamp: $TimestampUrl"

if (-not (Test-Path $appExe)) { throw "EXE non trovato: $appExe (esegui prima la build PyInstaller)." }

# --- 1. Firma dell'EXE applicazione ------------------------------------------
Write-Host "`nFirma dell'EXE applicazione..." -ForegroundColor Cyan
& $signtool @signArgs $appExe
if ($LASTEXITCODE -ne 0) { throw "Firma EXE fallita (exit $LASTEXITCODE). Vedi gli errori comuni in store_assets\AZURE_ARTIFACT_SIGNING_SETUP.md" }

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
    [System.IO.File]::WriteAllText($signToolIss, $content, (New-Object System.Text.UTF8Encoding($false)))

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
