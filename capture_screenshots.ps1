<# 
.SYNOPSIS
    Automatizza cattura 5 screenshot per uptodown.dev - Franchetti Raw Converter Pro

.DESCRIPTION
    Lancia l'app, guida l'utente attraverso i 5 step e cattura screenshot
    con Win+Shift+S (Strumento ritaglio) o PrintScreen automatico.

.NOTES
    Requisiti: Windows 10/11, app in dist\FranchettiRawConverterPro.exe
    Output: screenshots\01_main_window.png ... 05_watermark_detail.png
#>

param(
    [string]$ExePath = "dist\FranchettiRawConverterPro.exe",
    [string]$OutputDir = "screenshots",
    [string]$TestRawFolder = ""  # Opzionale: cartella con RAW di test
)

# ─── Config ───
$Width = 1920
$Height = 1080
$Dpi = 96
$WaitAfterLaunch = 3
$WaitAfterAction = 2

# ─── Setup ───
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$FullExe = Join-Path $ScriptDir $ExePath
$FullOut = Join-Path $ScriptDir $OutputDir

if (-not (Test-Path $FullExe)) {
    Write-Error "Eseguibile non trovato: $FullExe"
    exit 1
}

if (-not (Test-Path $FullOut)) { New-Item -ItemType Directory -Path $FullOut | Out-Null }

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Capture-Screen {
    param([string]$Filename, [string]$Message)
    
    Write-Host "`n$Message" -ForegroundColor Cyan
    Write-Host "Premi INVIO quando pronto, poi usa Win+Shift+S per selezionare area..." -ForegroundColor Yellow
    Read-Host
    
    # Apre Strumento ritaglio (Win+Shift+S)
    $wshell = New-Object -ComObject WScript.Shell
    $wshell.SendKeys("^+s")  # Ctrl+Shift+S = Win+Shift+S su Win10/11
    Start-Sleep 1
    
    Write-Host "Seleziona l'area dell'app, poi incolla in Paint e salva come $Filename`nOppure: cattura tutto schermo (Print) e ritaglia dopo." -ForegroundColor Gray
    Read-Host "Premi INVIO dopo aver salvato il file in $FullOut\$Filename"
    
    # Verifica file
    $outFile = Join-Path $FullOut $Filename
    if (Test-Path $outFile) {
        Write-Host "✅ Salvato: $outFile" -ForegroundColor Green
    } else {
        Write-Warning "File non trovato: $outFile (controlla dove hai salvato)"
    }
}

function Launch-App {
    Write-Host "Avvio app..." -ForegroundColor Cyan
    $proc = Start-Process -FilePath $FullExe -PassThru
    Start-Sleep $WaitAfterLaunch
    return $proc
}

function Load-TestFiles {
    param($proc)
    if ($TestRawFolder -and (Test-Path $TestRawFolder)) {
        Write-Host "Caricamento file RAW da $TestRawFolder..." -ForegroundColor Cyan
        # Simula click "Seleziona Cartella" - richiede UI Automation complessa
        Write-Host "MANUALE: Clicca '📁 Seleziona Cartella' e scegli: $TestRawFolder" -ForegroundColor Yellow
        Read-Host "Premi INVIO quando file caricati"
    } else {
        Write-Host "Nessuna cartella test specificata. Carica file manualmente." -ForegroundColor Yellow
        Read-Host "Premi INVIO quando hai 8-12 file RAW nella lista"
    }
}

function Set-Options {
    Write-Host "IMPOSTA OPZIONI per screenshot #2:" -ForegroundColor Cyan
    Write-Host "  - Dimensione max: 1920 (default)" -ForegroundColor Gray
    Write-Host "  - Qualità JPG: 85 (default)" -ForegroundColor Gray
    Write-Host "  - Copyright: '© Mario Rossi 2024 | mariorossi.photo'" -ForegroundColor Gray
    Write-Host "  - Font size: 16" -ForegroundColor Gray
    Write-Host "  - Mantieni nome: ON, Prefisso: 'MR_'" -ForegroundColor Gray
    Read-Host "Premi INVIO quando fatto"
}

