from __future__ import annotations

import ctypes
from ctypes import wintypes

from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtGui import QPainter, QPaintEvent, QGuiApplication
from PySide6.QtWidgets import QWidget

from config import AppConfig
from crosshair import draw_crosshair, required_canvas_size
from window_focus import is_target_focused, foreground_window_rect_logical


# Win32 extended window styles to enforce click-through + transparency
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008


def _apply_click_through(hwnd: int) -> None:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    GetWindowLongPtr = user32.GetWindowLongPtrW
    SetWindowLongPtr = user32.SetWindowLongPtrW
    GetWindowLongPtr.restype = ctypes.c_ssize_t
    GetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int]
    SetWindowLongPtr.restype = ctypes.c_ssize_t
    SetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]

    ex = GetWindowLongPtr(hwnd, GWL_EXSTYLE)
    ex |= WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TOPMOST
    SetWindowLongPtr(hwnd, GWL_EXSTYLE, ex)


class OverlayWindow(QWidget):
    """Transparent, click-through, always-on-top crosshair overlay."""

    def __init__(self, cfg: AppConfig) -> None:
        super().__init__(
            None,
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput,
        )
        self.cfg = cfg
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setWindowTitle("fpsdot overlay")

        self._user_visible = True

        # Re-evaluate position / visibility frequently (cheap)
        self._timer = QTimer(self)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._tick)

        self._resize_to_crosshair()

    # ---------- lifecycle ----------

    def start(self) -> None:
        self.show()
        # Apply click-through AFTER native window exists
        hwnd = int(self.winId())
        _apply_click_through(hwnd)
        self._tick()
        self._timer.start()

    def set_user_visible(self, visible: bool) -> None:
        self._user_visible = visible
        self._tick()

    def is_user_visible(self) -> bool:
        return self._user_visible

    def reload_config(self) -> None:
        self._resize_to_crosshair()
        self._tick()
        self.update()

    # ---------- positioning ----------

    def _target_center(self) -> QPoint:
        ov = self.cfg.overlay
        # Try focused-window center first (more reliable for windowed/fullscreen-windowed games)
        if ov.monitor_index < 0:
            rect = foreground_window_rect_logical()
            if rect is not None:
                left, top, right, bottom = rect
                if right > left and bottom > top:
                    cx = (left + right) // 2 + ov.offset_x
                    cy = (top + bottom) // 2 + ov.offset_y
                    return QPoint(cx, cy)

        # Fall back to chosen monitor (or primary)
        screens = QGuiApplication.screens()
        if not screens:
            return QPoint(0, 0)
        idx = ov.monitor_index if 0 <= ov.monitor_index < len(screens) else 0
        geom = screens[idx].geometry()
        return QPoint(
            geom.x() + geom.width() // 2 + ov.offset_x,
            geom.y() + geom.height() // 2 + ov.offset_y,
        )

    def _resize_to_crosshair(self) -> None:
        side = required_canvas_size(self.cfg.crosshair)
        self.resize(side, side)

    def _reposition(self) -> None:
        center = self._target_center()
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)

    # ---------- visibility tick ----------

    def _should_show(self) -> bool:
        if not self._user_visible:
            return False
        if not self.cfg.overlay.visible:
            return False
        if self.cfg.overlay.only_when_target_focused:
            return is_target_focused(self.cfg.overlay.target_processes)
        return True

    def _tick(self) -> None:
        should = self._should_show()
        if should:
            self._reposition()
            if not self.isVisible():
                self.show()
                _apply_click_through(int(self.winId()))
        else:
            if self.isVisible():
                self.hide()

    # ---------- painting ----------

    def paintEvent(self, _: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        cx = self.width() // 2
        cy = self.height() // 2
        draw_crosshair(painter, self.cfg.crosshair, cx, cy)
