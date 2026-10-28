"""Live verification script for Google AI Studio Gemini API models.

Loads .env, paginates model list via pageSize/nextPageToken, verifies that
the configured model is in the returned list (exiting non-zero if absent),
and executes one sample generateContent call.

Usage:
    python scripts/check_gemini.py
Or:
    python scripts/check_gemini.py --api-key "your-key" --model "gemini-3.5-flash"
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env from project root
_root = Path(__file__).resolve().parent.parent
_env_path = _root / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()


async def check_gemini(api_key: str, model: str) -> bool:
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    print("[*] Querying Google AI Studio models endpoint (with pagination)...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. List available models with pagination
        models = []
        page_token = None
        try:
            while True:
                params = {"pageSize": 1000}
                if page_token:
                    params["pageToken"] = page_token

                resp = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    headers=headers,
                    params=params,
                )
                if resp.status_code != 200:
                    print(f"[-] Models list failed (HTTP {resp.status_code}): {resp.text}")
                    return False

                data = resp.json()
                for m in data.get("models", []):
                    name = m.get("name", "").replace("models/", "")
                    if name:
                        models.append(name)

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

            print(f"[+] Successfully fetched {len(models)} live models from Google AI:")
            flash_models = [m for m in models if "flash" in m.lower()]
            for m in flash_models:
                print(f"    - {m}")

        except Exception as e:
            print(f"[-] Failed to fetch models list: {e}")
            return False

        # 2. Check if configured model name is in the list
        if model not in models:
            print(
                f"\n[-] ERROR: Configured model '{model}' was NOT found in the available Google AI models list!"
            )
            print(f"    Available Flash models: {flash_models}")
            return False
        else:
            print(f"\n[+] Verified: Configured model '{model}' is present in the live models list.")

        # 3. Test generateContent call
        print(f"[*] Testing generateContent call to model '{model}'...")
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Reply with 'OK: Gemini live check succeeded' and nothing else."}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 32,
                "temperature": 0.0,
            },
        }

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            gen_resp = await client.post(url, headers=headers, json=payload)
            if gen_resp.status_code == 200:
                gen_data = gen_resp.json()
                candidates = gen_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    reply = "".join(p.get("text", "") for p in parts)
                    print(f"[+] generateContent succeeded! Response:\n{reply.strip()}")
                    return True
                else:
                    print(f"[-] No candidate returned in response: {gen_data}")
                    return False
            else:
                print(f"[-] generateContent failed (HTTP {gen_resp.status_code}): {gen_resp.text}")
                return False
        except Exception as e:
            print(f"[-] Failed generateContent call: {e}")
            return False


def main() -> int:
    default_model = os.getenv(
        "BOLSAMAJH_GOOGLE_AI_MODEL", os.getenv("GOOGLE_AI_MODEL", "gemini-3.5-flash")
    )
    api_key_env = os.getenv("GOOGLE_AI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

    parser = argparse.ArgumentParser(description="Verify live Google AI Studio Gemini API access.")
    parser.add_argument("--api-key", default=api_key_env, help="Google AI Studio Gemini API Key")
    parser.add_argument(
        "--model",
        default=default_model,
        help=f"Gemini model to test (default from env: {default_model})",
    )
    args = parser.parse_args()

    api_key = args.api_key.strip()
    if not api_key:
        print("[!] No GOOGLE_AI_API_KEY or GEMINI_API_KEY found.")
        print("    Please set GOOGLE_AI_API_KEY in your .env or pass --api-key <KEY>.")
        print("    Example:")
        print("        python scripts/check_gemini.py --api-key AIzaSy...")
        return 1

    success = asyncio.run(check_gemini(api_key, args.model))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
