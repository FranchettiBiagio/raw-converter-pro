# Guida Installazione e Deployment

**Franchetti Raw Converter Pro v2.50.1**  
*Opzioni per utenti singoli, IT admin, enterprise*

---

## 🎯 Utente Singolo (Consigliato)

### Download Diretto
1. Vai su [GitHub Releases](https://github.com/franchetti/raw-converter-pro/releases/latest) o [uptodown.dev](https://www.uptodown.dev/apps/franchetti-raw-converter-pro)
2. Scarica `FranchettiRawConverterPro.exe`
3. Sposta in cartella a scelta (es. `C:\Tools\`, `D:\Apps\`, Desktop)
4. **Doppio clic per avviare** — nessuna installazione

### Creare Collegamenti (Opzionale)
| Metodo | Comando |
|--------|---------|
| **Desktop** | Tasto destro sul `.exe` → "Invia a" → "Desktop (crea collegamento)" |
| **Start Menu** | Tasto destro → "Aggiungi a Start" |
| **Barra applicazioni** | Trascina `.exe` sulla taskbar |
| **Context Menu (Send To)** | `Win+R` → `shell:sendto` → incolla collegamento |

### Primo Avvio - SmartScreen
Windows potrebbe mostrare "Windows ha protetto il tuo PC":
1. Clicca **"Ulteriori informazioni"**
2. Clicca **"Esegui comunque"**
*Normale per eseguibili non firmati con certificato EV.*

---

## 🏢 Deployment Enterprise (IT Admin)

### Opzione 1: Copia File Semplice (GPO/Script)
```batch
@echo off
:: deploy_franchetti_raw_converter.bat
set SOURCE=\\server\share\software\FranchettiRawConverterPro.exe
set DEST=%PROGRAMFILES%\Franchetti Raw Converter Pro\
mkdir "%DEST%" 2>nul
copy /Y "%SOURCE%" "%DEST%"
:: Collegamento Start Menu per tutti gli utenti
set SHORTCUT="%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Franchetti Raw Converter Pro.lnk"
powershell -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%');$s.TargetPath='%DEST%FranchettiRawConverterPro.exe';$s.Save()"
```

**GPO**: Computer Configuration → Preferences → Windows Settings → Files (copia) + Shortcuts (collegamento)

### Opzione 2: Microsoft Intune (Win32 App)
1. **Intune Admin Center** → Apps → Windows → Add → **Windows app (Win32)**
2. **File**: `FranchettiRawConverterPro.exe` (carica direttamente)
3. **Install command**: `cmd /c "mkdir %ProgramFiles%\FranchettiRawConverterPro & copy FranchettiRawConverterPro.exe %ProgramFiles%\FranchettiRawConverterPro\"`
4. **Uninstall command**: `cmd /c "rmdir /s /q %ProgramFiles%\FranchettiRawConverterPro"`
5. **Detection rules**: File exists `%ProgramFiles%\FranchettiRawConverterPro\FranchettiRawConverterPro.exe`
6. **Requirements**: Windows 10 1809+, 64-bit, 100 MB disk
7. **Assign**: Required / Available per gruppi

### Opzione 3: Chocolatey / Winget (Community)
```yaml
# chocolatey package (da creare)
id: franchetti-raw-converter-pro
version: 2.50.1
url: https://github.com/FranchettiBiagio/raw-converter-pro/releases/download/v2.50.1/FranchettiRawConverterPro.exe
checksum: SHA256_HASH
checksumType: sha256
```

```bash
# winget (dopo pubblicazione su GitHub)
winget install --id Franchetti.RawConverterPro
```

### Opzione 4: SCCM / MEMCM
- **Application Type**: Windows app (.exe)
- **Installation Program**: `cmd /c copy FranchettiRawConverterPro.exe "C:\Program Files\Franchetti Raw Converter Pro\"`
- **Detection Method**: File system → `C:\Program Files\Franchetti Raw Converter Pro\FranchettiRawConverterPro.exe`
- **User Experience**: Install for system, hidden, allow restart

---

## 🔐 Code Signing (Produzione)

### Certificato EV Consigliato
| Tipo | Costo/Anno | SmartScreen | Reputation |
|------|------------|-------------|------------|
| **OV (Organization Validation)** | ~$200-400 | Warning iniziale | Build reputation |
| **EV (Extended Validation)** | ~$300-600 | **Immediate trust** | Instant reputation |

### Firmare l'Eseguibile
```cmd
:: signtool.exe (Windows SDK)
signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a FranchettiRawConverterPro.exe

:: Verifica
signtool verify /pa /v FranchettiRawConverterPro.exe
```

### AppLocker Rule (Allow Solo Firmato)
```xml
<RuleCollection Type="Exe" EnforcementMode="Enabled">
  <FilePublisherRule Id="{GUID}" Name="Franchetti Raw Converter Pro"
    Description="Official signed release" UserOrGroupSid="S-1-1-0" Action="Allow">
    <Conditions>
      <FilePublisherCondition PublisherName="O=Franchetti, L=Citta, S=Stato, C=IT"
        ProductName="Franchetti Raw Converter Pro" BinaryName="FranchettiRawConverterPro.exe">
        <BinaryVersionRange LowSection="2.50.1.0" HighSection="2.9999.9999.9999" />
      </FilePublisherCondition>
    </Conditions>
  </FilePublisherRule>
</RuleCollection>
```

---

## 🐳 Container / PortableApps / USB

### PortableApps.com Format
```
FranchettiRawConverterProPortable/
├── App/
│   └── AppInfo/
│       └── appinfo.ini
│   └── FranchettiRawConverterPro.exe
├── Data/
│   └── settings/ (vuoto, app non salva config)
├── Other/
│   └── Source/ (opzionale)
├── FranchettiRawConverterProPortable.exe (launcher)
└── help.html
```

**appinfo.ini**:
```ini
[Format]
Type=PortableApps.comFormat
Version=3.5

[Details]
Name=Franchetti Raw Converter Pro
AppID=FranchettiRawConverterPro
Publisher=Franchetti
Homepage=https://franchetti.dev/raw-converter-pro
Category=PhotoVideo
Description=RAW to JPEG converter with watermark
Language=Italian
Trademarks=Franchetti

[License]
Shareable=true
OpenSource=true
Freeware=true
CommercialUse=true
EULAVersion=1

[Version]
DisplayVersion=2.50.1
PackageVersion=2.50.1.0

[Control]
Start=FranchettiRawConverterPro.exe
```

### USB Stick / Chiavetta
- Copia solo `FranchettiRawConverterPro.exe` su chiavetta
- Esegui direttamente da qualsiasi PC Windows
- Nessuna traccia lasciata sul PC host

---

## 🔧 Configurazione Silenziosa (Pre-impostazioni)

L'app **non salva configurazioni** su disco (design choice per privacy/portabilità).  
Per pre-impostare valori default, modifica `main.py` prima del build:

```python
# In ConverterGUI.__init__ o _build_ui:
self.var_max_dim = tk.IntVar(value=3000)        # Default: 3000px invece di 1920
self.var_quality = tk.IntVar(value=90)          # Default: 90 invece di 85
self.var_copyright = tk.StringVar(value="© Studio Rossi 2024")
self.var_font_size = tk.IntVar(value=16)
self.var_keep_name = tk.BooleanVar(value=True)
self.var_prefix = tk.StringVar(value="SR_")
```

Poi ricompila: `python build_exe.py`

---

## 📋 Verifica Post-Installazione

| Test | Comando/Verifica |
|------|------------------|
| **Esecuzione base** | Doppio clic → GUI appare in <2s |
| **Conversione test** | Seleziona 1 RAW → Output JPG corretto |
| **Watermark visibile** | Apri JPG → copyright in basso destra |
| **Permessi** | Scrive in cartella utente, non richiede admin |
| **Antivirus** | Nessun blocco/quarantena |
| **SmartScreen** | "Esegui comunque" solo prima volta (non firmato) |
| **Rete** | `netstat -an` durante uso → nessuna connessione |

---

## 🗑️ Disinstallazione

| Metodo | Azione |
|--------|--------|
| **Portable/Utente** | Elimina `.exe` e collegamenti |
| **Enterprise (GPO/Intune)** | Rimuovi assignment → uninstalla automatico |
| **Script** | `rmdir /s /q "%PROGRAMFILES%\Franchetti Raw Converter Pro"` + rimuovi shortcuts |

*Nessun registro, nessun file in AppData, nessun servizio da fermare.*

---

## 📞 Supporto Deployment

- **Email IT**: `enterprise@franchetti.dev`
- **Documentazione**: Questo file + `TECHNICAL_SPECS.md`
- **Custom build**: Pre-impostazioni aziendali su richiesta

---

*Guida Installation v2.50.1 — Gennaio 2025*