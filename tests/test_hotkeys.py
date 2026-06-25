from __future__ import annotations

import pytest

from hotkeys import (
    parse_hotkey,
    MOD_CONTROL,
    MOD_SHIFT,
    MOD_ALT,
    MOD_WIN,
    MOD_NOREPEAT,
)


@pytest.mark.parametrize(
    "spec, expected_mods, expected_vk",
    [
        ("F8", MOD_NOREPEAT, 0x77),
        ("F12", MOD_NOREPEAT, 0x7B),
        ("X", MOD_NOREPEAT, 0x58),
        ("1", MOD_NOREPEAT, 0x31),
        ("SPACE", MOD_NOREPEAT, 0x20),
        ("Ctrl+Shift+X", MOD_NOREPEAT | MOD_CONTROL | MOD_SHIFT, 0x58),
        ("alt+f1", MOD_NOREPEAT | MOD_ALT, 0x70),
        ("Win+Space", MOD_NOREPEAT | MOD_WIN, 0x20),
        ("Ctrl+1", MOD_NOREPEAT | MOD_CONTROL, 0x31),
        ("CONTROL+alt+DELETE", MOD_NOREPEAT | MOD_CONTROL | MOD_ALT, 0x2E),
    ],
)
def test_parse_hotkey_valid(spec, expected_mods, expected_vk):
    assert parse_hotkey(spec) == (expected_mods, expected_vk)


@pytest.mark.parametrize(
    "spec",
    [
        "",
        "Ctrl+",          # only modifier
        "Ctrl+Shift+",    # only modifiers
        "+",              # nothing
        "Ctrl+Alt+NotAKey",  # unknown key name
        "Bogus",          # unknown bare key
        "F99",            # out of range function key
    ],
)
def test_parse_hotkey_invalid_returns_none(spec):
    assert parse_hotkey(spec) is None


def test_parse_hotkey_strips_whitespace():
    assert parse_hotkey("  Ctrl + Shift + X  ") == (
        MOD_NOREPEAT | MOD_CONTROL | MOD_SHIFT,
        0x58,
    )
