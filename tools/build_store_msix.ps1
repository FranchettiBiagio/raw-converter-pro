<#
    Build + firma + verifica del pacchetto MSIX con l'identita' reale di
    Partner Center.

    Da usare dopo la conversione del prodotto (o la creazione del nuovo
    prodotto MSIX), quando in Partner Center > Product identity sono
    disponibili Package/Identity/Name e Package/Identity/Publisher.

    Uso:
      .\tools\build_store_msix.ps1 `
        -Identity "12345FranchettiAcademy.FranchettiRawConverterPro" `
        -Publisher "CN=1A2B3C4D-1111-2222-3333-444455556666"

    Lo script:
      1. ricompila il pacchetto con i valori indicati;
      2. crea/usa un certificato self-signed con lo stesso subject del
         publisher e firma il pacchetto;
      3. estrae il manifest dal pacchetto e verifica che identita',
         publisher e versione coincidano;
      4. controlla che il firmatario coincida con il publisher;
      5. stampa SHA-256 e i passi successivi.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Identity,

    [Parameter(Mandatory = $true)]
    [string]$Publisher,

    [string]$Version = "2.58.1.0",
    [string]$PublisherDisplay = "Franchetti Academy",
    [string]$DisplayName = "Franchetti Raw Converter Pro",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

if ($Publisher -notmatch '^CN=.+') {
    throw "Publisher non valido: deve iniziare con 'CN=' (valore Package/Identity/Publisher di Partner Center)."
}
if ($Identity -match '^FranchettiAcademy\.' -and $Publisher -eq "CN=FranchettiAcademy") {
    throw "Stai usando l'identita' provvisoria: inserisci i valori reali di Partner Center."
}

$out = Join-Path $root ("Output\FranchettiRawConverterPro_" + $Version + "_x64.msix")

Write-Host "Build pacchetto..." -ForegroundColor Cyan
& $Python (Join-Path $root "tools\build_msix.py") `
    --identity $Identity `
    --publisher $Publisher `
    --version $Version `
    --publisher-display $PublisherDisplay `
    --display-name $DisplayName `
    --out $out
if ($LASTEXITCODE -ne 0) { throw "Build MSIX fallita (exit $LASTEXITCODE)." }

Write-Host "`nFirma..." -ForegroundColor Cyan
& (Join-Path $root "tools\sign_msix_dev.ps1") `
    -Package $out `
    -Publisher $Publisher `
    -IdentityName $Identity
if ($LASTEXITCODE -ne 0) { throw "Firma MSIX fallita (exit $LASTEXITCODE)." }

# --- verifica contenuto del pacchetto ----------------------------------------
Write-Host "`nVerifica manifest nel pacchetto..." -ForegroundColor Cyan
$tmp = Join-Path $env:TEMP ("msixcheck_" + [guid]::NewGuid().ToString("N"))
try {
    $sdkBin = Join-Path $root "tools\sdkbuildtools\bin"
    $makeappx = $null
    if (Test-Path $sdkBin) {
        $makeappx = Get-ChildItem $sdkBin -Recurse -Filter makeappx.exe -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\x64\\' } |
            Sort-Object FullName -Descending |
            Select-Object -First 1
    }
    if (-not $makeappx) {
        $makeappx = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin" -Recurse -Filter makeappx.exe -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\x64\\' } |
            Sort-Object FullName -Descending |
            Select-Object -First 1
    }
    if (-not $makeappx) { throw "makeappx.exe non trovato." }

    & $makeappx.FullName unpack /p $out /d $tmp /o | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "makeappx unpack fallito (exit $LASTEXITCODE)." }

    [xml]$manifest = Get-Content (Join-Path $tmp "AppxManifest.xml")
    $id = $manifest.Package.Identity
    $checks = @(
        @{ Nome = "Identity/@Name";        Atteso = $Identity;  Trovato = $id.Name },
        @{ Nome = "Identity/@Publisher";   Atteso = $Publisher; Trovato = $id.Publisher },
        @{ Nome = "Identity/@Version";     Atteso = $Version;   Trovato = $id.Version },
        @{ Nome = "Identity/@Architecture"; Atteso = "x64";     Trovato = $id.ProcessorArchitecture }
    )
    $bad = $false
    foreach ($c in $checks) {
        $ok = ($c.Atteso -eq $c.Trovato)
        if (-not $ok) { $bad = $true }
        $color = if ($ok) { "Green" } else { "Red" }
        Write-Host ("  {0,-26} {1}" -f $c.Nome, $c.Trovato) -ForegroundColor $color
    }
    if ($bad) { throw "Il manifest nel pacchetto non corrisponde ai valori richiesti." }
}
finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

# --- verifica firmatario ------------------------------------------------------
$sig = Get-AuthenticodeSignature $out
if (-not $sig.SignerCertificate) { throw "Il pacchetto non risulta firmato." }
if ($sig.SignerCertificate.Subject -ne $Publisher) {
    throw ("Firmatario '" + $sig.SignerCertificate.Subject + "' diverso dal publisher '" + $Publisher + "'.")
}
Write-Host ("`nFirmatario: " + $sig.SignerCertificate.Subject) -ForegroundColor Green
Write-Host ("Scadenza:   " + $sig.SignerCertificate.NotAfter.ToString("yyyy-MM-dd"))
Write-Host ("Stato:      " + $sig.Status + " (self-signed: normale prima dell'upload)") -ForegroundColor Yellow

$hash = (Get-FileHash $out -Algorithm SHA256).Hash.ToLower()
Write-Host ("`nPacchetto: " + $out)
Write-Host ("SHA-256:   " + $hash)

Write-Host "`nPassi successivi:" -ForegroundColor Cyan
Write-Host "  1. Partner Center > prodotto > Packages > carica il .msix"
Write-Host "  2. la versione deve essere superiore all'ultima pubblicata"
Write-Host "  3. incolla le note di certificazione da store_assets\MSIX_CERTIFICATION_NOTES.md"
Write-Host "  4. invia per la certificazione (Microsoft ri-firma il pacchetto)"
