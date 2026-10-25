"""Overlay HUD — floating status indicator using tkinter.

Shows a small, always-on-top, semi-transparent pill that indicates:
  🎤 Listening  |  ⏳ Processing  |  ✅ Done  |  ❌ Error
"""

import logging
import threading
import tkinter as tk
from typing import Literal

log = logging.getLogger(__name__)

HUDState = Literal["idle", "listening", "processing", "done", "error"]

# State → (emoji, label, bg color, fg color)
_STATE_DISPLAY = {
    "idle":       ("",  "",           "#1a1a2e", "#8b8ba7"),
    "listening":  ("🎤", "Listening…", "#1a3a1a", "#4ade80"),
    "processing": ("⏳", "Processing…","#1a2a3a", "#60a5fa"),
    "done":       ("✅", "Done",       "#1a2a1a", "#4ade80"),
    "error":      ("❌", "Error",      "#3a1a1a", "#f87171"),
}

# How long to show "done" before auto-hiding (ms)
_DONE_TIMEOUT = 2000


class OverlayHUD:
    """Floating overlay HUD for BolSamajh status."""

    def __init__(self):
        self._root: tk.Tk | None = None
        self._label: tk.Label | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._state: HUDState = "idle"

    def start(self) -> None:
        """Start the overlay in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_tk, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=3.0)
        log.debug("Overlay HUD started")

    def _run_tk(self) -> None:
        """Tkinter mainloop (runs in dedicated thread)."""
        self._root = tk.Tk()
        self._root.title("BolSamajh")
        self._root.overrideredirect(True)        # No title bar
        self._root.attributes("-topmost", True)  # Always on top
        self._root.attributes("-alpha", 0.9)     # Slightly transparent

        # Position: bottom-center of screen
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        w, h = 220, 44
        x = (screen_w - w) // 2
        y = screen_h - h - 80  # 80px from bottom
        self._root.geometry(f"{w}x{h}+{x}+{y}")

        # Rounded-look frame
        self._root.configure(bg="#1a1a2e")
        self._label = tk.Label(
            self._root,
            text="",
            font=("Segoe UI", 13),
            bg="#1a1a2e",
            fg="#8b8ba7",
            padx=16,
            pady=6,
        )
        self._label.pack(fill=tk.BOTH, expand=True)

        # Start hidden
        self._root.withdraw()
        self._ready.set()
        self._root.mainloop()

    def set_state(self, state: HUDState, extra: str = "") -> None:
        """Update the HUD state (thread-safe)."""
        if not self._root or not self._label:
            return

        self._state = state
        emoji, label, bg, fg = _STATE_DISPLAY.get(state, _STATE_DISPLAY["idle"])

        display_text = f" {emoji} {label}" if label else ""
        if extra:
            display_text += f"  {extra}"

        def _update():
            try:
                self._label.configure(text=display_text, bg=bg, fg=fg)
                self._root.configure(bg=bg)
                if state == "idle":
                    self._root.withdraw()
                else:
                    self._root.deiconify()
                    self._root.lift()

                # Auto-hide after "done"
                if state == "done":
                    self._root.after(_DONE_TIMEOUT, lambda: self.set_state("idle"))
            except tk.TclError:
                pass  # Widget destroyed

        self._root.after(0, _update)

    def show_text(self, text: str, duration_ms: int = 2000) -> None:
        """Show a temporary text message."""
        if not self._root or not self._label:
            return

        def _show():
            try:
                self._label.configure(text=f"  {text}", bg="#1a2a3a", fg="#60a5fa")
                self._root.configure(bg="#1a2a3a")
                self._root.deiconify()
                self._root.lift()
                self._root.after(duration_ms, lambda: self.set_state("idle"))
            except tk.TclError:
                pass

        self._root.after(0, _show)

    def stop(self) -> None:
        """Stop the overlay."""
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
