; Inno Setup script for SAI_Calibration_Setup.exe (built by build_desktop.ps1)

[Setup]
AppId={{6E4C2B1A-5D3F-4A8E-9C7B-2F1D0E9A8B64}
AppName=SAI Calibration
AppVersion=1.0
AppPublisher=SAI Accurate Instruments
DefaultDirName={autopf}\SAI Calibration App
DefaultGroupName=SAI Calibration
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=SAI_Calibration_Setup
SetupIconFile=app\static\images\sai.ico
UninstallDisplayIcon={app}\SAI_Calibration.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\SAI_Calibration\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SAI Calibration"; Filename: "{app}\SAI_Calibration.exe"
Name: "{autodesktop}\SAI Calibration"; Filename: "{app}\SAI_Calibration.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SAI_Calibration.exe"; Description: "Open SAI Calibration now"; Flags: nowait postinstall skipifsilent
