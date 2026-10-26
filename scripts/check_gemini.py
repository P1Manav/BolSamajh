"""Live verification script for Google AI Studio Gemini API models.

Checks live available models via list_available_models and executes one
sample generateContent call using the provided API key.

Usage:
    export GEMINI_API_KEY="your-key"
    python scripts/check_gemini.py

Or:
    python scripts/check_gemini.py --api-key "your-key"
"""

import sys
import os
import argparse
import asyncio
import httpx


async def check_gemini(api_key: str, model: str = "gemini-3.5-flash") -> bool:
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    print(f"[*] Querying Google AI Studio models endpoint...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. List available models
        try:
            resp = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name", "").replace("models/", "") for m in data.get("models", [])]
                print(f"[+] Successfully fetched {len(models)} live models from Google AI:")
                flash_models = [m for m in models if "flash" in m.lower()]
                for m in flash_models:
                    print(f"    - {m}")
            else:
                print(f"[-] Models list failed (HTTP {resp.status_code}): {resp.text}")
                return False
        except Exception as e:
            print(f"[-] Failed to fetch models list: {e}")
            return False

        # 2. Test generateContent call
        print(f"\n[*] Testing generateContent call to model '{model}'...")
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
    parser = argparse.ArgumentParser(description="Verify live Google AI Studio Gemini API access.")
    parser.add_argument("--api-key", default=os.getenv("GEMINI_API_KEY", ""), help="Google AI Studio Gemini API Key")
    parser.add_argument("--model", default="gemini-3.5-flash", help="Gemini model to test (default: gemini-3.5-flash)")
    args = parser.parse_args()

    api_key = args.api_key.strip()
    if not api_key:
        print("[!] No GEMINI_API_KEY found.")
        print("    Please set GEMINI_API_KEY in your environment or pass --api-key <KEY>.")
        print("    Example:")
        print("        python scripts/check_gemini.py --api-key AIzaSy...")
        return 1

    success = asyncio.run(check_gemini(api_key, args.model))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
