<#
    Firma un pacchetto MSIX per il test locale o per l'upload in Partner Center.

    Per il Microsoft Store la firma puo' essere anche self-signed: Microsoft
    ri-firma il pacchetto dopo la certificazione. L'unico vincolo e' che il
    soggetto del certificato coincida con Identity/@Publisher del manifest.

    Uso:
      .\tools\sign_msix_dev.ps1 -Package Output\FranchettiRawConverterPro_2.58.1.0_x64.msix
      .\tools\sign_msix_dev.ps1 -Package ... -Publisher "CN=XXXXXXX"   # publisher di Partner Center
      .\tools\sign_msix_dev.ps1 -Package ... -Install                 # firma + installa in prova

    -Install aggiunge il certificato in CurrentUser\TrustedPeople e registra
    il pacchetto con Add-AppxPackage (utile per verificare che l'app si avvii).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Package,
    [string]$Publisher = "CN=FranchettiAcademy",
    [string]$IdentityName = "FranchettiAcademy.FranchettiRawConverterPro",
    [switch]$Install,
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Package)) { throw "Pacchetto non trovato: $Package" }
$Package = (Resolve-Path $Package).Path

function Find-Tool {
    param([string]$Name)
    $roots = @(
        (Join-Path (Split-Path -Parent $PSScriptRoot) "tools\sdkbuildtools\bin"),
        "C:\Program Files (x86)\Windows Kits\10\bin"
    )
    foreach ($root in $roots) {
        if (Test-Path $root) {
            $found = Get-ChildItem $root -Recurse -Filter $Name -ErrorAction SilentlyContinue |
                Where-Object { $_.FullName -match '\\x64\\' } |
                Sort-Object FullName -Descending |
                Select-Object -First 1
            if ($found) { return $found.FullName }
        }
    }
    throw "$Name non trovato."
}

# --- certificato di firma -----------------------------------------------------
# signtool accetta solo certificati con EKU "Code Signing" (1.3.6.1.5.5.7.3.3):
# un certificato con un EKU diverso viene ignorato con l'errore
# "No certificates were found that met all the given criteria".
$codeSigningEku = "1.3.6.1.5.5.7.3.3"

$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
    Where-Object {
        $_.Subject -eq $Publisher -and
        $_.NotAfter -gt (Get-Date) -and
        $_.HasPrivateKey -and
        ($_.EnhancedKeyUsageList.ObjectId -contains $codeSigningEku)
    } |
    Sort-Object NotAfter -Descending |
    Select-Object -First 1

if (-not $cert) {
    Write-Host "Creo un certificato self-signed per il test: $Publisher"
    $cert = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject $Publisher `
        -KeyUsage DigitalSignature `
        -KeyAlgorithm RSA `
        -KeyLength 2048 `
        -HashAlgorithm SHA256 `
        -FriendlyName "FRC MSIX dev signing" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -NotAfter (Get-Date).AddYears(3)
}

Write-Host ("Certificato: " + $cert.Subject + "  " + $cert.Thumbprint)

$signtool = Find-Tool "signtool.exe"
& $signtool sign /fd SHA256 /sha1 $cert.Thumbprint /tr $TimestampUrl /td SHA256 $Package
if ($LASTEXITCODE -ne 0) { throw "Firma fallita (exit $LASTEXITCODE)." }

$sig = Get-AuthenticodeSignature $Package
Write-Host ("Firma: " + $sig.Status + "  " + $Package)
if ($sig.Status -ne "Valid") {
    Write-Host "Nota: 'UnknownError' e' normale per un certificato self-signed non ancora attendibile." -ForegroundColor Yellow
}

if ($Install) {
    $cerPath = [System.IO.Path]::ChangeExtension($Package, ".cer")
    Export-Certificate -Cert $cert -FilePath $cerPath -Type CERT | Out-Null

    # Per installare un MSIX con certificato self-signed il certificato deve
    # essere attendibile anche a livello di macchina: TrustedPeople per la
    # firma dell'app e Root per chiudere la catena. Richiede privilegi admin.
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        throw "L'installazione di prova richiede una shell da amministratore (trust store di macchina)."
    }

    Import-Certificate -FilePath $cerPath -CertStoreLocation "Cert:\LocalMachine\TrustedPeople" | Out-Null
    Import-Certificate -FilePath $cerPath -CertStoreLocation "Cert:\LocalMachine\Root" | Out-Null
    Write-Host "Certificato importato in LocalMachine\TrustedPeople e LocalMachine\Root"

    Add-AppxPackage -Path $Package
    $info = Get-AppxPackage -Name $IdentityName -ErrorAction SilentlyContinue
    if (-not $info) {
        $info = Get-AppxPackage | Where-Object { $_.SignatureKind -eq "Developer" } |
            Sort-Object InstallDate -Descending | Select-Object -First 1
    }
    Write-Host ("Installato: " + $info.Name + " " + $info.Version) -ForegroundColor Green
    Write-Host "Avvia l'app dal menu Start per la prova, poi rimuovila con:"
    Write-Host ("  Remove-AppxPackage " + $info.PackageFullName)
}
