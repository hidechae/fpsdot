from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QPainter, QPixmap, QColor
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from config import AppConfig
from crosshair import draw_crosshair
from hotkeys import HotkeyManager
from overlay import OverlayWindow
from settings_window import SettingsWindow


def make_tray_icon(cfg: AppConfig) -> QIcon:
    """Render a tiny crosshair into a pixmap so the tray shows what's active."""
    px = QPixmap(32, 32)
    px.fill(Qt.transparent)
    p = QPainter(px)
    # background ring so it's visible on any taskbar theme
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setBrush(QColor(20, 20, 20, 180))
    p.setPen(Qt.NoPen)
    p.drawEllipse(0, 0, 32, 32)
    draw_crosshair(p, cfg.crosshair, 16, 16)
    p.end()
    return QIcon(px)


class App:
    def __init__(self) -> None:
        self.cfg = AppConfig.load()
        self.qapp = QApplication(sys.argv)
        self.qapp.setQuitOnLastWindowClosed(False)

        self.overlay = OverlayWindow(self.cfg)
        self.settings = SettingsWindow(self.cfg)
        self.settings.changed.connect(self._on_changed)

        self.tray = QSystemTrayIcon(make_tray_icon(self.cfg))
        self.tray.setToolTip("fpsdot — crosshair overlay")
        self._build_tray_menu()
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        # Hotkeys
        self.hk = HotkeyManager()
        self.hk.triggered.connect(self._on_hotkey)
        self._reload_hotkeys()

    def _build_tray_menu(self) -> None:
        # Keep menu + every QAction on self — Qt does NOT take Python-side
        # ownership and a local QAction will be garbage-collected before
        # the user ever opens the menu.
        self._tray_menu = QMenu()
        self.act_toggle = QAction("Hide overlay", self._tray_menu)
        self.act_toggle.triggered.connect(self._toggle_overlay)
        self.act_settings = QAction("Settings…", self._tray_menu)
        self.act_settings.triggered.connect(self._open_settings)
        self.act_quit = QAction("Quit", self._tray_menu)
        self.act_quit.triggered.connect(self._quit)
        self._tray_menu.addAction(self.act_toggle)
        self._tray_menu.addAction(self.act_settings)
        self._tray_menu.addSeparator()
        self._tray_menu.addAction(self.act_quit)
        self.tray.setContextMenu(self._tray_menu)
        self._update_toggle_label()

    def _update_toggle_label(self) -> None:
        self.act_toggle.setText(
            "Hide overlay" if self.cfg.overlay.visible else "Show overlay"
        )

    # ---------- events ----------

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self._open_settings()

    def _on_changed(self) -> None:
        self.cfg.save()
        self.overlay.reload_config()
        self.tray.setIcon(make_tray_icon(self.cfg))
        self._update_toggle_label()
        self._reload_hotkeys()

    def _on_hotkey(self, name: str) -> None:
        if name == "toggle_overlay":
            self._toggle_overlay()
        elif name == "open_settings":
            self._open_settings()

    def _toggle_overlay(self) -> None:
        self.cfg.overlay.visible = not self.cfg.overlay.visible
        self.cfg.save()
        self.overlay.reload_config()
        self._update_toggle_label()
        # Reflect in settings dialog if open
        try:
            self.settings._update_visibility_btn()
        except Exception:
            pass
        self.tray.showMessage(
            "fpsdot",
            "Overlay ON" if self.cfg.overlay.visible else "Overlay OFF",
            QSystemTrayIcon.Information, 1500,
        )

    def _open_settings(self) -> None:
        self.settings.show()
        self.settings.raise_()
        self.settings.activateWindow()

    def _quit(self) -> None:
        self.hk.stop()
        self.tray.hide()
        self.qapp.quit()

    # ---------- hotkeys ----------

    def _reload_hotkeys(self) -> None:
        self.hk.stop()
        self.hk.set_bindings({
            "toggle_overlay": self.cfg.hotkeys.toggle_overlay,
            "open_settings": self.cfg.hotkeys.open_settings,
        })
        self.hk.start()

    # ---------- run ----------

    def run(self) -> int:
        self.overlay.start()
        # If no tray support (rare), open settings so user has a way in
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QTimer.singleShot(200, self._open_settings)
        return self.qapp.exec()


def main() -> int:
    app = App()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
