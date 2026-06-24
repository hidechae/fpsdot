from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path


CONFIG_DIR = Path.home() / ".fpsdot"
CONFIG_PATH = CONFIG_DIR / "config.json"


SHAPES = ("dot", "plus", "plus_dot", "circle", "circle_dot", "t_shape")


@dataclass
class CrosshairConfig:
    shape: str = "dot"
    size: int = 6                    # outer extent (px)
    thickness: int = 2               # line / dot thickness (px)
    gap: int = 4                     # center gap for plus / cross (px)
    color: str = "#00FF00"           # main color
    alpha: int = 230                 # 0..255
    outline: bool = True
    outline_color: str = "#000000"
    outline_thickness: int = 1

    def validate(self) -> None:
        if self.shape not in SHAPES:
            self.shape = "dot"
        self.size = max(1, min(self.size, 200))
        self.thickness = max(1, min(self.thickness, 30))
        self.gap = max(0, min(self.gap, 100))
        self.alpha = max(0, min(self.alpha, 255))
        self.outline_thickness = max(0, min(self.outline_thickness, 10))


@dataclass
class OverlayConfig:
    # which monitor (0 = primary). -1 = current focused window's monitor
    monitor_index: int = -1
    offset_x: int = 0
    offset_y: int = 0
    # only show overlay when one of these processes is foreground
    target_processes: list[str] = field(
        default_factory=lambda: [
            "FortniteClient-Win64-Shipping.exe",
            "r5apex.exe",         # Apex Legends
            "r5apex_dx12.exe",
        ]
    )
    # if empty, always show
    only_when_target_focused: bool = True
    visible: bool = True


@dataclass
class HotkeyConfig:
    toggle_overlay: str = "F8"
    open_settings: str = "Ctrl+Shift+X"


@dataclass
class AppConfig:
    crosshair: CrosshairConfig = field(default_factory=CrosshairConfig)
    overlay: OverlayConfig = field(default_factory=OverlayConfig)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)

    @classmethod
    def load(cls) -> "AppConfig":
        if not CONFIG_PATH.exists():
            return cls()
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        cfg = cls(
            crosshair=CrosshairConfig(**data.get("crosshair", {})),
            overlay=OverlayConfig(**data.get("overlay", {})),
            hotkeys=HotkeyConfig(**data.get("hotkeys", {})),
        )
        cfg.crosshair.validate()
        return cfg

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


PRESETS: dict[str, CrosshairConfig] = {
    "Pro Dot (green)": CrosshairConfig(
        shape="dot", size=4, thickness=4, color="#00FF00",
        outline=True, outline_color="#000000", outline_thickness=1,
    ),
    "Cyan Dot": CrosshairConfig(
        shape="dot", size=3, thickness=3, color="#00FFFF",
        outline=True, outline_color="#000000", outline_thickness=1,
    ),
    "Magenta Dot": CrosshairConfig(
        shape="dot", size=3, thickness=3, color="#FF00FF",
        outline=True, outline_color="#000000", outline_thickness=1,
    ),
    "Plus (CS:GO style)": CrosshairConfig(
        shape="plus", size=8, thickness=2, gap=3, color="#00FF00",
        outline=True, outline_color="#000000", outline_thickness=1,
    ),
    "Plus + Dot": CrosshairConfig(
        shape="plus_dot", size=10, thickness=2, gap=4, color="#00FF00",
        outline=True, outline_color="#000000", outline_thickness=1,
    ),
    "Circle + Dot": CrosshairConfig(
        shape="circle_dot", size=12, thickness=2, gap=0, color="#FFFFFF",
        outline=True, outline_color="#000000", outline_thickness=1,
    ),
    "T-shape": CrosshairConfig(
        shape="t_shape", size=8, thickness=2, gap=3, color="#00FF00",
        outline=True, outline_color="#000000", outline_thickness=1,
    ),
}
