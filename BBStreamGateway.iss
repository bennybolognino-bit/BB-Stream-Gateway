#define MyAppName "BB Stream Gateway"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "BB"
#define MyAppExeName "BBStreamGateway.exe"

[Setup]
AppId={{A54C1639-D1C5-4F43-AF1B-6223C89AD511}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\BB Stream Gateway
DefaultGroupName=BB Stream Gateway
OutputDir=installer
OutputBaseFilename=BB-Stream-Gateway-Setup-1.0.2
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupLogging=yes
CloseApplications=yes
RestartApplications=no
UninstallDisplayName=BB Stream Gateway

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crea un collegamento sul desktop"; GroupDescription: "Collegamenti:"

[Files]
Source: "dist\BBStreamGateway\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\data"
Name: "{app}\logs"

[Icons]
Name: "{autoprograms}\BB Stream Gateway"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\BB Stream Gateway"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Avvia BB Stream Gateway"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"


