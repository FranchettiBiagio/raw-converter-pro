<#
    Elenca i certificati di firma codice disponibili per l'utente corrente.

    Serve dopo aver installato un certificato IV/OV su token o aver attivato
    un servizio di firma cloud (SSL.com eSigner CKA, Certum SimplySign): il
    certificato compare in Cert:\CurrentUser\My e va passato a
    sign_and_build.ps1 -Mode Store -Thumbprint <THUMBPRINT>.

    Uso:
      .\tools\check-signing-cert.ps1
#>

$ErrorActionPreference = "Stop"
$now = Get-Date

$all = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert -ErrorAction SilentlyContinue

if (-not $all) {
    Write-Host "Nessun certificato di firma codice in Cert:\CurrentUser\My." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Se usi un servizio cloud:" -ForegroundColor Cyan
    Write-Host "  - SSL.com eSigner: avvia eSigner CKA e completa l'enroll del certificato"
    Write-Host "  - Certum SimplySign: avvia SimplySign Desktop e accedi"
    Write-Host "Se usi un token USB: inserisci il token e verifica che il driver sia installato."
    exit 1
}

function Test-Usable {
    param($Cert)
    if (-not $Cert.HasPrivateKey) { return $false }
    if ($Cert.NotAfter -le $now) { return $false }
    # self-signed: non accettato dallo Store
    if ($Cert.Subject -eq $Cert.Issuer) { return $false }
    # placeholder di altri software (es. driver virtuali)
    if ($Cert.Subject -match 'CN=0{8}-0{4}-0{4}-0{4}-0{12}') { return $false }
    return $true
}

$usable = @()
foreach ($c in ($all | Sort-Object NotAfter -Descending)) {
    $ok = Test-Usable $c
    if ($ok) { $usable += $c }

    $provider = ""
    try {
        if ($c.HasPrivateKey -and $c.PrivateKey) {
            $provider = $c.PrivateKey.CspKeyContainerInfo.ProviderName
        }
    }
    catch { $provider = "(provider non leggibile)" }

    $note = if ($ok) { "utilizzabile" }
            elseif ($c.Subject -eq $c.Issuer) { "self-signed: NON accettato dallo Store" }
            elseif (-not $c.HasPrivateKey) { "senza chiave privata" }
            else { "scaduto" }

    Write-Host ("[{0}] {1}" -f $note, $c.Subject)
    Write-Host ("      issuer:     " + $c.Issuer)
    Write-Host ("      scadenza:   " + $c.NotAfter.ToString("yyyy-MM-dd") + "  (giorni: " + [int]($c.NotAfter - $now).TotalDays + ")")
    Write-Host ("      provider:   " + $provider)
    Write-Host ("      thumbprint: " + $c.Thumbprint)
    Write-Host ""
}

if (-not $usable) {
    Write-Host "Nessun certificato utilizzabile per il Microsoft Store." -ForegroundColor Red
    Write-Host "Serve un certificato IV/OV di una CA pubblica, con chiave privata e non scaduto." -ForegroundColor Yellow
    Write-Host "Vedi store_assets\CODE_SIGNING_INDIVIDUAL_IT.md" -ForegroundColor Yellow
    exit 1
}

$pick = $usable | Select-Object -First 1
Write-Host "Certificato consigliato:" -ForegroundColor Green
Write-Host ("  " + $pick.Subject)
Write-Host ("  thumbprint: " + $pick.Thumbprint)
Write-Host ""
Write-Host "Firma con:" -ForegroundColor Cyan
Write-Host ("  .\tools\sign_and_build.ps1 -Mode Store -Thumbprint " + $pick.Thumbprint)
