from __future__ import annotations

import window_focus


def test_is_target_focused_exact_match(monkeypatch):
    monkeypatch.setattr(
        window_focus, "foreground_process_name",
        lambda: "FortniteClient-Win64-Shipping.exe",
    )
    assert window_focus.is_target_focused(["FortniteClient-Win64-Shipping.exe"]) is True


def test_is_target_focused_is_case_insensitive(monkeypatch):
    monkeypatch.setattr(
        window_focus, "foreground_process_name",
        lambda: "fortniteclient-win64-shipping.exe",
    )
    assert window_focus.is_target_focused(["FortniteClient-Win64-Shipping.exe"]) is True


def test_is_target_focused_no_match(monkeypatch):
    monkeypatch.setattr(window_focus, "foreground_process_name", lambda: "notepad.exe")
    assert window_focus.is_target_focused(["fortnite.exe", "apex.exe"]) is False


def test_is_target_focused_is_permissive_when_unknown(monkeypatch):
    """If we can't read the foreground process we don't want to *hide* the
    overlay — better to leave it visible than fight the user."""
    monkeypatch.setattr(window_focus, "foreground_process_name", lambda: None)
    assert window_focus.is_target_focused(["fortnite.exe"]) is True


def test_is_target_focused_handles_target_with_path(monkeypatch):
    """User may paste a full path; only basename should matter."""
    monkeypatch.setattr(window_focus, "foreground_process_name", lambda: "fortnite.exe")
    assert window_focus.is_target_focused(["C:\\Games\\Epic\\fortnite.exe"]) is True


def test_is_target_focused_empty_list(monkeypatch):
    monkeypatch.setattr(window_focus, "foreground_process_name", lambda: "notepad.exe")
    assert window_focus.is_target_focused([]) is False
