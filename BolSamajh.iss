; Script generated for Inno Setup 6
; BolSamajh — Hinglish Voice AI Companion for Windows
; Produces: BolSamajh-Setup-v1.1.0.exe

#define MyAppName "BolSamajh"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Manav"
#define MyAppURL "https://github.com/P1Manav/BolSamajh"
#define MyAppExeName "BolSamajh.exe"

[Setup]
; Per-user install: no administrator privileges needed
AppId={{D37F8E92-29C4-4A3C-9024-F41C283F11A5}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Programs\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=BolSamajh-Setup-v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\bolsamajh.ico
UninstallDisplayIcon={app}\assets\bolsamajh.ico
UninstallDisplayName={#MyAppName} (Voice AI Companion)

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Launch BolSamajh automatically when signing into Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "dist\BolSamajh\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\bolsamajh.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "samples\*"; DestDir: "{app}\samples"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\bolsamajh.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\bolsamajh.ico"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
