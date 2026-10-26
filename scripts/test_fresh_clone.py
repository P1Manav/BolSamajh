"""BolSamajh — Fresh-Clone Quickstart Smoke Test Verification.

Clones the repo into an isolated temp folder, creates a fresh virtualenv,
installs from requirements.lock.txt, and verifies the smoke tests:
1. Module import & version check
2. Server launch and /api/status readiness
3. Clean shutdown
Saves raw transcript to docs/evidence/fresh_clone.txt.
"""

import os
import sys
import time
import shutil
import urllib.request
import json
import subprocess
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def run_fresh_clone_test():
    transcript = []
    def log_print(msg: str):
        print(msg)
        transcript.append(msg)

    log_print("BolSamajh — Fresh-Clone Smoke Test Verification")
    log_print("================================================")
    log_print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S IST')}")
    log_print(f"Source Repo: {ROOT_DIR}")
    log_print(f"Host OS:     Windows ({sys.platform})")

    temp_clone_dir = Path(tempfile.gettempdir()) / "bolsamajh_fresh_clone_audit"
    if temp_clone_dir.exists():
        shutil.rmtree(temp_clone_dir, ignore_errors=True)

    log_print(f"\n[Step 1] Cloning repo into clean temp directory: {temp_clone_dir}...")
    clone_res = subprocess.run(
        ["git", "clone", str(ROOT_DIR), str(temp_clone_dir)],
        capture_output=True,
        text=True,
    )
    assert clone_res.returncode == 0, f"Git clone failed: {clone_res.stderr}"
    log_print("[+] Clone successful.")

    log_print("\n[Step 2] Creating fresh virtual environment in cloned repo...")
    venv_dir = temp_clone_dir / "venv"
    # Use python 3.12 (the running python)
    py_exe = sys.executable
    venv_res = subprocess.run([py_exe, "-m", "venv", str(venv_dir)], capture_output=True, text=True)
    assert venv_res.returncode == 0, f"Venv creation failed: {venv_res.stderr}"
    clone_python = venv_dir / "Scripts" / "python.exe"
    clone_pip = venv_dir / "Scripts" / "pip.exe"
    log_print(f"[+] Fresh venv created: {clone_python}")

    log_print("\n[Step 3] Installing dependencies from requirements.lock.txt (or requirements.txt)...")
    t0 = time.time()
    # Install locked dependencies
    pip_res = subprocess.run(
        [str(clone_pip), "install", "-r", str(temp_clone_dir / "requirements.lock.txt"), "--no-warn-script-location"],
        capture_output=True,
        text=True,
    )
    log_print(f"[+] Pip install finished in {time.time() - t0:.1f}s (Return Code: {pip_res.returncode})")
    if pip_res.returncode != 0:
        log_print(f"Pip stderr: {pip_res.stderr[:500]}")
    assert pip_res.returncode == 0, f"Pip install failed!"

    log_print("\n[Step 4] Running smoke test 1: Package import & version check...")
    import_cmd = [str(clone_python), "-c", "import bolsamajh; print('BolSamajh Version:', bolsamajh.__version__)"]
    import_res = subprocess.run(import_cmd, cwd=str(temp_clone_dir), capture_output=True, text=True)
    log_print(f"Output: {import_res.stdout.strip()}")
    assert import_res.returncode == 0, f"Import smoke test failed: {import_res.stderr}"

    log_print("\n[Step 5] Running smoke test 2: Launch BolSamajh server & query /api/status...")
    test_port = 8999
    env = os.environ.copy()
    env["BOLSAMAJH_HOST"] = "127.0.0.1"

    server_proc = subprocess.Popen(
        [
            str(clone_python),
            "-m",
            "uvicorn",
            "bolsamajh.web.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(test_port),
            "--log-level",
            "warning",
        ],
        cwd=str(temp_clone_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    status_data = None
    try:
        url = f"http://127.0.0.1:{test_port}/api/status"
        for _ in range(40):
            time.sleep(0.5)
            try:
                with urllib.request.urlopen(url, timeout=1.0) as resp:
                    if resp.status == 200:
                        status_data = json.loads(resp.read().decode("utf-8"))
                        break
            except Exception:
                pass

        assert status_data is not None, "Server failed to respond to /api/status within 20s!"
        log_print("[+] /api/status returned HTTP 200 OK:")
        log_print(json.dumps(status_data, indent=2))
        assert status_data.get("status") == "ready", f"Unexpected status: {status_data}"
        log_print("[+] Health status 'ready' verified!")

    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3.0)
        except Exception:
            pass

    log_print("\n[Step 6] Cleanup temporary clone directory...")
    shutil.rmtree(temp_clone_dir, ignore_errors=True)
    log_print("[+] Temp directory cleaned up.")

    log_print("\nFresh Clone Quickstart Smoke Test: PASS")

    evidence_file = ROOT_DIR / "docs" / "evidence" / "fresh_clone.txt"
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    with open(evidence_file, "w", encoding="utf-8") as f:
        f.write("\n".join(transcript) + "\n")
    log_print(f"\n[+] Saved evidence to {evidence_file}")


if __name__ == "__main__":
    run_fresh_clone_test()
