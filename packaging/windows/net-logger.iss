; Inno Setup script for Net Logger.
; Build after PyInstaller creates dist\Net Logger.exe:
;   iscc packaging\windows\net-logger.iss

#define AppName "Net Logger"
#define AppVersion "0.1.3"
#define AppPublisher "deltabrav0"
#define AppExeName "Net Logger.exe"

[Setup]
AppId={{F5D81CB1-4E7F-49D6-91A9-BD4E5A78B52F}
AppName=Net Logger
AppVersion=0.1.3
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Net Logger
DefaultGroupName=Net Logger
DisableProgramGroupPage=yes
OutputDir=..\..\dist\installer
OutputBaseFilename=NetLoggerSetup-0.1.3
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Net Logger"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{group}\Net Logger Data Folder"; Filename: "{userappdata}\Net Logger"
Name: "{autodesktop}\Net Logger"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch Net Logger"; Flags: nowait postinstall skipifsilent

[Dirs]
Name: "{userappdata}\Net Logger"