function Start-Conversion {
    Write-Host "AVVIA CONVERSIONE per screenshot #3:" -ForegroundColor Cyan
    Write-Host "  - Clicca '▶ AVVIA CONVERSIONE'" -ForegroundColor Gray
    Write-Host "  - Attendi barra progresso ~60% (es. 42/70)" -ForegroundColor Gray
    Read-Host "Premi INVIO quando barra al ~60% e log mostra righe verdi"
}

function Open-OutputFolder {
    param($proc)
    Write-Host "APRI CARTELLA OUTPUT per screenshot #4:" -ForegroundColor Cyan
    $outPath = Join-Path $env:USERPROFILE "Pictures\Converted"
    if (-not (Test-Path $outPath)) { $outPath = Join-Path $env:USERPROFILE "Desktop\Converted" }
    Write-Host "  - Apri Esplora Risorse su: $outPath" -ForegroundColor Gray
    Write-Host "  - Vista 'Icone grandi' o 'Dettagli'" -ForegroundColor Gray
    Write-Host "  - Devono vedersi 15+ file .jpg" -ForegroundColor Gray
    Read-Host "Premi INVIO quando pronto"
}

function Capture-Watermark {
    Write-Host "ZOOM WATERMARK per screenshot #5:" -ForegroundColor Cyan
    Write-Host "  - Apri un JPG generato in 'Visualizzatore foto' (default Win10/11)" -ForegroundColor Gray
    Write-Host "  - Zoom 100% o 200% (Ctrl+rotellina)" -ForegroundColor Gray
    Write-Host "  - Vai in ANGOLO BASSO DESTRA" -ForegroundColor Gray
    Write-Host "  - Deve vedersi watermark: '© Mario Rossi 2024 | mariorossi.photo'" -ForegroundColor Gray
    Read-Host "Premi INVIO quando pronto"
}

# ─── MAIN ───
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  CAPTURE SCREENSHOTS - Franchetti Raw Converter Pro       ║" -ForegroundColor Cyan
Write-Host "║  5 screenshot per uptodown.dev                             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`nOutput: $FullOut"
Write-Host "Eseguibile: $FullExe`n"

# 1. Avvia
$proc = Launch-App

# 2. Carica file
Load-TestFiles $proc

# 3. Screenshot #1 - Main window
Capture-Screen "01_main_window.png" "📸 SCREENSHOT 1/5 - Finestra principale con file caricati"

# 4. Imposta opzioni + Screenshot #2
Set-Options
Capture-Screen "02_options_panel.png" "📸 SCREENSHOT 2/5 - Pannello opzioni (menu dimensione aperto, copyright visibile)"

# 5. Avvia conversione + Screenshot #3
Start-Conversion
Capture-Screen "03_conversion_progress.png" "📸 SCREENSHOT 3/5 - Conversione in corso (~60%, log verde, ANNULLA attivo)"

# 6. Apri output + Screenshot #4
Open-OutputFolder $proc
Capture-Screen "04_output_folder.png" "📸 SCREENSHOT 4/5 - Esplora Risorse cartella output (15+ JPG)"

# 7. Zoom watermark + Screenshot #5
Capture-Watermark
Capture-Screen "05_watermark_detail.png" "📸 SCREENSHOT 5/5 - Zoom 100-200% angolo basso destra (watermark leggibile)"

# 8. Chiusura
Write-Host "`n✅ TUTTI E 5 GLI SCREENSHOT RICHIESTI" -ForegroundColor Green
Write-Host "Cartella: $FullOut" -ForegroundColor Cyan
Get-ChildItem $FullOut -Filter "*.png" | ForEach-Object { 
    Write-Host "  $($_.Name) - $([math]::Round($_.Length/1KB)) KB" 
}

# Chiudi app
$proc | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "`nApp chiusa. Fatto!" -ForegroundColor Cyan