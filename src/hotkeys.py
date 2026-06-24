"""Global hotkey registration using Win32 RegisterHotKey.

Runs a dedicated message loop thread that owns the hotkey registrations and
emits a Qt signal whenever a registered hotkey fires.
"""
from __future__ import annotations

import threading
import ctypes
from ctypes import wintypes
from typing import Callable

from PySide6.QtCore import QObject, Signal


MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

VK_MAP = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
    "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "SPACE": 0x20, "ESC": 0x1B, "ESCAPE": 0x1B, "TAB": 0x09,
    "INSERT": 0x2D, "DELETE": 0x2E, "HOME": 0x24, "END": 0x23,
    "PAGEUP": 0x21, "PAGEDOWN": 0x22,
}
for _i in range(26):
    VK_MAP[chr(ord("A") + _i)] = 0x41 + _i
for _i in range(10):
    VK_MAP[str(_i)] = 0x30 + _i


def parse_hotkey(spec: str) -> tuple[int, int] | None:
    """Parse 'Ctrl+Shift+X' style spec -> (modifiers, vk). None on failure."""
    if not spec:
        return None
    parts = [p.strip().upper() for p in spec.split("+") if p.strip()]
    if not parts:
        return None
    mods = 0
    key: str | None = None
    for p in parts:
        if p in ("CTRL", "CONTROL"):
            mods |= MOD_CONTROL
        elif p == "SHIFT":
            mods |= MOD_SHIFT
        elif p == "ALT":
            mods |= MOD_ALT
        elif p in ("WIN", "META", "SUPER"):
            mods |= MOD_WIN
        else:
            key = p
    if key is None or key not in VK_MAP:
        return None
    return (mods | MOD_NOREPEAT, VK_MAP[key])


class HotkeyManager(QObject):
    """Owns a hotkey thread; emits triggered(name) when a hotkey fires."""

    triggered = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._registered: dict[int, str] = {}  # id -> name
        self._spec_by_name: dict[str, str] = {}
        self._stop_evt = threading.Event()
        self._ready_evt = threading.Event()
        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    # ---------- public API ----------

    def set_bindings(self, bindings: dict[str, str]) -> None:
        """Replace the entire binding set. Restart needed via start()."""
        self._spec_by_name = dict(bindings)

    def register(self, name: str, spec: str) -> bool:
        self._spec_by_name[name] = spec
        if self._thread and self._thread.is_alive():
            # Restart thread to apply changes; cheapest correct approach.
            self.stop()
        return self.start()

    def start(self) -> bool:
        if self._thread and self._thread.is_alive():
            return True
        self._stop_evt.clear()
        self._ready_evt.clear()
        self._thread = threading.Thread(target=self._run, name="HotkeyThread", daemon=True)
        self._thread.start()
        self._ready_evt.wait(timeout=2.0)
        return True

    def stop(self) -> None:
        if self._thread_id is not None:
            self._user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread:
            self._thread.join(timeout=2.0)
        self._thread = None
        self._thread_id = None
        self._registered.clear()

    # ---------- thread body ----------

    def _run(self) -> None:
        self._thread_id = self._kernel32.GetCurrentThreadId()
        # Register all
        next_id = 1
        for name, spec in self._spec_by_name.items():
            parsed = parse_hotkey(spec)
            if parsed is None:
                continue
            mods, vk = parsed
            if self._user32.RegisterHotKey(None, next_id, mods, vk):
                self._registered[next_id] = name
                next_id += 1
        self._ready_evt.set()

        msg = wintypes.MSG()
        try:
            while True:
                res = self._user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if res == 0 or res == -1:
                    break
                if msg.message == WM_HOTKEY:
                    hotkey_id = int(msg.wParam)
                    name = self._registered.get(hotkey_id)
                    if name is not None:
                        self.triggered.emit(name)
                # Allow standard dispatch (not strictly necessary for hotkeys)
        finally:
            for hk_id in list(self._registered):
                self._user32.UnregisterHotKey(None, hk_id)
            self._registered.clear()
