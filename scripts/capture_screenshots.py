"""BolSamajh — Playwright Automated Screenshot & UI Verification Suite.

Captures responsive screenshots at 1440px (Desktop) and 375px (Mobile)
for all 9 primary application views and verifies zero console errors:
- Home (Dashboard)
- Dictate
- Documents (Talk to Document)
- Commands (Voice Actions)
- Web Call
- History
- Why BolSamajh
- Benchmark
- Settings
"""

import os
import sys
import time
import threading
from pathlib import Path

# Set UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from playwright.sync_api import sync_playwright
from bolsamajh.web.server import app

PORT = 8042
SERVER_URL = f"http://127.0.0.1:{PORT}"
SCREENS_DIR = ROOT_DIR / "docs" / "screens"
SCREENS_DIR.mkdir(parents=True, exist_ok=True)

TABS = [
    ("dashboard", "01_home_dashboard"),
    ("dictate", "02_dictate"),
    ("doc", "03_documents_rag"),
    ("actions", "04_voice_commands"),
    ("webcall", "05_web_call"),
    ("history", "06_history"),
    ("why", "07_why_bolsamajh"),
    ("benchmark", "08_benchmark"),
    ("settings", "09_settings"),
]


class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        config = uvicorn.Config(app=app, host="127.0.0.1", port=PORT, log_level="warning")
        self.server = uvicorn.Server(config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def wait_for_server():
    import urllib.request
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"{SERVER_URL}/healthz", timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    print(f"[*] Starting local server on port {PORT}...")
    server_thread = ServerThread()
    server_thread.start()

    if not wait_for_server():
        print("[!] Server failed to respond on /healthz in time.")
        sys.exit(1)

    print("[+] Server healthy at " + SERVER_URL)
    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for mode, width, height in [("desktop", 1440, 900), ("mobile", 375, 812)]:
            print(f"\n[*] Capturing {mode.upper()} viewports ({width}x{height})...")
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()

            def on_console(msg):
                if msg.type == "error":
                    # Ignore harmless media stream or favicon errors in test headless
                    text = msg.text
                    if "favicon" not in text.lower():
                        console_errors.append(f"[{mode} {msg.location}] {text}")

            page.on("console", on_console)

            # Navigate to base URL
            page.goto(SERVER_URL, wait_until="networkidle")
            page.wait_for_timeout(1000)

            for tab_id, filename_prefix in TABS:
                print(f"  -> Switching to tab '{tab_id}'...")
                # Click tab
                tab_btn = page.locator(f"button.nav-tab[data-tab='{tab_id}']")
                if tab_btn.count() > 0:
                    tab_btn.first.click()
                else:
                    # Mobile or fallback
                    page.evaluate(f"window.location.hash = '{tab_id}'")

                page.wait_for_timeout(600)

                screenshot_path = SCREENS_DIR / f"{filename_prefix}_{width}.png"
                page.screenshot(path=str(screenshot_path), full_page=False)
                print(f"     Saved {screenshot_path.name} ({os.path.getsize(screenshot_path):,} bytes)")

                # If home dashboard desktop, also save to assets/
                if tab_id == "dashboard" and width == 1440:
                    hero_path = ROOT_DIR / "assets" / "app_screenshot_desktop.png"
                    hero_path.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(hero_path), full_page=False)
                    print(f"     Saved primary hero capture -> assets/app_screenshot_desktop.png")

            context.close()

        browser.close()

    server_thread.stop()

    print("\n" + "=" * 60)
    print("  PLAYWRIGHT SCREENSHOT VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Screenshots captured in: {SCREENS_DIR}")
    print(f"Total screenshots: {len(list(SCREENS_DIR.glob('*.png')))}")
    print(f"Console errors: {len(console_errors)}")
    if console_errors:
        print("[!] Console errors encountered:")
        for err in console_errors:
            print(f"    - {err}")
    else:
        print("[OK] Zero browser console errors across all 9 views and both viewports!")

    return 0 if len(console_errors) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
