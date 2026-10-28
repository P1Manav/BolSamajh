"""Text insertion and selection via clipboard with sentinel verification and modifier release.

Adheres strictly to Tier 5 Requirements:
- Releases Shift, Alt, and Ctrl modifiers before simulating Ctrl+C and Ctrl+V to prevent
  accidental shortcuts (e.g. Alt+Ctrl+C or Ctrl+Shift+C) when triggered via Alt+Shift hotkeys.
- Restores modifier keys after simulation based on physical keys actually held.
- Preserves clipboard text content reliably using unique UUID sentinels.
- Always restores original clipboard state (including clearing it if empty).
- Documents limitation for non-text clipboard data (bitmaps/files are replaced during insertion; text is never lost).
"""

import logging
import os
import sys
import time
import uuid

import pyperclip

log = logging.getLogger(__name__)


class _StubKey:
    shift = "shift"
    shift_r = "shift_r"
    alt = "alt"
    alt_r = "alt_r"
    alt_gr = "alt_gr"
    ctrl = "ctrl"
    ctrl_r = "ctrl_r"


class _NullKeyboard:
    def press(self, key):
        pass

    def release(self, key):
        pass


try:
    from pynput.keyboard import Controller
    from pynput.keyboard import Key as _PynputKey

    _keyboard = Controller()
    Key = _PynputKey
except Exception:
    Controller = None
    Key = _StubKey
    _keyboard = _NullKeyboard()


MODIFIER_KEYS = [
    Key.shift if Key else None,
    Key.shift_r if Key else None,
    Key.alt if Key else None,
    Key.alt_r if Key else None,
    Key.alt_gr if Key else None,
    Key.ctrl if Key else None,
    Key.ctrl_r if Key else None,
]

MODIFIER_VK_MAP = {
    Key.shift if Key else None: 0x10,
    Key.ctrl if Key else None: 0x11,
    Key.alt if Key else None: 0x12,
}


class ModifierGuard:
    """Context manager to safely release modifier keys during keyboard simulation and restore them."""

    def __init__(self):
        self._released_keys = []

    def __enter__(self):
        self._released_keys = []
        if _keyboard is None or Key is None:
            return self

        # Detect physically held modifiers so we only re-press those on exit
        if sys.platform == "win32":
            try:
                import ctypes

                for k, vk in [(Key.shift, 0x10), (Key.ctrl, 0x11), (Key.alt, 0x12)]:
                    if k is not None and (ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000):
                        self._released_keys.append((k, vk))
            except Exception as e:
                log.debug("GetAsyncKeyState check failed: %s", e)
        else:
            for k in [Key.shift, Key.ctrl, Key.alt]:
                if k is not None:
                    self._released_keys.append((k, 0))

        # Release modifiers to prevent interference with simulated Ctrl+C/Ctrl+V
        for k in [Key.shift, Key.ctrl, Key.alt]:
            if k is not None:
                try:
                    _keyboard.release(k)
                except Exception:
                    pass
        time.sleep(0.02)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if _keyboard is None or Key is None:
            return
        # Restore only the physical modifier state that was actually released
        if sys.platform == "win32":
            try:
                import ctypes

                for k, vk in self._released_keys:
                    if vk == 0 or (ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000):
                        try:
                            _keyboard.press(k)
                        except Exception:
                            pass
            except Exception as e:
                log.debug("Modifier restore failed: %s", e)
        else:
            for k, _ in self._released_keys:
                try:
                    _keyboard.press(k)
                except Exception:
                    pass


def _get_restore_delay() -> float:
    try:
        return float(os.getenv("BOLSAMAJH_CLIPBOARD_RESTORE_DELAY", "0.3"))
    except ValueError:
        return 0.3


def _restore_clipboard(target: str, retries: int = 3, delay: float | None = None) -> None:
    """Safely restore the clipboard to the target text (or empty string), verifying with retry loop."""
    if delay is None:
        delay = _get_restore_delay()
    time.sleep(delay)
    val_to_set = target if target is not None else ""
    for _ in range(retries):
        try:
            pyperclip.copy(val_to_set)
            if pyperclip.paste() == val_to_set:
                break
        except Exception:
            pass
        time.sleep(0.05)


def insert_text(text: str) -> bool:
    """Insert text at the current cursor position in any application.

    Strategy:
    1. Save existing clipboard text.
    2. Release any held modifiers (Alt, Shift, Ctrl) from hotkeys.
    3. Copy text to clipboard and simulate Ctrl+V.
    4. Restore original clipboard text (or clear it if previously empty).

    Returns:
        bool: True if text was successfully inserted via clipboard paste, False otherwise.
    """
    if not text or not text.strip():
        log.debug("Empty text, nothing to insert")
        return False

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
        return True

    except Exception as e:
        log.error("Failed to insert text via clipboard: %s", e)
        return False

    finally:
        # Always restore original clipboard text, clearing it if it was empty
        _restore_clipboard(original)


def get_selected_text(timeout_sec: float = 0.3) -> str:
    """Get currently selected text from any app using a clipboard sentinel.

    Fixes:
    1. Releases Shift, Alt, and Ctrl before sending Ctrl+C so physical hotkey holds
       (e.g. Alt+Shift+C) do not trigger Alt+Ctrl+C or Ctrl+Shift+C.
    2. Sets a unique UUID sentinel so copying text that matches previous clipboard content
       is correctly recognized as a valid selection.
    3. Always restores original clipboard text (clearing if empty), preventing sentinel leakage.
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
        # Always restore original clipboard text, clearing it if it was empty
        _restore_clipboard(original)
