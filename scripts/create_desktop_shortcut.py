"""Create a Windows desktop shortcut for BolSamajh with application icon."""

import os
import sys
from pathlib import Path


def create_shortcut():
    if sys.platform != "win32":
        print("Shortcut creation is only supported on Windows.")
        return

    root = Path(__file__).resolve().parent.parent
    exe_path = root / "dist" / "BolSamajh" / "BolSamajh.exe"
    vbs_path = root / "BolSamajh.vbs"
    bat_path = root / "BolSamajh.bat"

    if exe_path.exists():
        target_path = exe_path
    elif vbs_path.exists():
        target_path = vbs_path
    else:
        target_path = bat_path
    icon_path = root / "assets" / "bolsamajh.ico"

    desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    if not desktop.exists():
        print(f"Could not locate Desktop folder at {desktop}")
        return

    shortcut_path = desktop / "BolSamajh.lnk"

    try:
        import win32com.client

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.TargetPath = str(target_path)
        shortcut.WorkingDirectory = str(root)
        shortcut.Description = "BolSamajh — Bolo. Samjho. Hinglish Voice Companion"
        if icon_path.exists():
            shortcut.IconLocation = f"{icon_path},0"
        shortcut.save()
        print(f"Desktop shortcut created successfully at: {shortcut_path}")
    except Exception as e:
        # Fallback to PowerShell
        ps_cmd = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f'$s = $ws.CreateShortcut("{shortcut_path}"); '
            f'$s.TargetPath = "{target_path}"; '
            f'$s.WorkingDirectory = "{root}"; '
            f'$s.Description = "BolSamajh — Bolo. Samjho."; '
            f'if (Test-Path "{icon_path}") {{ $s.IconLocation = "{icon_path},0" }}; '
            f"$s.Save()"
        )
        import subprocess

        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True
        )
        if res.returncode == 0:
            print(f"Desktop shortcut created via PowerShell at: {shortcut_path}")
        else:
            print(f"Failed to create shortcut: {res.stderr or e}")


if __name__ == "__main__":
    create_shortcut()
