; Kokoro Reader installer (Inno Setup 7). Build: build\tools\innosetup\ISCC.exe build\KokoroReader.iss
#define AppName "Kokoro Reader"
#define AppVersion "1.1.1"
#define Dist "dist\KokoroReader"

[Setup]
AppId={{6B0E3A51-7C2D-4E0B-9F4A-2C8D5E1B7A31}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=ETINSTW
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=output
OutputBaseFilename=KokoroReader-Setup-{#AppVersion}
SetupIconFile={#Dist}\app\static\icon.ico
UninstallDisplayIcon={app}\app\static\icon.ico
UninstallDisplayName={#AppName}
InfoBeforeFile={#Dist}\README.txt
Compression=lzma2/max
SolidCompression=yes
LZMANumBlockThreads=4
CloseApplications=yes
WizardStyle=modern
ShowLanguageDialog=auto

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "zh"; MessagesFile: "compiler:Languages\ChineseTraditional.isl"

[CustomMessages]
en.DesktopIcon=Create a desktop shortcut
zh.DesktopIcon=建立桌面捷徑
en.LaunchApp=Start Kokoro Reader now
zh.LaunchApp=立即啟動 Kokoro Reader
en.OpenManual=Open the Getting Started manual
zh.OpenManual=開啟使用入門手冊

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; Flags: unchecked

[Files]
Source: "{#Dist}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\app\launcher.pyw"""; WorkingDir: "{app}"; IconFilename: "{app}\app\static\icon.ico"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\app\launcher.pyw"""; WorkingDir: "{app}"; IconFilename: "{app}\app\static\icon.ico"; Tasks: desktopicon
Name: "{autoprograms}\{#AppName} – Getting Started"; Filename: "{app}\Kokoro Reader - Getting Started.pdf"
Name: "{autoprograms}\{#AppName} – 使用入門"; Filename: "{app}\Kokoro Reader - 使用入門.pdf"

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: """{app}\app\launcher.pyw"""; WorkingDir: "{app}"; Description: "{cm:LaunchApp}"; Flags: postinstall nowait skipifsilent
Filename: "{app}\Kokoro Reader - Getting Started.pdf"; Description: "{cm:OpenManual}"; Flags: postinstall shellexec nowait skipifsilent; Languages: en
Filename: "{app}\Kokoro Reader - 使用入門.pdf"; Description: "{cm:OpenManual}"; Flags: postinstall shellexec nowait skipifsilent; Languages: zh

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\KokoroReader"
