from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QSlider, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from config import AppConfig, CrosshairConfig, PRESETS, SHAPES
from crosshair import draw_crosshair, required_canvas_size


SHAPE_LABELS = {
    "dot": "Dot",
    "plus": "Plus (+)",
    "plus_dot": "Plus + center dot",
    "circle": "Circle (○)",
    "circle_dot": "Circle + dot (◎)",
    "t_shape": "T-shape",
}


class PreviewWidget(QWidget):
    def __init__(self, cfg: CrosshairConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.setMinimumSize(QSize(240, 200))
        self.setAutoFillBackground(False)

    def sizeHint(self) -> QSize:
        return QSize(240, 200)

    def paintEvent(self, _):
        p = QPainter(self)
        # neutral game-screen-ish background to judge contrast
        p.fillRect(self.rect(), QColor("#1f2933"))
        # subtle crosshair-position marker so user sees where center is
        p.setPen(QColor(255, 255, 255, 30))
        p.drawLine(0, self.height() // 2, self.width(), self.height() // 2)
        p.drawLine(self.width() // 2, 0, self.width() // 2, self.height())
        draw_crosshair(p, self.cfg, self.width() // 2, self.height() // 2)


class ColorButton(QPushButton):
    changed = Signal(str)

    def __init__(self, initial_hex: str) -> None:
        super().__init__()
        self._hex = initial_hex
        self.setFixedWidth(80)
        self._refresh()
        self.clicked.connect(self._pick)

    def hex(self) -> str:
        return self._hex

    def set_hex(self, value: str) -> None:
        c = QColor(value)
        if c.isValid():
            self._hex = c.name().upper()
            self._refresh()

    def _pick(self) -> None:
        col = QColorDialog.getColor(QColor(self._hex), self, "Pick color")
        if col.isValid():
            self._hex = col.name().upper()
            self._refresh()
            self.changed.emit(self._hex)

    def _refresh(self) -> None:
        self.setStyleSheet(
            f"QPushButton {{ background: {self._hex}; border: 1px solid #888; }}"
        )
        self.setText(self._hex)


class SettingsWindow(QDialog):
    """Live-editing settings dialog. Emits `changed` whenever config mutates."""

    changed = Signal()

    def __init__(self, cfg: AppConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle("fpsdot — Settings")
        self.setMinimumWidth(560)
        self._build_ui()
        self._load_from_cfg()
        self._wire()

    # ---------- UI construction ----------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        top = QHBoxLayout()
        root.addLayout(top, 1)

        # ---- Left: tabs ----
        self.tabs = QTabWidget()
        top.addWidget(self.tabs, 3)

        self._build_crosshair_tab()
        self._build_overlay_tab()
        self._build_hotkeys_tab()
        self._build_presets_tab()

        # ---- Right: preview ----
        preview_box = QGroupBox("Preview")
        v = QVBoxLayout(preview_box)
        self.preview = PreviewWidget(self.cfg.crosshair)
        v.addWidget(self.preview)
        top.addWidget(preview_box, 2)

        # ---- Bottom buttons ----
        btns = QHBoxLayout()
        root.addLayout(btns)
        self.btn_visible = QPushButton("Hide overlay")
        self.btn_close = QPushButton("Close")
        btns.addStretch(1)
        btns.addWidget(self.btn_visible)
        btns.addWidget(self.btn_close)

    def _build_crosshair_tab(self) -> None:
        w = QWidget()
        f = QFormLayout(w)

        self.cmb_shape = QComboBox()
        for s in SHAPES:
            self.cmb_shape.addItem(SHAPE_LABELS.get(s, s), s)

        self.spin_size = QSpinBox(); self.spin_size.setRange(1, 200)
        self.spin_thick = QSpinBox(); self.spin_thick.setRange(1, 30)
        self.spin_gap = QSpinBox(); self.spin_gap.setRange(0, 100)
        self.btn_color = ColorButton("#00FF00")
        self.sld_alpha = QSlider(Qt.Horizontal); self.sld_alpha.setRange(0, 255)
        self.lbl_alpha = QLabel("230")
        alpha_row = QHBoxLayout(); alpha_row.addWidget(self.sld_alpha, 1); alpha_row.addWidget(self.lbl_alpha)
        alpha_w = QWidget(); alpha_w.setLayout(alpha_row)

        self.chk_outline = QCheckBox("Enable outline (visibility)")
        self.btn_outline_color = ColorButton("#000000")
        self.spin_outline_thick = QSpinBox(); self.spin_outline_thick.setRange(0, 10)

        f.addRow("Shape", self.cmb_shape)
        f.addRow("Size (px)", self.spin_size)
        f.addRow("Thickness (px)", self.spin_thick)
        f.addRow("Center gap (px)", self.spin_gap)
        f.addRow("Color", self.btn_color)
        f.addRow("Opacity", alpha_w)
        f.addRow(self.chk_outline)
        f.addRow("Outline color", self.btn_outline_color)
        f.addRow("Outline thickness", self.spin_outline_thick)

        self.tabs.addTab(w, "Crosshair")

    def _build_overlay_tab(self) -> None:
        w = QWidget()
        f = QFormLayout(w)

        self.cmb_monitor = QComboBox()
        self.cmb_monitor.addItem("Auto (focused window)", -1)
        for i, scr in enumerate(QGuiApplication.screens()):
            g = scr.geometry()
            self.cmb_monitor.addItem(
                f"#{i}: {scr.name()} {g.width()}x{g.height()}", i,
            )

        self.spin_off_x = QSpinBox(); self.spin_off_x.setRange(-9999, 9999)
        self.spin_off_y = QSpinBox(); self.spin_off_y.setRange(-9999, 9999)

        self.chk_only_target = QCheckBox("Show only when target game is focused")

        self.list_targets = QListWidget()
        self.list_targets.setSelectionMode(self.list_targets.SelectionMode.SingleSelection)
        target_btns = QHBoxLayout()
        self.btn_target_add = QPushButton("Add…")
        self.btn_target_remove = QPushButton("Remove")
        self.edit_new_target = QLineEdit()
        self.edit_new_target.setPlaceholderText("e.g. FortniteClient-Win64-Shipping.exe")
        target_btns.addWidget(self.edit_new_target, 1)
        target_btns.addWidget(self.btn_target_add)
        target_btns.addWidget(self.btn_target_remove)
        targets_box = QVBoxLayout()
        targets_box.addWidget(self.list_targets)
        targets_box.addLayout(target_btns)
        targets_w = QWidget(); targets_w.setLayout(targets_box)

        f.addRow("Monitor", self.cmb_monitor)
        f.addRow("Offset X (px)", self.spin_off_x)
        f.addRow("Offset Y (px)", self.spin_off_y)
        f.addRow(self.chk_only_target)
        f.addRow("Target processes", targets_w)

        self.tabs.addTab(w, "Overlay")

    def _build_hotkeys_tab(self) -> None:
        w = QWidget()
        f = QFormLayout(w)
        self.edit_hk_toggle = QLineEdit()
        self.edit_hk_settings = QLineEdit()
        f.addRow(QLabel("Format: Ctrl+Shift+X, F8, Alt+F1 …"))
        f.addRow("Toggle overlay", self.edit_hk_toggle)
        f.addRow("Open settings", self.edit_hk_settings)
        self.lbl_hotkey_note = QLabel("Changes apply after pressing Apply hotkeys.")
        self.btn_apply_hotkeys = QPushButton("Apply hotkeys")
        f.addRow(self.lbl_hotkey_note)
        f.addRow(self.btn_apply_hotkeys)
        self.tabs.addTab(w, "Hotkeys")

    def _build_presets_tab(self) -> None:
        w = QWidget()
        v = QVBoxLayout(w)
        self.list_presets = QListWidget()
        for name in PRESETS:
            self.list_presets.addItem(QListWidgetItem(name))
        self.btn_apply_preset = QPushButton("Apply selected preset")
        v.addWidget(QLabel("Built-in presets:"))
        v.addWidget(self.list_presets, 1)
        v.addWidget(self.btn_apply_preset)
        self.tabs.addTab(w, "Presets")

    # ---------- bind config -> UI ----------

    def _load_from_cfg(self) -> None:
        c = self.cfg.crosshair
        i = self.cmb_shape.findData(c.shape)
        self.cmb_shape.setCurrentIndex(i if i >= 0 else 0)
        self.spin_size.setValue(c.size)
        self.spin_thick.setValue(c.thickness)
        self.spin_gap.setValue(c.gap)
        self.btn_color.set_hex(c.color)
        self.sld_alpha.setValue(c.alpha)
        self.lbl_alpha.setText(str(c.alpha))
        self.chk_outline.setChecked(c.outline)
        self.btn_outline_color.set_hex(c.outline_color)
        self.spin_outline_thick.setValue(c.outline_thickness)

        o = self.cfg.overlay
        i = self.cmb_monitor.findData(o.monitor_index)
        self.cmb_monitor.setCurrentIndex(i if i >= 0 else 0)
        self.spin_off_x.setValue(o.offset_x)
        self.spin_off_y.setValue(o.offset_y)
        self.chk_only_target.setChecked(o.only_when_target_focused)
        self.list_targets.clear()
        for t in o.target_processes:
            self.list_targets.addItem(t)

        self.edit_hk_toggle.setText(self.cfg.hotkeys.toggle_overlay)
        self.edit_hk_settings.setText(self.cfg.hotkeys.open_settings)

        self._update_visibility_btn()

    # ---------- bind UI -> config ----------

    def _wire(self) -> None:
        c = self.cfg.crosshair

        def push():
            c.shape = self.cmb_shape.currentData()
            c.size = self.spin_size.value()
            c.thickness = self.spin_thick.value()
            c.gap = self.spin_gap.value()
            c.color = self.btn_color.hex()
            c.alpha = self.sld_alpha.value()
            self.lbl_alpha.setText(str(c.alpha))
            c.outline = self.chk_outline.isChecked()
            c.outline_color = self.btn_outline_color.hex()
            c.outline_thickness = self.spin_outline_thick.value()
            c.validate()
            self.preview.update()
            self.changed.emit()

        self.cmb_shape.currentIndexChanged.connect(push)
        self.spin_size.valueChanged.connect(push)
        self.spin_thick.valueChanged.connect(push)
        self.spin_gap.valueChanged.connect(push)
        self.btn_color.changed.connect(lambda _hex: push())
        self.sld_alpha.valueChanged.connect(push)
        self.chk_outline.toggled.connect(push)
        self.btn_outline_color.changed.connect(lambda _hex: push())
        self.spin_outline_thick.valueChanged.connect(push)

        # overlay tab
        def push_ov():
            o = self.cfg.overlay
            o.monitor_index = int(self.cmb_monitor.currentData())
            o.offset_x = self.spin_off_x.value()
            o.offset_y = self.spin_off_y.value()
            o.only_when_target_focused = self.chk_only_target.isChecked()
            o.target_processes = [
                self.list_targets.item(i).text()
                for i in range(self.list_targets.count())
            ]
            self.changed.emit()

        self.cmb_monitor.currentIndexChanged.connect(push_ov)
        self.spin_off_x.valueChanged.connect(push_ov)
        self.spin_off_y.valueChanged.connect(push_ov)
        self.chk_only_target.toggled.connect(push_ov)

        def add_target():
            t = self.edit_new_target.text().strip()
            if not t:
                return
            self.list_targets.addItem(t)
            self.edit_new_target.clear()
            push_ov()

        def remove_target():
            for it in self.list_targets.selectedItems():
                self.list_targets.takeItem(self.list_targets.row(it))
            push_ov()

        self.btn_target_add.clicked.connect(add_target)
        self.edit_new_target.returnPressed.connect(add_target)
        self.btn_target_remove.clicked.connect(remove_target)

        # presets
        def apply_preset():
            it = self.list_presets.currentItem()
            if it is None:
                return
            preset = PRESETS[it.text()]
            self.cfg.crosshair = CrosshairConfig(**preset.__dict__)
            self.preview.cfg = self.cfg.crosshair
            self._load_from_cfg()
            self.changed.emit()

        self.list_presets.itemDoubleClicked.connect(lambda _: apply_preset())
        self.btn_apply_preset.clicked.connect(apply_preset)

        # hotkeys (Apply triggers re-registration via main)
        self.btn_apply_hotkeys.clicked.connect(self._apply_hotkeys)

        # bottom
        self.btn_visible.clicked.connect(self._toggle_visible)
        self.btn_close.clicked.connect(self.hide)

    # ---------- actions ----------

    def _apply_hotkeys(self) -> None:
        self.cfg.hotkeys.toggle_overlay = self.edit_hk_toggle.text().strip()
        self.cfg.hotkeys.open_settings = self.edit_hk_settings.text().strip()
        self.changed.emit()

    def _toggle_visible(self) -> None:
        self.cfg.overlay.visible = not self.cfg.overlay.visible
        self._update_visibility_btn()
        self.changed.emit()

    def _update_visibility_btn(self) -> None:
        self.btn_visible.setText(
            "Hide overlay" if self.cfg.overlay.visible else "Show overlay"
        )
