"""Unit tests for clipboard text insertion and selection with sentinel verification."""

from unittest.mock import patch

from bolsamajh.utils.clipboard import get_selected_text, insert_text


def test_get_selected_text_with_sentinel():
    """Test that get_selected_text distinguishes sentinel from actual selection."""
    clipboard_state = {"content": "pre-existing clipboard"}

    def mock_copy(text):
        clipboard_state["content"] = text

    def mock_paste():
        return clipboard_state["content"]

    with (
        patch("pyperclip.copy", side_effect=mock_copy),
        patch("pyperclip.paste", side_effect=mock_paste),
        patch("bolsamajh.utils.clipboard._keyboard") as mock_kb,
    ):
        # Scenario 1: Target app copies new text
        def on_press(key):
            if key == "c":
                clipboard_state["content"] = "Selected text from app"

        mock_kb.press.side_effect = on_press

        selected = get_selected_text(timeout_sec=0.1)
        assert selected == "Selected text from app"
        # Original clipboard restored
        assert clipboard_state["content"] == "pre-existing clipboard"


def test_get_selected_text_no_selection_sentinel_remains():
    """Test that if target app has no selection, sentinel matches and returns empty string."""
    clipboard_state = {"content": "initial clipboard text"}

    def mock_copy(text):
        clipboard_state["content"] = text

    def mock_paste():
        return clipboard_state["content"]

    with (
        patch("pyperclip.copy", side_effect=mock_copy),
        patch("pyperclip.paste", side_effect=mock_paste),
        patch("bolsamajh.utils.clipboard._keyboard"),
    ):
        # Target app does NOT modify clipboard upon Ctrl+C
        selected = get_selected_text(timeout_sec=0.05)
        assert selected == ""
        # Original clipboard restored
        assert clipboard_state["content"] == "initial clipboard text"


def test_insert_text_mocked():
    """Test insert_text writes to clipboard, simulates Ctrl+V, and restores original."""
    clipboard_state = {"content": "prior text"}

    def mock_copy(text):
        clipboard_state["content"] = text

    def mock_paste():
        return clipboard_state["content"]

    with (
        patch("pyperclip.copy", side_effect=mock_copy),
        patch("pyperclip.paste", side_effect=mock_paste),
        patch("bolsamajh.utils.clipboard._keyboard"),
    ):
        insert_text("New dictated Hinglish sentence")
        # Restores prior text
        assert clipboard_state["content"] == "prior text"


def test_insert_text_restores_empty_clipboard(monkeypatch):
    """Test insert_text clears the clipboard when original content was empty."""
    monkeypatch.setenv("BOLSAMAJH_CLIPBOARD_RESTORE_DELAY", "0.01")
    clipboard_state = {"content": ""}

    def mock_copy(text):
        clipboard_state["content"] = text

    def mock_paste():
        return clipboard_state["content"]

    with (
        patch("pyperclip.copy", side_effect=mock_copy),
        patch("pyperclip.paste", side_effect=mock_paste),
        patch("bolsamajh.utils.clipboard._keyboard"),
    ):
        insert_text("New text")
        # Must be cleared to empty string, not left with "New text"
        assert clipboard_state["content"] == ""


def test_get_selected_text_restores_empty_clipboard(monkeypatch):
    """Test get_selected_text clears sentinel even when clipboard was initially empty."""
    monkeypatch.setenv("BOLSAMAJH_CLIPBOARD_RESTORE_DELAY", "0.01")
    clipboard_state = {"content": ""}

    def mock_copy(text):
        clipboard_state["content"] = text

    def mock_paste():
        return clipboard_state["content"]

    with (
        patch("pyperclip.copy", side_effect=mock_copy),
        patch("pyperclip.paste", side_effect=mock_paste),
        patch("bolsamajh.utils.clipboard._keyboard"),
    ):
        selected = get_selected_text(timeout_sec=0.02)
        assert selected == ""
        # Must restore to empty string, not leave the sentinel
        assert clipboard_state["content"] == ""
