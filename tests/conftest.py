"""Shared pytest setup.

- Set QT_QPA_PLATFORM=offscreen so Qt runs without a display (CI / headless).
- Put `src/` on sys.path so test files can `import config`, `import crosshair`, etc.
- Provide a session-scoped QApplication fixture for tests that need to paint.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


import pytest  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    return app
