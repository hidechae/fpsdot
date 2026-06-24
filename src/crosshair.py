from __future__ import annotations

from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QBrush, QColor

from config import CrosshairConfig


def required_canvas_size(cfg: CrosshairConfig) -> int:
    """Side length of the square canvas the crosshair will be drawn into."""
    outline = cfg.outline_thickness if cfg.outline else 0
    extent = max(cfg.size, cfg.thickness) + outline + 4
    return max(16, extent * 2 + 2)


def _make_color(hex_str: str, alpha: int) -> QColor:
    c = QColor(hex_str)
    if not c.isValid():
        c = QColor("#FFFFFF")
    c.setAlpha(alpha)
    return c


def draw_crosshair(painter: QPainter, cfg: CrosshairConfig, cx: int, cy: int) -> None:
    """Render the crosshair centered at (cx, cy) on the given painter."""
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    main = _make_color(cfg.color, cfg.alpha)
    outline_color = _make_color(cfg.outline_color, cfg.alpha)
    use_outline = cfg.outline and cfg.outline_thickness > 0

    shape = cfg.shape

    def stroked(draw_fn) -> None:
        # outline first (slightly thicker), then main on top
        if use_outline:
            pen_w = cfg.thickness + cfg.outline_thickness * 2
            painter.setPen(QPen(outline_color, pen_w, Qt.SolidLine, Qt.FlatCap))
            painter.setBrush(Qt.NoBrush)
            draw_fn()
        painter.setPen(QPen(main, cfg.thickness, Qt.SolidLine, Qt.FlatCap))
        painter.setBrush(Qt.NoBrush)
        draw_fn()

    def draw_dot() -> None:
        r = max(1, cfg.size)
        if use_outline:
            ro = r + cfg.outline_thickness
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(outline_color))
            painter.drawEllipse(QPoint(cx, cy), ro, ro)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(main))
        painter.drawEllipse(QPoint(cx, cy), r, r)

    def draw_plus_lines() -> None:
        gap = cfg.gap
        s = cfg.size
        # horizontal
        painter.drawLine(cx - s, cy, cx - gap, cy)
        painter.drawLine(cx + gap, cy, cx + s, cy)
        # vertical
        painter.drawLine(cx, cy - s, cx, cy - gap)
        painter.drawLine(cx, cy + gap, cx, cy + s)

    def draw_t_lines() -> None:
        gap = cfg.gap
        s = cfg.size
        painter.drawLine(cx - s, cy, cx - gap, cy)
        painter.drawLine(cx + gap, cy, cx + s, cy)
        painter.drawLine(cx, cy + gap, cx, cy + s)

    def draw_circle() -> None:
        r = cfg.size
        rect = QRect(cx - r, cy - r, r * 2, r * 2)
        if use_outline:
            painter.setPen(QPen(outline_color, cfg.thickness + cfg.outline_thickness * 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(rect)
        painter.setPen(QPen(main, cfg.thickness))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect)

    if shape == "dot":
        draw_dot()
    elif shape == "plus":
        stroked(draw_plus_lines)
    elif shape == "plus_dot":
        stroked(draw_plus_lines)
        r = max(1, cfg.thickness)
        if use_outline:
            ro = r + cfg.outline_thickness
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(outline_color))
            painter.drawEllipse(QPoint(cx, cy), ro, ro)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(main))
        painter.drawEllipse(QPoint(cx, cy), r, r)
    elif shape == "circle":
        draw_circle()
    elif shape == "circle_dot":
        draw_circle()
        # center dot — small
        r = max(1, cfg.thickness)
        if use_outline:
            ro = r + cfg.outline_thickness
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(outline_color))
            painter.drawEllipse(QPoint(cx, cy), ro, ro)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(main))
        painter.drawEllipse(QPoint(cx, cy), r, r)
    elif shape == "t_shape":
        stroked(draw_t_lines)
    else:
        draw_dot()
