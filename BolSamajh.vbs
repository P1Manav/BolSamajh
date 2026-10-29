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

If fso.FileExists(strPath & "\venv\Scripts\pythonw.exe") Then
    strPython = """" & strPath & "\venv\Scripts\pythonw.exe"""
ElseIf fso.FileExists(strPath & "\venv\Scripts\python.exe") Then
    strPython = """" & strPath & "\venv\Scripts\python.exe"""
Else
    strPython = "python"
End If

strCmd = strPython & " -m bolsamajh.main"
WshShell.Run strCmd, 0, False
