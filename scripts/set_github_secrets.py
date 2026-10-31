"""BolSamajh — GitHub Actions Secrets Auto-Configurator.

Reads 'github_secrets.env' and uploads non-empty secrets to GitHub Actions:
- Uses GitHub CLI (`gh secret set`) if installed and authenticated.
- Or uses GitHub REST API with a Personal Access Token (PAT).
- Or prints the exact values formatted for copy-pasting into GitHub web settings.
"""

import base64
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SECRETS_FILE = ROOT_DIR / "github_secrets.env"
REPO = "P1Manav/BolSamajh"


def load_secrets():
    if not SECRETS_FILE.exists():
        print(f"[!] '{SECRETS_FILE.name}' not found. Creating from template...")
        template = ROOT_DIR / "github_secrets.env.example"
        if template.exists():
            shutil.copy(template, SECRETS_FILE)
            print(f"[+] Created '{SECRETS_FILE.name}'. Fill in your keys and re-run.")
        return {}

    secrets = {}
    with open(SECRETS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'").strip('"')
                if v:
                    secrets[k] = v
    return secrets


def set_via_gh_cli(secrets):
    print("[*] Found GitHub CLI ('gh'). Setting secrets...")
    success = True
    for k, v in secrets.items():
        try:
            res = subprocess.run(
                ["gh", "secret", "set", k, "--body", v, "--repo", REPO],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                print(f"  [+] Secret '{k}' successfully set.")
            else:
                print(f"  [!] Failed to set '{k}': {res.stderr.strip()}")
                success = False
        except Exception as e:
            print(f"  [!] Error setting '{k}': {e}")
            success = False
    return success


def set_via_api(secrets, token):
    try:
        import httpx
        from nacl import encoding, public
    except ImportError:
        print("[*] Installing pynacl and httpx for direct API upload...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pynacl", "httpx"])
        import httpx
        from nacl import encoding, public

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    client = httpx.Client(headers=headers, timeout=15)

    # 1. Get repo public key
    pk_url = f"https://api.github.com/repos/{REPO}/actions/secrets/public-key"
    r = client.get(pk_url)
    if r.status_code != 200:
        print(f"[!] Failed to fetch repo public key (HTTP {r.status_code}): {r.text}")
        return False

    pk_data = r.json()
    key_id = pk_data["key_id"]
    public_key = public.PublicKey(pk_data["key"].encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)

    for k, v in secrets.items():
        encrypted = sealed_box.encrypt(v.encode("utf-8"))
        encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")

        put_url = f"https://api.github.com/repos/{REPO}/actions/secrets/{k}"
        res = client.put(put_url, json={"encrypted_value": encrypted_b64, "key_id": key_id})
        if res.status_code in (201, 204):
            print(f"  [+] Secret '{k}' successfully set via GitHub API.")
        else:
            print(f"  [!] Failed to set '{k}' (HTTP {res.status_code}): {res.text}")

    return True


def main():
    print("=" * 65)
    print("  BOLSAMAJH — GITHUB ACTIONS SECRETS CONFIGURATOR")
    print("=" * 65)

    secrets = load_secrets()
    if not secrets:
        print(f"[!] No active secrets found in '{SECRETS_FILE.name}'.")
        print("    Edit the file with your keys and re-run.")
        return 0

    print(f"[+] Loaded {len(secrets)} non-empty secret(s) from {SECRETS_FILE.name}:")
    for k in secrets.keys():
        print(f"    - {k}")

    # Check if gh CLI is available
    gh_path = shutil.which("gh")
    if gh_path:
        # Check gh auth status
        auth_res = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        if auth_res.returncode == 0:
            set_via_gh_cli(secrets)
            return 0

    # Check for GITHUB_TOKEN in env
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        set_via_api(secrets, token)
        return 0

    # Otherwise show interactive guidance
    print("\n" + "-" * 65)
    print("  HOW TO APPLY THESE SECRETS:")
    print("-" * 65)
    print("Option A (Fastest via GitHub CLI):")
    print("  1. Install GitHub CLI: winget install --id GitHub.cli")
    print("  2. Authenticate:      gh auth login")
    print("  3. Run this script:   python scripts/set_github_secrets.py\n")

    print("Option B (Directly in Browser):")
    print(f"  1. Go to: https://github.com/{REPO}/settings/secrets/actions")
    print("  2. Click 'New repository secret' for each key:\n")
    for k, v in secrets.items():
        masked = v[:4] + "..." + v[-4:] if len(v) > 10 else "***"
        print(f"     Name:  {k}")
        print(f"     Value: (from your github_secrets.env, value: {masked})\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

