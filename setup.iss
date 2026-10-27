; Inno Setup Script for Franchetti Raw Converter Pro v2.54.0
; Build: iscc setup.iss
; Output: Output/Franchetti_Raw_Converter_Setup_v2.54.0.exe

#define AppName "Franchetti Raw Converter Pro"
#define AppVersion "2.54.0"
#define AppVersionTuple "2.54.0.0"
#define AppPublisher "Franchetti"
#define AppWebsite "https://github.com/FranchettiBiagio/raw-converter-pro"
#define AppExeName "FranchettiRawConverterPro.exe"
#define SourceExe "dist\FranchettiRawConverterPro.exe"
#define OutputBaseName "Franchetti_Raw_Converter_Setup_v2.54.0"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppWebsite}
AppSupportURL={#AppWebsite}
AppUpdatesURL={#AppWebsite}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename={#OutputBaseName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
PrivilegesRequired=lowest
UsePreviousAppDir=no
UsePreviousGroup=no
UsePreviousLanguage=no
CreateAppDir=yes
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=no
DisableFinishedPage=no
ShowLanguageDialog=auto
LicenseFile=LICENSE
SetupIconFile=foto\logo_store1080-frc_1.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}
UninstallDisplaySize=65000000
UninstallFilesDir={app}

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "PRIVACY.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "USER_MANUAL.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "GUIDA_COMPLETA.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "GUIDA_COMPLETA.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "FAQ.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Comment: "Convertitore RAW professionale con pipeline Y/Cb/Cr e denoise ISO"
Name: "{group}\Guida completa"; Filename: "{app}\GUIDA_COMPLETA.html"; WorkingDir: "{app}"; Comment: "Guida elementare a tutte le funzioni e impostazioni consigliate"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"; WorkingDir: "{app}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Comment: "Convertitore RAW professionale"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[UninstallRun]
; Cleanup vuoto - nessun registro, nessun AppData, nessuna traccia

[Code]
function InitializeSetup(): Boolean;
begin
  // Richiede Windows 10 o superiore ($0A000000 = 10.0.0)
  if GetWindowsVersion < $0A000000 then
  begin
    MsgBox('Franchetti Raw Converter Pro richiede Windows 10 o superiore.'#13#10 +
           'Aggiorna Windows per installare il programma.', mbError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;
