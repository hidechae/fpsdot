from __future__ import annotations

import ctypes
import os
from ctypes import wintypes

try:
    import win32gui
    import win32process
    import psutil  # type: ignore
    _HAVE_WIN32 = True
except Exception:  # pragma: no cover
    _HAVE_WIN32 = False


# --- Win32 structures / constants for per-monitor DPI conversion ----------

class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


_MONITOR_DEFAULTTONEAREST = 2

_user32 = ctypes.WinDLL("user32", use_last_error=True) if os.name == "nt" else None


def _get_window_dpi(hwnd: int) -> int:
    """Return DPI for the monitor that `hwnd` is on. Falls back to 96."""
    if _user32 is None:
        return 96
    # GetDpiForWindow exists on Win10 1607+; older systems fall through.
    try:
        fn = _user32.GetDpiForWindow
        fn.restype = wintypes.UINT
        fn.argtypes = [wintypes.HWND]
        dpi = int(fn(hwnd))
        return dpi if dpi > 0 else 96
    except Exception:
        return 96


def _get_window_monitor_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    """Physical rect of the monitor that `hwnd` is on, in screen pixels."""
    if _user32 is None:
        return None
    try:
        hmon = _user32.MonitorFromWindow(wintypes.HWND(hwnd), _MONITOR_DEFAULTTONEAREST)
        mi = _MONITORINFO()
        mi.cbSize = ctypes.sizeof(mi)
        if not _user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            return None
        r = mi.rcMonitor
        return (r.left, r.top, r.right, r.bottom)
    except Exception:
        return None


def _find_qt_screen_for_monitor(mon_physical: tuple[int, int, int, int], scale: float):
    """Match a Win32 physical monitor rect to a QScreen by logical size + DPR."""
    from PySide6.QtGui import QGuiApplication

    target_w = int(round((mon_physical[2] - mon_physical[0]) / scale))
    target_h = int(round((mon_physical[3] - mon_physical[1]) / scale))
    best = None
    best_err = 10**9
    for scr in QGuiApplication.screens():
        g = scr.geometry()
        dpr_diff = abs(scr.devicePixelRatio() - scale)
        size_err = abs(g.width() - target_w) + abs(g.height() - target_h)
        err = size_err + int(dpr_diff * 100)
        if err < best_err:
            best_err = err
            best = scr
    return best or QGuiApplication.primaryScreen()


# --- Public API -----------------------------------------------------------

def foreground_process_name() -> str | None:
    if not _HAVE_WIN32:
        return None
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid <= 0:
            return None
        return psutil.Process(pid).name()
    except Exception:
        return None


def foreground_window_rect_logical() -> tuple[int, int, int, int] | None:
    """Foreground window rect in Qt LOGICAL coordinates (DPI-corrected).

    Returns (left, top, right, bottom) suitable to pass to QWidget.move().
    """
    if not _HAVE_WIN32:
        return None
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        if right <= left or bottom <= top:
            return None

        dpi = _get_window_dpi(hwnd)
        scale = dpi / 96.0 if dpi > 0 else 1.0

        # Convert by re-anchoring to the window's monitor: physical offsets
        # within the monitor / scale, then re-added on top of the matching
        # QScreen's LOGICAL origin. This is correct even for multi-monitor
        # setups where each display has a different scale factor.
        mon = _get_window_monitor_rect(hwnd)
        if mon is None:
            # Fall back to naive division (works for single-monitor).
            return (
                int(left / scale), int(top / scale),
                int(right / scale), int(bottom / scale),
            )

        qt_screen = _find_qt_screen_for_monitor(mon, scale)
        sg = qt_screen.geometry()

        def conv(px: int, py: int) -> tuple[int, int]:
            lx = sg.x() + (px - mon[0]) / scale
            ly = sg.y() + (py - mon[1]) / scale
            return (int(round(lx)), int(round(ly)))

        l, t = conv(left, top)
        r, b = conv(right, bottom)
        return (l, t, r, b)
    except Exception:
        return None


def is_target_focused(target_processes: list[str]) -> bool:
    name = foreground_process_name()
    if name is None:
        return True  # if we can't tell, behave permissively
    name_l = name.lower()
    return any(
        name_l == t.lower() or name_l == os.path.basename(t).lower()
        for t in target_processes
    )
