' ==============================================================================
' BolSamajh — Silent Windowless Windows Launcher
' Double-click to launch BolSamajh silently into system tray and floating HUD.
' ==============================================================================
Option Explicit
Dim WshShell, fso, strPath, strPython, strCmd

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath

If fso.FileExists(strPath & "\dist\BolSamajh\BolSamajh.exe") Then
    strCmd = """" & strPath & "\dist\BolSamajh\BolSamajh.exe"""
ElseIf fso.FileExists(strPath & "\venv\Scripts\pythonw.exe") Then
    strCmd = """" & strPath & "\venv\Scripts\pythonw.exe"" -m bolsamajh.main"
ElseIf fso.FileExists(strPath & "\venv\Scripts\python.exe") Then
    strCmd = """" & strPath & "\venv\Scripts\python.exe"" -m bolsamajh.main"
Else
    strCmd = "python -m bolsamajh.main"
End If

WshShell.Run strCmd, 0, False
