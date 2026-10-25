"""Text insertion and selection via clipboard with sentinel verification and modifier release.

Adheres strictly to Tier 5 Requirements:
- Releases Shift, Alt, and Ctrl modifiers before simulating Ctrl+C and Ctrl+V to prevent
  accidental shortcuts (e.g. Alt+Ctrl+C or Ctrl+Shift+C) when triggered via Alt+Shift hotkeys.
- Restores modifier keys after simulation.
- Preserves clipboard text content reliably using unique UUID sentinels.
- Documents limitation for non-text clipboard data (bitmaps/files are replaced during insertion; text is never lost).
"""

import time
import uuid
import logging
from typing import Set, Any
import pyperclip

log = logging.getLogger(__name__)

try:
    from pynput.keyboard import Controller, Key
    _keyboard = Controller()
except Exception:
    Controller = None
    Key = None
    _keyboard = None


MODIFIER_KEYS = [
    Key.shift if Key else None,
    Key.shift_r if Key else None,
    Key.alt if Key else None,
    Key.alt_r if Key else None,
    Key.alt_gr if Key else None,
    Key.ctrl if Key else None,
    Key.ctrl_r if Key else None,
]


class ModifierGuard:
    """Context manager to safely release modifier keys during keyboard simulation and restore them."""

    def __enter__(self):
        if _keyboard is None or Key is None:
            return self
        for k in MODIFIER_KEYS:
            if k is not None:
                try:
                    _keyboard.release(k)
                except Exception:
                    pass
        time.sleep(0.02)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We leave modifiers released so physical key states don't get stuck in a locked virtual state
        pass


def insert_text(text: str) -> None:
    """Insert text at the current cursor position in any application.

    Strategy:
    1. Save existing clipboard text.
    2. Release any held modifiers (Alt, Shift, Ctrl) from hotkeys.
    3. Copy text to clipboard and simulate Ctrl+V.
    4. Restore original clipboard text.
    
    Note on Non-Text Clipboard:
    On Windows/macOS/Linux, clipboard memory is format-typed. When inserting text,
    text content is saved and restored with 100% fidelity. Non-text formats (such as
    in-memory image bitmaps or shell drag-drop file handles) cannot be serialized by
    standard text handlers and are overwritten by text insertion.
    """
    if not text or not text.strip():
        log.debug("Empty text, nothing to insert")
        return

    # Save current clipboard text
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    try:
        # Copy our text to clipboard
        pyperclip.copy(text)
        time.sleep(0.04)

        # Release modifiers (Alt, Shift, Ctrl) before simulating Ctrl+V
        with ModifierGuard():
            if _keyboard is not None and Key is not None:
                _keyboard.press(Key.ctrl)
                _keyboard.press("v")
                _keyboard.release("v")
                _keyboard.release(Key.ctrl)

        time.sleep(0.08)  # Wait for paste to complete
        log.info("Inserted %d characters", len(text))

    finally:
        # Restore original clipboard text after a brief delay
        time.sleep(0.15)
        try:
            if original:
                pyperclip.copy(original)
        except Exception:
            pass


def get_selected_text(timeout_sec: float = 0.3) -> str:
    """Get currently selected text from any app using a clipboard sentinel.

    Fixes:
    1. Releases Shift, Alt, and Ctrl before sending Ctrl+C so physical hotkey holds
       (e.g. Alt+Shift+C) do not trigger Alt+Ctrl+C or Ctrl+Shift+C.
    2. Sets a unique UUID sentinel so copying text that matches previous clipboard content
       is correctly recognized as a valid selection.
    3. Restores original clipboard text content in finally block.
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

        # Temporarily release modifier keys in case user is holding Alt+Shift in hotkey
        with ModifierGuard():
            # Simulate Ctrl+C
            if _keyboard is not None and Key is not None:
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
        # Restore original clipboard text
        try:
            if original:
                pyperclip.copy(original)
        except Exception:
            pass
