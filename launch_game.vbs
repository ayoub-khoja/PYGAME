Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Get the folder where this script is located
scriptPath = FSO.GetParentFolderName(WScript.ScriptFullName)

' Change to that directory
WshShell.CurrentDirectory = scriptPath

' Run the Python script
WshShell.Run "python main.py", 1, False
