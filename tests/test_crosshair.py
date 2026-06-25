from __future__ import annotations

import pytest

from config import CrosshairConfig, SHAPES
from crosshair import draw_crosshair, required_canvas_size


def _paint(cfg: CrosshairConfig, size: int = 80):
    """Render `cfg` into a fresh QImage of `size`x`size`. Returns the QImage."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QImage, QPainter

    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    try:
        draw_crosshair(painter, cfg, size // 2, size // 2)
    finally:
        painter.end()
    return img


def _count_painted(img) -> int:
    """Count non-transparent pixels in the image."""
    n = 0
    for x in range(img.width()):
        for y in range(img.height()):
            if img.pixelColor(x, y).alpha() > 0:
                n += 1
    return n


# ---------------- required_canvas_size --------------------------------

def test_required_canvas_size_has_floor():
    cfg = CrosshairConfig(size=1, thickness=1, outline=False)
    assert required_canvas_size(cfg) >= 16


def test_required_canvas_size_grows_with_size():
    a = required_canvas_size(CrosshairConfig(size=4, thickness=2))
    b = required_canvas_size(CrosshairConfig(size=40, thickness=2))
    assert b > a


def test_required_canvas_size_grows_with_outline():
    base = CrosshairConfig(size=8, thickness=2, outline=False)
    outlined = CrosshairConfig(size=8, thickness=2, outline=True, outline_thickness=4)
    assert required_canvas_size(outlined) >= required_canvas_size(base)


# ---------------- draw_crosshair --------------------------------------

@pytest.mark.parametrize("shape", list(SHAPES))
def test_every_shape_paints_something(qapp, shape):
    cfg = CrosshairConfig(
        shape=shape, size=10, thickness=2, gap=3,
        color="#00FF00", alpha=255,
        outline=True, outline_color="#000000", outline_thickness=1,
    )
    img = _paint(cfg)
    assert _count_painted(img) > 0, f"shape {shape!r} painted no pixels"


def test_dot_uses_configured_color(qapp):
    cfg = CrosshairConfig(
        shape="dot", size=10, thickness=10,
        color="#FF0000", alpha=255, outline=False,
    )
    img = _paint(cfg)
    c = img.pixelColor(40, 40)  # canvas center
    assert c.alpha() > 0
    assert c.red() > c.green()
    assert c.red() > c.blue()


def test_alpha_setting_is_respected(qapp):
    """A dot with alpha=128 should produce a center pixel with alpha around 128."""
    cfg = CrosshairConfig(
        shape="dot", size=10, thickness=10,
        color="#00FF00", alpha=128, outline=False,
    )
    img = _paint(cfg)
    c = img.pixelColor(40, 40)
    assert 80 < c.alpha() < 180  # generous range for antialiasing


def test_does_not_paint_outside_canvas(qapp):
    """No paint should land in the corners for a small crosshair."""
    cfg = CrosshairConfig(
        shape="dot", size=4, thickness=4,
        color="#00FF00", alpha=255, outline=False,
    )
    img = _paint(cfg, size=80)
    for x, y in [(0, 0), (79, 0), (0, 79), (79, 79)]:
        assert img.pixelColor(x, y).alpha() == 0


def test_circle_shape_has_hollow_center(qapp):
    """Bare circle (not circle+dot) should leave the center transparent."""
    cfg = CrosshairConfig(
        shape="circle", size=20, thickness=2, gap=0,
        color="#00FF00", alpha=255, outline=False,
    )
    img = _paint(cfg, size=80)
    assert img.pixelColor(40, 40).alpha() == 0
    # but somewhere along the ring there should be paint
    assert img.pixelColor(40 + 20, 40).alpha() > 0 or img.pixelColor(40, 40 + 20).alpha() > 0


def test_circle_dot_has_painted_center(qapp):
    cfg = CrosshairConfig(
        shape="circle_dot", size=20, thickness=4, gap=0,
        color="#00FF00", alpha=255, outline=False,
    )
    img = _paint(cfg, size=80)
    assert img.pixelColor(40, 40).alpha() > 0
