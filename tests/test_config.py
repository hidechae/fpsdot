from __future__ import annotations

import config
from config import AppConfig, CrosshairConfig, PRESETS, SHAPES


def test_default_app_config_is_valid():
    cfg = AppConfig()
    assert cfg.crosshair.shape in SHAPES
    assert cfg.crosshair.size > 0
    assert 0 <= cfg.crosshair.alpha <= 255
    assert cfg.overlay.monitor_index == -1  # auto = focused window
    assert "FortniteClient-Win64-Shipping.exe" in cfg.overlay.target_processes
    assert cfg.overlay.only_when_target_focused is True
    assert cfg.overlay.visible is True
    assert cfg.hotkeys.toggle_overlay
    assert cfg.hotkeys.open_settings


def test_crosshair_validate_clamps_out_of_range_values():
    c = CrosshairConfig(
        shape="not_a_shape",
        size=999,
        thickness=999,
        gap=-5,
        alpha=300,
        outline_thickness=20,
    )
    c.validate()
    assert c.shape == "dot"  # falls back to default
    assert c.size == 200
    assert c.thickness == 30
    assert c.gap == 0
    assert c.alpha == 255
    assert c.outline_thickness == 10


def test_crosshair_validate_preserves_in_range_values():
    c = CrosshairConfig(shape="plus", size=8, thickness=2, gap=3, alpha=180, outline_thickness=1)
    c.validate()
    assert c.shape == "plus"
    assert c.size == 8
    assert c.thickness == 2
    assert c.gap == 3
    assert c.alpha == 180
    assert c.outline_thickness == 1


def test_save_then_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")

    cfg = AppConfig()
    cfg.crosshair.color = "#FF00FF"
    cfg.crosshair.size = 10
    cfg.crosshair.shape = "plus_dot"
    cfg.overlay.target_processes = ["foo.exe", "bar.exe"]
    cfg.overlay.offset_x = 7
    cfg.hotkeys.toggle_overlay = "F12"
    cfg.save()

    loaded = AppConfig.load()
    assert loaded.crosshair.color == "#FF00FF"
    assert loaded.crosshair.size == 10
    assert loaded.crosshair.shape == "plus_dot"
    assert loaded.overlay.target_processes == ["foo.exe", "bar.exe"]
    assert loaded.overlay.offset_x == 7
    assert loaded.hotkeys.toggle_overlay == "F12"


def test_load_when_file_missing_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "does_not_exist.json")
    cfg = AppConfig.load()
    assert isinstance(cfg, AppConfig)
    assert cfg.crosshair.shape == "dot"


def test_load_when_file_corrupt_returns_defaults(tmp_path, monkeypatch):
    p = tmp_path / "config.json"
    p.write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", p)
    cfg = AppConfig.load()
    assert cfg.crosshair.shape == "dot"


def test_all_presets_are_valid():
    assert len(PRESETS) > 0
    for name, preset in PRESETS.items():
        preset.validate()
        assert preset.shape in SHAPES, f"{name} has invalid shape {preset.shape}"
        assert preset.size > 0
        assert 0 <= preset.alpha <= 255
        assert preset.color.startswith("#")


def test_save_creates_parent_directory(tmp_path, monkeypatch):
    nested = tmp_path / "deeply" / "nested"
    monkeypatch.setattr(config, "CONFIG_DIR", nested)
    monkeypatch.setattr(config, "CONFIG_PATH", nested / "config.json")
    cfg = AppConfig()
    cfg.save()
    assert (nested / "config.json").exists()
