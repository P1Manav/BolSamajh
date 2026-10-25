"""Text insertion via clipboard — works in any app that accepts Ctrl+V."""

import time
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
        time.sleep(0.05)  # Small delay for clipboard to update

        # Simulate Ctrl+V
        _keyboard.press(Key.ctrl)
        _keyboard.press("v")
        _keyboard.release("v")
        _keyboard.release(Key.ctrl)

        time.sleep(0.1)  # Wait for paste to complete
        log.info("Inserted %d characters", len(text))

    finally:
        # Restore original clipboard after a brief delay
        time.sleep(0.2)
        try:
            pyperclip.copy(original)
        except Exception:
            pass


def get_selected_text() -> str:
    """Get currently selected text from any app by simulating Ctrl+C."""
    # Save current clipboard
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    try:
        # Simulate Ctrl+C
        _keyboard.press(Key.ctrl)
        _keyboard.press("c")
        _keyboard.release("c")
        _keyboard.release(Key.ctrl)

        time.sleep(0.15)  # Wait for copy

        selected = pyperclip.paste()

        # If clipboard didn't change, nothing was selected
        if selected == original:
            return ""
        return selected

    finally:
        # Restore original clipboard
        time.sleep(0.1)
        try:
            pyperclip.copy(original)
        except Exception:
            pass
