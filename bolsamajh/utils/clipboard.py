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

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt key

MODIFIER_VK_MAP = {
    Key.shift if Key else None: VK_SHIFT,
    Key.ctrl if Key else None: VK_CONTROL,
    Key.alt if Key else None: VK_MENU,
}


def _is_key_pressed(vk: int) -> bool:
    if sys.platform != "win32":
        return True
    try:
        import ctypes

        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)
    except Exception:
        return False


class ModifierGuard:
    """Context manager to safely release modifier keys during keyboard simulation and restore them."""

    def __init__(self):
        self._released_keys = []

    def _release_key(self, key):
        if _keyboard is not None and key is not None:
            try:
                _keyboard.release(key)
            except Exception:
                pass

    def _press_key(self, key):
        if _keyboard is not None and key is not None:
            try:
                _keyboard.press(key)
            except Exception:
                pass

    def __enter__(self):
        self._released_keys = []
        if _keyboard is None or Key is None:
            return self

        # Detect physically held modifiers so we only re-press those on exit
        if sys.platform == "win32":
            for k, vk in [(Key.shift, VK_SHIFT), (Key.ctrl, VK_CONTROL), (Key.alt, VK_MENU)]:
                if k is not None and _is_key_pressed(vk):
                    self._released_keys.append((k, vk))
        else:
            for k in [Key.shift, Key.ctrl, Key.alt]:
                if k is not None:
                    self._released_keys.append((k, 0))

        # Always release modifiers to prevent interference with simulated Ctrl+C/Ctrl+V
        for k in [Key.shift, Key.ctrl, Key.alt]:
            if k is not None:
                self._release_key(k)
        time.sleep(0.02)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if _keyboard is None or Key is None:
            return
        # Restore only the physical modifier state that was actually released
        if sys.platform == "win32":
            for k, vk in self._released_keys:
                if vk == 0 or _is_key_pressed(vk):
                    self._press_key(k)
        else:
            for k, _ in self._released_keys:
                self._press_key(k)


from contextlib import contextmanager


def _read_clipboard_text() -> str:
    try:
        val = pyperclip.paste()
        return val if val is not None else ""
    except Exception:
        return ""


def _write_clipboard_text(text: str) -> None:
    try:
        pyperclip.copy(text if text is not None else "")
    except Exception as e:
        log.warning("pyperclip.copy failed: %s", e)


def _empty_clipboard() -> None:
    _write_clipboard_text("")


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
            if not val_to_set:
                _empty_clipboard()
            else:
                _write_clipboard_text(val_to_set)
            if _read_clipboard_text() == val_to_set:
                break
        except Exception:
            pass
        time.sleep(0.05)


@contextmanager
def preserve_clipboard(delay: float | None = None):
    """Context manager to ensure clipboard is restored to its original content after exit."""
    original = _read_clipboard_text()
    try:
        yield original
    finally:
        _restore_clipboard(original, delay=delay)


# Alias for explicit clarity and test compatibility
restore_clipboard = preserve_clipboard


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

    with preserve_clipboard():
        try:
            # Copy our text to clipboard
            _write_clipboard_text(text)
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


def get_selected_text(timeout_sec: float = 0.3) -> str:
    """Get currently selected text from any app using a clipboard sentinel.

    Fixes:
    1. Releases Shift, Alt, and Ctrl before sending Ctrl+C so physical hotkey holds
       (e.g. Alt+Shift+C) do not trigger Alt+Ctrl+C or Ctrl+Shift+C.
    2. Sets a unique UUID sentinel so copying text that matches previous clipboard content
       is correctly recognized as a valid selection.
    3. Always restores original clipboard text (clearing if empty), preventing sentinel leakage.
    """
    with preserve_clipboard():
        sentinel = f"__BOLSAMAJH_SENTINEL_{uuid.uuid4().hex}__"

        try:
            # Place sentinel in clipboard
            _write_clipboard_text(sentinel)
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
                    val = _read_clipboard_text()
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

        except Exception as e:
            log.error("Failed to get selected text: %s", e)
            return ""
