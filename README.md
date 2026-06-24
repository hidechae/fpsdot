# fpsdot

A transparent crosshair overlay for FPS games (Fortnite, Apex Legends, etc.) on Windows. Draws a small dot or crosshair on top of the screen so you can clearly see the exact center of your viewport.

The overlay is a separate top-level window — **no DLL injection, no DirectX/OpenGL hooking, no interaction with the game process whatsoever**. It uses the same Windows layered-window mechanism as OBS or Discord overlays.

---

## Features

Modeled after the standard feature set of HudSight / CrossOver / Custom-Crosshair-Mod:

- **6 crosshair shapes**: Dot / Plus / Plus+Dot / Circle / Circle+Dot / T-shape
- **Full styling**: color, size, thickness, center gap, opacity
- **Outline** (black border) for contrast on any background
- **Per-monitor DPI aware** — places the dot at the true center on 4K + Windows scaling setups
- **Target-process gating** — by default the overlay is shown only while `FortniteClient-Win64-Shipping.exe` or `r5apex.exe` (Apex) is the foreground window
- **Always-on-top + click-through** — the mouse passes straight through the overlay
- **Global hotkeys** (defaults: `F8` to toggle, `Ctrl+Shift+X` for settings)
- **Tray-resident** with a live-preview settings window
- **7 built-in presets** (Pro Dot, CS:GO-style Plus, Circle+Dot, etc.)

---

## Setup

Requires Windows 10/11 and Python 3.10+.

```bat
git clone https://github.com/hidechae/fpsdot.git
cd fpsdot
run.bat
```

On first run, `run.bat` creates a `.venv`, installs dependencies, then launches the app. If no real Python interpreter is found (only the Microsoft Store stub), it offers to install Python 3.12 via winget.

Manual install:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python src\main.py
```

After the first successful launch, use `run-silent.bat` for normal everyday use — it runs the app without a console window via `pythonw.exe`.

---

## Usage

1. When the app starts, a tray icon appears (a tiny crosshair). Left-click it to open Settings; right-click for the menu (toggle / settings / quit).
2. Launch Fortnite or Apex. As soon as the game window becomes the foreground window, the dot appears at its center automatically.
3. Press `F8` to toggle the overlay on/off. Press `Ctrl+Shift+X` to bring up the settings window.

### Adding another game

Settings → **Overlay** tab → **Target processes** → enter the executable name (e.g. `VALORANT-Win64-Shipping.exe`) and click Add. You can find the exact name under the *Details* tab of Task Manager.

### Monitor / offset adjustment

- The monitor selector defaults to **Auto (focused window)** — the dot follows the center of whichever window is in focus. This works best in **borderless / fullscreen-windowed** modes.
- True exclusive fullscreen may hide the overlay. Switch the game to **borderless windowed** if the dot doesn't show.
- If the game UI's center is off-screen-center (some games), use the X/Y offset to align.

---

## Pro-style crosshair guidelines

| Use case | Shape | Size | Thickness | Gap | Color | Outline |
|---|---|---|---|---|---|---|
| Pure center dot (build + aim) | Dot | 3–4 | 3–4 | — | `#00FF00` / `#00FFFF` | on / 1px |
| AR / SMG | Plus + Dot | 8–10 | 2 | 3–4 | `#00FF00` | on / 1px |
| Shotgun body indicator | Circle + Dot | 12–16 | 2 | 0 | `#FFFFFF` | on / 1px |
| Sniper aid | T-shape | 6–8 | 2 | 3 | `#FFFF00` | on / 1px |

Pick a color that contrasts strongly with the dominant background colors of the maps you play. **Cyan and magenta** stay visible across forests, snow, and deserts alike.

---

## Anti-cheat (EAC) and Terms of Service — please read

This tool does **not** inject any code into the game process and does **not** hook any graphics or input APIs. It is a stand-alone, top-level Windows layered window that simply renders pixels on the desktop — the same technique used by OBS, Discord overlay, RTSS, etc. Easy Anti-Cheat / BattlEye target in-process tampering, which this tool does not do.

That said:

- **Epic Games' Terms of Service for Fortnite prohibit third-party software that confers a competitive advantage.** Whether a crosshair overlay falls under this clause is up to Epic's interpretation. **Use at your own risk** — the author accepts no responsibility for account bans or other consequences arising from use of this tool.
- In competitive events and ranked matches, third-party visual aids are very likely a ToS violation. Recommended for **custom matches / practice / casual play** only.
- **Do not use this with Valorant.** Riot Vanguard runs in kernel mode and applies its own criteria; cosmetic overlays are explicitly disallowed regardless of how they are implemented.

---

## Troubleshooting

- **Dot is not visible** → Run the game in **borderless windowed** mode. True exclusive fullscreen blocks overlays at the OS level.
- **Mouse seems to interact with the dot** → Should never happen. Click-through (`WS_EX_TRANSPARENT`) is applied at startup; toggle the overlay off/on once if anything looks wrong.
- **Hotkey doesn't fire** → Another app (OBS / Discord / Steam) may have claimed the same combination. Change it in Settings → Hotkeys.
- **Dot is offset on a multi-monitor setup** → Switch Settings → Overlay → Monitor from `Auto` to a specific monitor, or adjust Offset X/Y.

---

## Building a single-file EXE (optional)

```bat
.venv\Scripts\activate
pip install pyinstaller
pyinstaller --noconsole --onefile --name fpsdot src\main.py
```

The binary will be at `dist\fpsdot.exe`.

---

## Project layout

```
fpsdot/
├── README.md
├── requirements.txt
├── pyproject.toml
├── run.bat                 # First-run launcher (creates .venv, installs deps)
├── run-silent.bat          # Silent launcher (post-setup, no console)
└── src/
    ├── main.py             # Entry point, system-tray glue
    ├── overlay.py          # Transparent click-through window
    ├── settings_window.py  # Settings GUI with live preview
    ├── crosshair.py        # Shape rendering
    ├── config.py           # JSON config + presets
    ├── hotkeys.py          # Win32 RegisterHotKey wrapper
    └── window_focus.py     # Foreground-window detection + DPI conversion
```

User config is stored at `%USERPROFILE%\.fpsdot\config.json`.
