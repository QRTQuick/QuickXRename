[Setup]
AppName=QuickXRename
AppVersion=0.1.0
DefaultDirName={pf}\QuickXRename
DefaultGroupName=QuickXRename
OutputBaseFilename=QuickXRename-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\..\dist\QuickXRename\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\QuickXRename"; Filename: "{app}\QuickXRename.exe"
