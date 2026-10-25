"""Text insertion and selection via clipboard with sentinel verification.

Adheres to Tier 3 Requirement 19:
- Uses a unique sentinel string so 'selection equals previous clipboard' is never misread as no selection.
- Releases Shift modifier before simulating Ctrl+C so physical Shift hold doesn't convert Ctrl+C into Ctrl+Shift+C.
- Restores original clipboard content after operations.
"""

import time
import uuid
import logging
import pyperclip
from pynput.keyboard import Controller, Key

log = logging.getLogger(__name__)

_keyboard = Controller()


def insert_text(text: str) -> None:
    """Insert text at the current cursor position in any application.

    Strategy: save clipboard → copy text → paste → restore clipboard.
    """
    if not text or not text.strip():
        log.debug("Empty text, nothing to insert")
        return

    # Save current clipboard
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    try:
        # Copy our text to clipboard
        pyperclip.copy(text)
        time.sleep(0.04)

        # Simulate Ctrl+V
        _keyboard.press(Key.ctrl)
        _keyboard.press("v")
        _keyboard.release("v")
        _keyboard.release(Key.ctrl)

        time.sleep(0.08)  # Wait for paste to complete
        log.info("Inserted %d characters", len(text))

    finally:
        # Restore original clipboard after a brief delay
        time.sleep(0.15)
        try:
            pyperclip.copy(original)
        except Exception:
            pass


def get_selected_text(timeout_sec: float = 0.3) -> str:
    """Get currently selected text from any app using a clipboard sentinel.

    Fixes:
    1. Releases Shift before sending Ctrl+C so holding Shift does not trigger Ctrl+Shift+C.
    2. Sets a unique UUID sentinel so copying text that matches previous clipboard content
       is correctly recognized as a valid selection.
    """
    # Save original clipboard content
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    sentinel = f"__BOLSAMAJH_SENTINEL_{uuid.uuid4().hex}__"

    try:
        # Place sentinel in clipboard
        pyperclip.copy(sentinel)
        time.sleep(0.03)

        # Temporarily release Shift keys in case user is holding Shift in hotkey
        _keyboard.release(Key.shift)
        _keyboard.release(Key.shift_r)
        time.sleep(0.02)

        # Simulate Ctrl+C
        _keyboard.press(Key.ctrl)
        _keyboard.press("c")
        _keyboard.release("c")
        _keyboard.release(Key.ctrl)

        # Wait briefly for target application to process Ctrl+C
        t0 = time.time()
        selected = sentinel
        while time.time() - t0 < timeout_sec:
            time.sleep(0.04)
            try:
                val = pyperclip.paste()
                if val != sentinel:
                    selected = val
                    break
            except Exception:
                pass

        # If clipboard still contains sentinel, nothing was highlighted
        if selected == sentinel:
            log.debug("No text selected (clipboard retained sentinel)")
            return ""

        log.info("Captured selection (%d characters): %s", len(selected), selected[:40])
        return selected

    finally:
        # Restore original clipboard
        try:
            pyperclip.copy(original)
        except Exception:
            pass
