; Inno Setup Script for Cognitive Maze
; Professional Windows Installer with Desktop/Start Menu shortcuts, clean uninstaller, and low-privilege support for school labs.

#define MyAppName "Cognitive Maze"
#define MyAppVersion "1.2.4"
#define MyAppPublisher "Cognitive Maze Development Team"
#define MyAppURL "https://github.com/workingNeko/2DGameCognitiveQuest"
#define MyAppExeName "CognitiveMaze.exe"

[Setup]
AppId={{E65B9071-8F32-47DE-B1F7-C1959846EAF1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppCopyright=Copyright (C) 2026 Cognitive Maze Development Team. Independent educational software.
VersionInfoVersion=1.2.4.0
VersionInfoCopyright=Copyright (C) 2026 Cognitive Maze Development Team
VersionInfoDescription=Cognitive Maze - Interactive Grade 2 Mathematics Adventure
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=CognitiveMaze-Setup-v{#MyAppVersion}
SetupIconFile=assets\images\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\CognitiveMaze\*"; DestDir: "{app}"; Excludes: "db\saves\*"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\CognitiveMaze\db\saves\*"; DestDir: "{app}\db\saves"; Flags: onlyifdoesntexist recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\images\icon.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\images\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

