import asyncio
import base64
import colorsys
import io
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import deque
from pathlib import Path

import flet as ft
from PIL import Image, ImageDraw


# --- Themes (Moonlight presets from oNxZero/Moonlight managers.py) ---

DEFAULT_THEME = "moonlight"

MOONLIGHT_THEMES = {
    "moonlight": {
        "name": "Moonlight",
        "description": "Macchiato blues — the Moonlight default",
        "base": "#24273a",
        "mantle": "#1e2030",
        "crust": "#181926",
        "text": "#cad3f5",
        "subtext": "#a5adcb",
        "surface0": "#363a4f",
        "surface1": "#494d64",
        "blue": "#8caaee",
        "red": "#ed8796",
        "green": "#a6da95",
        "slider": "#cad3f5",
        "handle": "#cad3f5",
        "outline": "#494d64",
        "logo": "#cad3f5",
        "title": "#cad3f5",
        "shadow": "#000000",
        "switch_bg": "#8caaee",
    },
    "obsidian": {
        "name": "Obsidian",
        "description": "Pure black with silver accents",
        "base": "#000000",
        "mantle": "#0a0a0a",
        "crust": "#000000",
        "text": "#ffffff",
        "subtext": "#a1a1aa",
        "surface0": "#18181b",
        "surface1": "#27272a",
        "blue": "#c0c0c0",
        "red": "#ef4444",
        "green": "#22c55e",
        "slider": "#3f3f46",
        "handle": "#ffffff",
        "outline": "#27272a",
        "logo": "#c0c0c0",
        "title": "#ffffff",
        "shadow": "#000000",
        "switch_bg": "#c0c0c0",
    },
    "dracula": {
        "name": "Dracula",
        "description": "Classic purple vampire palette",
        "base": "#282a36",
        "mantle": "#21222c",
        "crust": "#191a21",
        "text": "#f8f8f2",
        "subtext": "#bd93f9",
        "surface0": "#44475a",
        "surface1": "#6272a4",
        "blue": "#bd93f9",
        "red": "#ff5555",
        "green": "#50fa7b",
        "slider": "#bd93f9",
        "handle": "#f8f8f2",
        "outline": "#44475a",
        "logo": "#bd93f9",
        "title": "#f8f8f2",
        "shadow": "#000000",
        "switch_bg": "#bd93f9",
    },
    "nord": {
        "name": "Nord",
        "description": "Cool arctic blues and grays",
        "base": "#2e3440",
        "mantle": "#242933",
        "crust": "#1c2128",
        "text": "#d8dee9",
        "subtext": "#88c0d0",
        "surface0": "#3b4252",
        "surface1": "#434c5e",
        "blue": "#88c0d0",
        "red": "#bf616a",
        "green": "#a3be8c",
        "slider": "#5e81ac",
        "handle": "#eceff4",
        "outline": "#434c5e",
        "logo": "#88c0d0",
        "title": "#eceff4",
        "shadow": "#000000",
        "switch_bg": "#88c0d0",
    },
    "catppuccin": {
        "name": "Catppuccin",
        "description": "Mocha pastels with pink highlights",
        "base": "#1e1e2e",
        "mantle": "#181825",
        "crust": "#11111b",
        "text": "#cdd6f4",
        "subtext": "#bac2de",
        "surface0": "#313244",
        "surface1": "#45475a",
        "blue": "#89b4fa",
        "red": "#f38ba8",
        "green": "#a6e3a1",
        "slider": "#b4befe",
        "handle": "#cdd6f4",
        "outline": "#45475a",
        "logo": "#f5c2e7",
        "title": "#cdd6f4",
        "shadow": "#000000",
        "switch_bg": "#89b4fa",
    },
}


def _from_moonlight(theme_id, colors):
    return {
        "name": colors["name"],
        "description": colors["description"],
        "mode": "dark",
        "bg": colors["crust"],
        "panel": colors["mantle"],
        "surface": colors["base"],
        "chip": colors["surface0"],
        "border": colors["outline"],
        "text": colors["text"],
        "muted": colors["subtext"],
        "accent": colors["blue"],
        "accent_dim": colors["slider"],
        "green": colors["green"],
        "red": colors["red"],
        "snack_ok": colors["surface1"],
        "on_accent": "#ffffff",
    }


THEMES = {
    theme_id: _from_moonlight(theme_id, colors)
    for theme_id, colors in MOONLIGHT_THEMES.items()
}

THEMES.update(
    {
        "light": {
            "name": "Light",
            "description": "White background with black text",
            "mode": "light",
            "bg": "#ffffff",
            "panel": "#ffffff",
            "surface": "#ffffff",
            "chip": "#f5f5f5",
            "border": "#e5e5e5",
            "text": "#000000",
            "muted": "#666666",
            "accent": "#2563eb",
            "accent_dim": "#2563eb",
            "green": "#16a34a",
            "red": "#dc2626",
            "snack_ok": "#dbeafe",
            "on_accent": "#ffffff",
        },
        "dark": {
            "name": "Dark",
            "description": "Neutral charcoal with soft blue accents",
            "mode": "dark",
            "bg": "#121212",
            "panel": "#1a1a1a",
            "surface": "#242424",
            "chip": "#2e2e2e",
            "border": "#404040",
            "text": "#f5f5f5",
            "muted": "#a3a3a3",
            "accent": "#60a5fa",
            "accent_dim": "#3b82f6",
            "green": "#4ade80",
            "red": "#f87171",
            "snack_ok": "#1e3a5f",
            "on_accent": "#ffffff",
        },
    }
)

THEME_ORDER = [
    "moonlight",
    "light",
    "dark",
    "obsidian",
    "catppuccin",
    "dracula",
    "nord",
]


def get_theme(theme_id):
    return THEMES.get(theme_id, THEMES[DEFAULT_THEME])


def iter_themes():
    seen = set()
    for theme_id in THEME_ORDER:
        if theme_id in THEMES:
            seen.add(theme_id)
            yield theme_id, THEMES[theme_id]
    for theme_id, meta in THEMES.items():
        if theme_id not in seen:
            yield theme_id, meta


THEME_TILE_SIZE = 96
THEME_GRID_GAP = 8
THEME_GRID_COLS = 3


def theme_grid_width():
    return THEME_TILE_SIZE * THEME_GRID_COLS + THEME_GRID_GAP * (THEME_GRID_COLS - 1)


def build_theme_tile_preview(meta):
    accent = meta["accent"]
    border = meta["border"]
    panel = meta["panel"]
    chip = meta.get("chip", meta["surface"])
    bg = meta["bg"]
    muted = meta["muted"]
    text = meta["text"]

    def preview_toggle(on):
        return ft.Container(
            width=14,
            height=6,
            border_radius=3,
            bgcolor=accent if on else muted,
            padding=1,
            content=ft.Row(
                [
                    ft.Container(
                        width=4,
                        height=4,
                        border_radius=2,
                        bgcolor=text,
                    )
                ],
                alignment=(
                    ft.MainAxisAlignment.END if on else ft.MainAxisAlignment.START
                ),
            ),
        )

    return ft.Container(
        expand=True,
        border_radius=5,
        bgcolor=bg,
        border=ft.Border.all(1, border),
        padding=4,
        content=ft.Column(
            [
                ft.Container(height=7, border_radius=2, bgcolor=panel),
                ft.Container(height=6, border_radius=2, bgcolor=chip),
                ft.Row(
                    [
                        preview_toggle(False),
                        ft.Container(expand=True),
                        preview_toggle(True),
                    ],
                    spacing=0,
                ),
                ft.Stack(
                    [
                        ft.Container(height=3, border_radius=2, bgcolor=muted),
                        ft.Container(width=16, height=3, border_radius=2, bgcolor=accent),
                        ft.Container(
                            left=13,
                            top=-1,
                            width=4,
                            height=4,
                            border_radius=2,
                            bgcolor=text,
                        ),
                    ],
                    height=5,
                ),
            ],
            spacing=3,
            expand=True,
        ),
    )


def build_theme_card(meta, selected, on_pick):
    accent = meta["accent"]
    border = meta["border"]
    card_bg = meta["chip"] if selected else meta["surface"]
    swatches = ft.Row(
        [
            ft.Container(width=10, height=10, border_radius=2, bgcolor=meta["accent"]),
            ft.Container(
                width=10,
                height=10,
                border_radius=2,
                bgcolor=meta.get("green", meta["accent"]),
            ),
            ft.Container(
                width=10,
                height=10,
                border_radius=2,
                bgcolor=meta.get("red", meta["muted"]),
            ),
        ],
        spacing=3,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    return ft.Container(
        width=THEME_TILE_SIZE,
        height=THEME_TILE_SIZE,
        border_radius=8,
        bgcolor=card_bg,
        border=ft.Border.all(2 if selected else 1, accent if selected else border),
        padding=6,
        ink=True,
        on_click=on_pick,
        content=ft.Column(
            [
                build_theme_tile_preview(meta),
                ft.Text(
                    meta["name"],
                    size=11,
                    weight=ft.FontWeight.W_600,
                    color=meta["text"],
                    text_align=ft.TextAlign.CENTER,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                swatches,
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        ),
    )


ROOT = Path(__file__).resolve().parent

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "ctm-generator")
CONFIG_PATH = os.path.join(CONFIG_DIR, "settings.json")
MAX_UNDO = 50
PREVIEW_TEXEL_SCALE = 32
PREVIEW_MAX_PX = 2048
ZOOM_MIN = 0.25
ZOOM_MAX = 4.0
ZOOM_STEP = 0.1
ZOOM_STEP_FINE = 0.01
DEFAULT_PREVIEW_ZOOM = 0.5
ZOOM_SLIDER_DIVISIONS = 240
ZOOM_PERCENT_MIN = 50
ZOOM_PERCENT_MAX = 500
ZOOM_PERCENT_FIT = 100
ZOOM_SCROLL_STEP = 5
BORDER_WIDTH_UI_MAX = 16

_CTRL_KEYS = frozenset({"control left", "control right"})


def _is_ctrl_key(key: str) -> bool:
    return (key or "").strip().lower() in _CTRL_KEYS


def scroll_wheel_zooms_in(delta_y: float) -> bool:
    if platform.system() == "Windows":
        return delta_y > 0
    return delta_y < 0


def sanitize_viewport_dim(value, default=600):
    try:
        size = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(size) or size <= 0:
        return default
    return max(200, min(int(size), 8192))


def prefer_flet_ctrl_fallback() -> bool:
    return bool(os.environ.get("WAYLAND_DISPLAY"))


class CtrlTracker:
    def __init__(self):
        self.pressed = False
        self._listener = None
        self.use_flet_fallback = False
        self._flet_refs = 0

    def start(self):
        if prefer_flet_ctrl_fallback():
            self.use_flet_fallback = True
            return
        if self._start_pynput():
            return
        self.use_flet_fallback = True

    def _start_pynput(self) -> bool:
        try:
            from pynput.keyboard import Key, Listener

            ctrl_keys = {Key.ctrl_l, Key.ctrl_r}

            def on_press(key):
                if key in ctrl_keys:
                    self.pressed = True

            def on_release(key):
                if key in ctrl_keys:
                    self.pressed = False

            self._listener = Listener(on_press=on_press, on_release=on_release)
            self._listener.daemon = True
            self._listener.start()
            return True
        except Exception:
            self._listener = None
            return False

    def on_flet_key_down(self, e: ft.KeyDownEvent):
        if not self.use_flet_fallback:
            return
        if _is_ctrl_key(e.key):
            self._flet_refs += 1
            self.pressed = True

    def on_flet_key_up(self, e: ft.KeyUpEvent):
        if not self.use_flet_fallback:
            return
        if _is_ctrl_key(e.key):
            self._flet_refs = max(0, self._flet_refs - 1)
            self.pressed = self._flet_refs > 0

    def on_flet_keyboard(self, e: ft.KeyboardEvent):
        if not self.use_flet_fallback:
            return
        if _is_ctrl_key(e.key) or e.ctrl:
            self.pressed = True


def zoom_step_for_span(span):
    span = max(float(span), 0.0)
    if span <= 0.2:
        return ZOOM_STEP_FINE
    if span <= 0.75:
        return 0.02
    if span <= 2.0:
        return 0.05
    return ZOOM_STEP


def snap_zoom(value, max_zoom=None, min_zoom=None, step=None):
    min_z = min_zoom if min_zoom is not None else ZOOM_MIN
    cap = max_zoom if max_zoom is not None else ZOOM_MAX
    if step is None:
        step = zoom_step_for_span(cap - min_z)
    stepped = round(round(value / step) * step, 3)
    return max(min_z, min(cap, stepped))


def clamp_zoom(value, max_zoom=None, min_zoom=None):
    min_z = min_zoom if min_zoom is not None else ZOOM_MIN
    cap = max_zoom if max_zoom is not None else ZOOM_MAX
    return max(min_z, min(cap, float(value)))


def format_zoom_value(value, fit_zoom, min_zoom=None, max_zoom=None, step=None):
    min_z = min_zoom if min_zoom is not None else ZOOM_MIN
    cap = max_zoom if max_zoom is not None else ZOOM_MAX
    zoom = snap_zoom(value, cap, min_z, step)
    if fit_zoom > 0:
        return f"{zoom / fit_zoom * 100:.0f}%"
    if zoom < 1:
        return f"{zoom:.2f}×"
    return f"{zoom:.1f}×"


# Design tokens (updated by theme)
C_BG = "#0f1117"
C_PANEL = "#16181f"
C_SURFACE = "#1e2129"
C_CHIP = "#282c36"
C_BORDER = "#3d4451"
C_TEXT = "#e8eaed"
C_MUTED = "#9aa0a9"
C_ACCENT = "#5b9cf5"
C_ACCENT_DIM = "#3d7dd6"
C_SNACK_OK = "#1e3a5f"
C_ON_ACCENT = "#ffffff"


def apply_theme_colors(theme_id):
    global C_BG, C_PANEL, C_SURFACE, C_CHIP, C_BORDER, C_TEXT, C_MUTED
    global C_ACCENT, C_ACCENT_DIM, C_SNACK_OK, C_ON_ACCENT
    t = get_theme(theme_id)
    C_BG = t["bg"]
    C_PANEL = t["panel"]
    C_SURFACE = t["surface"]
    C_CHIP = t["chip"]
    C_BORDER = t["border"]
    C_TEXT = t["text"]
    C_MUTED = t["muted"]
    C_ACCENT = t["accent"]
    C_ACCENT_DIM = t["accent_dim"]
    C_SNACK_OK = t["snack_ok"]
    C_ON_ACCENT = t.get("on_accent", C_TEXT)
    return t
ICON_BTN_STYLE = ft.ButtonStyle(
    padding=6,
    shape=ft.RoundedRectangleBorder(radius=6),
)
CHIP_SWATCH = 28
CHIP_HEX_H = 28


def chip_divider():
    return ft.Container(width=1, height=22, bgcolor=C_BORDER)


def color_chip_row(swatch, hex_field, trailing=None):
    items = [swatch, hex_field]
    if trailing is not None:
        items.append(trailing)
    return ft.Container(
        border=ft.Border.all(1, C_BORDER),
        border_radius=8,
        bgcolor=C_CHIP,
        padding=ft.Padding(left=8, right=8, top=6, bottom=6),
        content=ft.Row(
            items,
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


SLIDER_VALUE_W = 44


def slider_value_field(value, *, suffix=None, on_submit=None, on_blur=None, on_focus=None):
    return ft.TextField(
        value=str(value),
        width=SLIDER_VALUE_W + (10 if suffix else 0),
        height=28,
        text_size=12,
        border_radius=4,
        bgcolor=C_SURFACE,
        border_color=C_BORDER,
        focused_border_color=C_ACCENT,
        content_padding=ft.Padding(left=4, right=4),
        text_align=ft.TextAlign.RIGHT,
        keyboard_type=ft.KeyboardType.NUMBER,
        suffix=ft.Text(suffix, size=12, color=C_MUTED) if suffix else None,
        on_submit=on_submit,
        on_blur=on_blur,
        on_focus=on_focus,
    )


def border_slider_divisions(max_width):
    max_width = int(max_width)
    if max_width <= 0:
        return None
    if max_width <= 48:
        return max_width
    return None


PRESET_COLORS = [
    "#000000", "#FFFFFF", "#9CA3AF", "#6B7280", "#EF4444", "#F97316",
    "#EAB308", "#22C55E", "#3B82F6", "#8B5CF6", "#EC4899", "#06B6D4",
]

CTM_RULES = [
    (1, 1, 1, 1, 1, 1, 1, 1),
    (1, 1, 1, 1, 1, 0, 1, 1),
    (1, 1, 1, 1, 1, 0, 1, 0),
    (1, 1, 1, 1, 1, 1, 1, 0),
    (1, 1, 1, 1, 1, 0, 0, 1),
    (1, 1, 1, 1, 1, 1, 0, 0),
    (1, 1, 1, 1, 0, 0, 0, 1),
    (1, 1, 1, 1, 1, 0, 0, 0),
    (1, 0, 1, 1, 0, 0, 0, 0),
    (1, 1, 1, 0, 0, 0, 0, 0),
    (0, 1, 0, 1, 0, 0, 0, 0),
    (0, 0, 1, 1, 0, 0, 0, 0),
    (1, 1, 1, 1, 1, 1, 0, 1),
    (1, 1, 1, 0, 1, 0, 0, 1),
    (1, 1, 0, 0, 1, 0, 0, 0),
    (1, 1, 0, 1, 1, 1, 0, 0),
    (1, 1, 1, 1, 0, 0, 1, 1),
    (1, 1, 1, 1, 0, 1, 1, 0),
    (1, 1, 1, 1, 0, 0, 1, 0),
    (1, 1, 1, 1, 0, 1, 0, 0),
    (0, 1, 1, 1, 0, 0, 0, 0),
    (1, 1, 0, 1, 0, 0, 0, 0),
    (1, 1, 0, 0, 0, 0, 0, 0),
    (1, 0, 1, 0, 0, 0, 0, 0),
    (1, 1, 1, 1, 0, 1, 0, 1),
    (1, 0, 1, 0, 0, 0, 0, 1),
    (0, 0, 0, 0, 0, 0, 0, 0),
    (0, 1, 0, 1, 0, 1, 0, 0),
    (1, 1, 1, 0, 0, 0, 0, 1),
    (1, 1, 0, 1, 1, 0, 0, 0),
    (1, 0, 1, 1, 0, 0, 0, 1),
    (1, 1, 1, 0, 1, 0, 0, 0),
    (0, 0, 0, 1, 0, 0, 0, 0),
    (0, 0, 1, 0, 0, 0, 0, 0),
    (1, 0, 0, 1, 0, 0, 0, 0),
    (0, 1, 1, 0, 0, 0, 0, 0),
    (1, 1, 1, 1, 0, 1, 1, 1),
    (1, 0, 1, 1, 0, 0, 1, 1),
    (0, 0, 1, 1, 0, 0, 1, 0),
    (0, 1, 1, 1, 0, 1, 1, 0),
    (1, 0, 1, 1, 0, 0, 1, 0),
    (0, 1, 1, 1, 0, 1, 0, 0),
    (0, 1, 1, 1, 0, 0, 1, 0),
    (1, 1, 0, 1, 0, 1, 0, 0),
    (0, 1, 0, 0, 0, 0, 0, 0),
    (1, 0, 0, 0, 0, 0, 0, 0),
    (1, 1, 1, 1, 0, 0, 0, 0),
]

# 3×5 pixel digits — no anti-aliasing, solid red only
_DIGIT_3X5 = {
    "0": ("###", "#.#", "#.#", "#.#", "###"),
    "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"),
    "3": ("###", "..#", "###", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"),
    "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"),
    "7": ("###", "..#", "..#", "..#", "..#"),
    "8": ("###", "#.#", "###", "#.#", "###"),
    "9": ("###", "#.#", "###", "..#", "###"),
}
_DIGIT_W = 3
_DIGIT_H = 5
_DIGIT_GAP = 1


def _render_pixel_digits(text, scale):
    count = len(text)
    raw_w = count * _DIGIT_W + (count - 1) * _DIGIT_GAP
    raw_h = _DIGIT_H
    layer = Image.new("RGBA", (raw_w, raw_h), (0, 0, 0, 0))
    px = layer.load()
    red = (255, 0, 0, 255)
    for i, ch in enumerate(text):
        glyph = _DIGIT_3X5[ch]
        ox = i * (_DIGIT_W + _DIGIT_GAP)
        for row, line in enumerate(glyph):
            for col, cell in enumerate(line):
                if cell == "#":
                    px[ox + col, row] = red
    if scale > 1:
        layer = layer.resize(
            (raw_w * scale, raw_h * scale), Image.Resampling.NEAREST
        )
    return layer


def overlay_tile_index(image, index, border_width=0):
    img = image.copy()
    w, h = img.size
    bw = max(0, int(border_width))
    inner_l = bw
    inner_t = bw
    inner_r = w - bw
    inner_b = h - bw
    inner_w = max(1, inner_r - inner_l)
    inner_h = max(1, inner_b - inner_t)

    text = str(index)
    label_digits = 2
    raw_w = label_digits * _DIGIT_W + (label_digits - 1) * _DIGIT_GAP
    max_scale = max(1, min(inner_w // raw_w, inner_h // _DIGIT_H))
    scale = max(1, max_scale // 2)
    digits = _render_pixel_digits(text, scale)
    dx = inner_l + (inner_w - digits.width) // 2
    dy = inner_t + (inner_h - digits.height) // 2
    img.paste(digits, (dx, dy), digits)
    return img


def rgb_to_hex(rgb):
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_hsv255(rgb):
    h, s, v = colorsys.rgb_to_hsv(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255)
    return round(h * 360), round(s * 100), round(v * 100)


def hsv255_to_rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h / 360, s / 100, v / 100)
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


PICKER_W = 300
SV_PLANE_H = 130
PICKER_SWATCH = 48
PICKER_SLIDER_W = PICKER_W - PICKER_SWATCH - 12
PICKER_STRIP_H = 16
ALPHA_STRIP_H = 22
PICKER_MARKER = 14
SV_PLANE_W = PICKER_W
HUE_STRIP_H = PICKER_STRIP_H

_HUE_STRIP_SRC = None
_SV_PLANE_SRC_CACHE = {}
_ALPHA_STRIP_CACHE = {}
_CHECKER_PREVIEW_SRC = None
_CHECKER_TILE_SRC = None


def get_checker_preview_src():
    global _CHECKER_PREVIEW_SRC
    if _CHECKER_PREVIEW_SRC is None:
        _CHECKER_PREVIEW_SRC = pil_to_src(tiled_checkerboard(56, 56, tile_size=8))
    return _CHECKER_PREVIEW_SRC


def get_checker_tile_src():
    global _CHECKER_TILE_SRC
    if _CHECKER_TILE_SRC is None:
        _CHECKER_TILE_SRC = pil_to_src(make_checkerboard(16, 8))
    return _CHECKER_TILE_SRC


def make_sv_plane_image(hue, width=SV_PLANE_W, height=SV_PLANE_H):
    hue_key = int(round(hue)) % 360
    h_norm = hue_key / 360.0
    ymax = max(height - 1, 1)
    xmax = max(width - 1, 1)
    pixels = bytearray(width * height * 3)
    offset = 0
    for y in range(height):
        v = 1.0 - y / ymax
        for x in range(width):
            s = x / xmax
            r, g, b = colorsys.hsv_to_rgb(h_norm, s, v)
            pixels[offset] = int(r * 255)
            pixels[offset + 1] = int(g * 255)
            pixels[offset + 2] = int(b * 255)
            offset += 3
    return Image.frombytes("RGB", (width, height), bytes(pixels))


def make_hue_strip_image(width=SV_PLANE_W, height=HUE_STRIP_H):
    row_bytes = bytearray(width * 3)
    xmax = max(width - 1, 1)
    rows = []
    for x in range(width):
        r, g, b = colorsys.hsv_to_rgb(x / xmax, 1.0, 1.0)
        row_bytes[x * 3] = int(r * 255)
        row_bytes[x * 3 + 1] = int(g * 255)
        row_bytes[x * 3 + 2] = int(b * 255)
    row = bytes(row_bytes)
    for _ in range(height):
        rows.append(row)
    return Image.frombytes("RGB", (width, height), b"".join(rows))


def get_hue_strip_src(width=PICKER_SLIDER_W, height=HUE_STRIP_H):
    global _HUE_STRIP_SRC
    if _HUE_STRIP_SRC is None:
        _HUE_STRIP_SRC = pil_to_src(make_hue_strip_image(width, height))
    return _HUE_STRIP_SRC


def make_light_checkerboard(width, height, cell=6):
    tile = Image.new("RGBA", (cell * 2, cell * 2), (255, 255, 255, 255))
    px = tile.load()
    dark = (192, 192, 192, 255)
    for y in range(cell * 2):
        for x in range(cell * 2):
            if (x // cell + y // cell) % 2:
                px[x, y] = dark
    canvas = Image.new("RGBA", (width, height))
    for y in range(0, height, cell * 2):
        for x in range(0, width, cell * 2):
            canvas.paste(tile, (x, y))
    return canvas


def make_alpha_strip_image(rgb, width=PICKER_SLIDER_W, height=ALPHA_STRIP_H):
    bg = make_light_checkerboard(width, height, cell=6)
    fg = Image.new("RGBA", (width, height), (*rgb, 255))
    xmax = max(width - 1, 1)
    mask_pixels = [
        int(x / xmax * 255) for y in range(height) for x in range(width)
    ]
    mask = Image.new("L", (width, height))
    mask.putdata(mask_pixels)
    return Image.composite(fg, bg, mask)


def get_alpha_strip_src(rgb):
    key = (rgb, PICKER_SLIDER_W, ALPHA_STRIP_H)
    cached = _ALPHA_STRIP_CACHE.get(key)
    if cached is None:
        if len(_ALPHA_STRIP_CACHE) > 128:
            _ALPHA_STRIP_CACHE.clear()
        cached = pil_to_src(make_alpha_strip_image(rgb))
        _ALPHA_STRIP_CACHE[key] = cached
    return cached


def picker_marker_left(value_ratio, track_w):
    return max(
        0,
        min(track_w - PICKER_MARKER, value_ratio * track_w - PICKER_MARKER / 2),
    )


def picker_track_pad(track_h):
    return max(3, (PICKER_MARKER - track_h) // 2 + 1)


def picker_track_height(track_h):
    return track_h + picker_track_pad(track_h) * 2


def make_picker_marker(left=0, top=0):
    return ft.Container(
        width=PICKER_MARKER,
        height=PICKER_MARKER,
        left=left,
        top=top,
        border_radius=PICKER_MARKER // 2,
        bgcolor="#FFFFFF",
        border=ft.Border.all(2, ft.Colors.with_opacity(0.5, "#000000")),
    )


def make_picker_strip_field(
    image,
    marker,
    track_w,
    track_h,
    on_tap,
    on_pan,
    on_pan_end,
):
    pad = picker_track_pad(track_h)
    stack_h = picker_track_height(track_h)
    marker.top = pad + (track_h - PICKER_MARKER) // 2
    return ft.GestureDetector(
        on_tap_down=on_tap,
        on_pan_update=on_pan,
        on_pan_end=on_pan_end,
        content=ft.Container(
            width=track_w,
            height=stack_h,
            content=ft.Stack(
                width=track_w,
                height=stack_h,
                controls=[
                    ft.Container(
                        top=pad,
                        width=track_w,
                        height=track_h,
                        border_radius=6,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        content=image,
                    ),
                    marker,
                ],
            ),
        ),
    )


def get_sv_plane_src(hue):
    key = int(round(hue)) % 360
    cached = _SV_PLANE_SRC_CACHE.get(key)
    if cached is None:
        cached = pil_to_src(make_sv_plane_image(key))
        _SV_PLANE_SRC_CACHE[key] = cached
    return cached


def parse_hex_color(hex_color):
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) in (3, 4):
        hex_color = "".join(c * 2 for c in hex_color)
    if len(hex_color) == 6:
        rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        return rgb, None
    if len(hex_color) == 8:
        rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        alpha = int(hex_color[6:8], 16)
        return rgb, alpha
    raise ValueError(f"Invalid hex color: {hex_color}")


def hex_to_rgb(hex_color):
    rgb, _ = parse_hex_color(hex_color)
    return rgb


def parse_rgb(rgb):
    if isinstance(rgb, str):
        return hex_to_rgb(rgb)
    values = [float(v) for v in rgb]
    if max(values) <= 1.0:
        values = [v * 255 for v in values]
    return tuple(int(round(v)) for v in values[:3])


def pil_to_b64(image, fast=False):
    buf = io.BytesIO()
    if fast:
        image.save(buf, format="PNG", compress_level=1)
    else:
        image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def pil_to_src(image, fast=False, live=False):
    if live:
        buf = io.BytesIO()
        image.save(buf, format="PNG", compress_level=0, optimize=False)
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    return f"data:image/png;base64,{pil_to_b64(image, fast)}"


def make_checkerboard(size=16, cell=8):
    img = Image.new("RGBA", (size, size), "#1c1c1f")
    pixels = img.load()
    light = (36, 36, 40, 255)
    dark = (24, 24, 27, 255)
    for y in range(size):
        for x in range(size):
            pixels[x, y] = light if (x // cell + y // cell) % 2 else dark
    return img


def tiled_checkerboard(width, height, tile_size=16):
    tile = make_checkerboard(tile_size, tile_size // 2)
    canvas = Image.new("RGBA", (width, height))
    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            canvas.paste(tile, (x, y))
    return canvas


_VIEWPORT_CHECKER_CACHE = {}


def cached_viewport_checkerboard(width, height):
    key = (width, height)
    cached = _VIEWPORT_CHECKER_CACHE.get(key)
    if cached is None:
        cached = tiled_checkerboard(width, height)
        _VIEWPORT_CHECKER_CACHE[key] = cached
    return cached.copy()


def is_remembered_directory(path):
    if not path or not os.path.isdir(path):
        return False
    real = os.path.realpath(path)
    temp_root = os.path.realpath(tempfile.gettempdir())
    return real != temp_root and not real.startswith(temp_root + os.sep)


def load_settings():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def save_settings(**updates):
    data = load_settings()
    data.update(updates)
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


def load_last_save_directory():
    data = load_settings()
    last_dir = data.get("last_save_directory", data.get("last_directory", ""))
    if is_remembered_directory(last_dir):
        return last_dir
    return None


def save_last_save_directory(path):
    directory = path if os.path.isdir(path) else os.path.dirname(path)
    if not is_remembered_directory(directory):
        return
    save_settings(last_save_directory=directory)


def open_path_in_file_manager(path):
    if not path or not os.path.isdir(path):
        return False
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except OSError:
        return False


class CTMEngine:
    def __init__(self):
        self.base_image = None
        self.base_filename = "texture"
        self.custom_outline_image = None
        self.border_width = 1
        self.brush_color = (0, 0, 0)
        self.brush_alpha = 255
        self.border_color = (0, 0, 0)
        self.border_alpha = 255
        self.zoom = DEFAULT_PREVIEW_ZOOM
        self.fill_tolerance = 32
        self.preview_tile = 0
        self.use_custom_outline = False
        self.show_guides = True
        self.debug_tile_labels = False
        self.last_save_directory = load_last_save_directory()
        self.preview_pan_x = 0.0
        self.preview_pan_y = 0.0
        self.preview_viewport_w = 800
        self.preview_viewport_h = 600
        self.preview_offset_x = 0
        self.preview_offset_y = 0
        self.preview_scale = 1.0
        self.preview_display_w = 0
        self.preview_display_h = 0
        self._draw_ctx = None
        self._border_layer_cache = None
        self._border_cache_key = None
        self.apply_all_tiles = False
        self.tile_bases = {}

    def clear_tile_bases(self):
        self.tile_bases.clear()

    def tile_source(self, tile_idx):
        if self.base_image is None:
            return None
        if self.apply_all_tiles:
            return self.base_image
        return self.tile_bases.get(tile_idx, self.base_image)

    def edit_image(self):
        if self.base_image is None:
            return None
        if self.apply_all_tiles:
            return self.base_image
        idx = self.preview_tile
        if idx not in self.tile_bases:
            self.tile_bases[idx] = self.base_image.copy()
        return self.tile_bases[idx]

    def invalidate_border_cache(self):
        self._border_layer_cache = None
        self._border_cache_key = None

    def set_preview_viewport(self, width, height):
        self.preview_viewport_w = max(int(width), 200)
        self.preview_viewport_h = max(int(height), 200)

    def preview_origin(self, display_w=None, display_h=None):
        if display_w is None:
            display_w = self.preview_display_w or self.tile_display_size()[0]
        if display_h is None:
            display_h = self.preview_display_h or self.tile_display_size()[1]
        return (
            (self.preview_viewport_w - display_w) / 2 + self.preview_pan_x,
            (self.preview_viewport_h - display_h) / 2 + self.preview_pan_y,
        )

    def display_scale(self, zoom=None):
        zoom = self.zoom if zoom is None else zoom
        return PREVIEW_TEXEL_SCALE * zoom

    def preview_display_metrics(self, zoom=None):
        if not self.base_image:
            return 0, 0, 1.0
        zoom = self.zoom if zoom is None else zoom
        tex_w, tex_h = self.base_image.size
        scale = self.display_scale(zoom)
        display_w = min(int(tex_w * scale), PREVIEW_MAX_PX)
        display_h = min(int(tex_h * scale), PREVIEW_MAX_PX)
        layout_scale = display_w / tex_w if tex_w else 1.0
        return display_w, display_h, layout_scale

    def tile_display_size(self, zoom=None):
        dw, dh, _ = self.preview_display_metrics(zoom)
        return dw, dh

    def center_view(self, viewport_w=None, viewport_h=None):
        if viewport_w is not None and viewport_h is not None:
            self.set_preview_viewport(viewport_w, viewport_h)
        self.preview_pan_x = 0.0
        self.preview_pan_y = 0.0

    def apply_zoom_at(self, new_zoom, focal_x, focal_y, max_zoom=None, min_zoom=None):
        if not self.base_image:
            return
        tex_w, tex_h = self.base_image.size
        old_zoom = self.zoom
        new_zoom = clamp_zoom(new_zoom, max_zoom, min_zoom)
        old_dw, old_dh, old_scale = self.preview_display_metrics(old_zoom)
        old_ox, old_oy = self.preview_origin(old_dw, old_dh)
        if old_scale > 0:
            tex_x = (focal_x - old_ox) / old_scale
            tex_y = (focal_y - old_oy) / old_scale
        else:
            tex_x = tex_w / 2
            tex_y = tex_h / 2
        self.zoom = new_zoom
        new_dw, new_dh, new_scale = self.preview_display_metrics(new_zoom)
        new_ox = focal_x - tex_x * new_scale
        new_oy = focal_y - tex_y * new_scale
        self.preview_pan_x = new_ox - (self.preview_viewport_w - new_dw) / 2
        self.preview_pan_y = new_oy - (self.preview_viewport_h - new_dh) / 2

    def _border_settings_key(self):
        return (
            self.use_custom_outline,
            self.border_width,
            self.border_color,
            self.border_alpha,
            id(self.custom_outline_image) if self.custom_outline_image else None,
        )

    def max_border_width(self):
        if not self.base_image:
            return BORDER_WIDTH_UI_MAX
        w, h = self.base_image.size
        return max(0, (min(w, h) - 1) // 2)

    def ui_border_width_max(self):
        if not self.base_image:
            return BORDER_WIDTH_UI_MAX
        return min(BORDER_WIDTH_UI_MAX, self.max_border_width())

    def _effective_border_width(self):
        return min(int(self.border_width), self.max_border_width())

    def _build_border_layer(self, rule, src_border):
        w, h = self.base_image.size
        bw = self._effective_border_width()
        border_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        if bw <= 0:
            return border_layer
        c_tl, c_tr, c_bl, c_br, e_t, e_r, e_b, e_l = rule

        def paste(piece, box):
            border_layer.paste(piece, box)

        if c_tl:
            paste(src_border.crop((0, 0, bw, bw)), (0, 0, bw, bw))
        if c_tr:
            paste(src_border.crop((w - bw, 0, w, bw)), (w - bw, 0, w, bw))
        if c_bl:
            paste(src_border.crop((0, h - bw, bw, h)), (0, h - bw, bw, h))
        if c_br:
            paste(src_border.crop((w - bw, h - bw, w, h)), (w - bw, h - bw, w, h))
        if e_t:
            paste(src_border.crop((bw, 0, w - bw, bw)), (bw, 0, w - bw, bw))
        if e_r:
            paste(src_border.crop((w - bw, bw, w, h - bw)), (w - bw, bw, w, h - bw))
        if e_b:
            paste(src_border.crop((bw, h - bw, w - bw, h)), (bw, h - bw, w - bw, h))
        if e_l:
            paste(src_border.crop((0, bw, bw, h - bw)), (0, bw, bw, h - bw))
        return border_layer

    def get_source_border(self):
        if self.base_image is None:
            return None
        w, h = self.base_image.size
        bw = int(self.border_width)
        if bw <= 0:
            return Image.new("RGBA", (w, h), (0, 0, 0, 0))

        if self.use_custom_outline:
            if not self.custom_outline_image:
                return Image.new("RGBA", (w, h), (0, 0, 0, 0))
            outline_img = self.custom_outline_image
            outline = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            outline.paste(outline_img.crop((0, 0, w, bw)), (0, 0, w, bw))
            outline.paste(outline_img.crop((0, h - bw, w, h)), (0, h - bw, w, h))
            outline.paste(outline_img.crop((0, bw, bw, h - bw)), (0, bw, bw, h - bw))
            outline.paste(
                outline_img.crop((w - bw, bw, w, h - bw)), (w - bw, bw, w, h - bw)
            )
            return outline

        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        c = self.border_color
        color = (c[0], c[1], c[2], int(self.border_alpha))
        draw.rectangle((0, 0, w - 1, h - 1), outline=color, width=bw)
        return img

    def create_tile(self, rule, tile_idx=0):
        if not self.base_image:
            return None
        base = self.tile_source(tile_idx)
        src_border = self.get_source_border()
        if not src_border:
            return base.copy()

        bw = int(self.border_width)
        if bw == 0:
            return base.copy()

        cache_key = (rule, self._border_settings_key())
        if cache_key != self._border_cache_key:
            self._border_layer_cache = self._build_border_layer(rule, src_border)
            self._border_cache_key = cache_key

        return Image.alpha_composite(base, self._border_layer_cache)

    def render_preview(self, viewport_w=800, viewport_h=600, live=False):
        if self.base_image is None:
            return None, None

        viewport_w = max(int(viewport_w), 200)
        viewport_h = max(int(viewport_h), 200)

        tile_idx = max(0, min(46, int(self.preview_tile)))
        self.preview_tile = tile_idx
        preview_img = self.create_tile(CTM_RULES[tile_idx], tile_idx)
        if self.debug_tile_labels:
            preview_img = overlay_tile_index(
                preview_img, tile_idx, self.border_width
            )

        display_scale = PREVIEW_TEXEL_SCALE * self.zoom
        new_w = min(int(preview_img.width * display_scale), PREVIEW_MAX_PX)
        new_h = min(int(preview_img.height * display_scale), PREVIEW_MAX_PX)

        preview_resized = preview_img.resize((new_w, new_h), Image.Resampling.NEAREST)

        if self.show_guides and self.border_width > 0:
            draw = ImageDraw.Draw(preview_resized)
            bw_px = int(self.border_width)
            scale = new_w / preview_img.width
            offset = bw_px * scale
            w_px, h_px = new_w, new_h
            guide_color = "#FF0000"
            line_w = 2
            draw.line([(offset, 0), (offset, h_px)], fill=guide_color, width=line_w)
            draw.line(
                [(w_px - offset, 0), (w_px - offset, h_px)],
                fill=guide_color,
                width=line_w,
            )
            draw.line([(0, offset), (w_px, offset)], fill=guide_color, width=line_w)
            draw.line(
                [(0, h_px - offset), (w_px, h_px - offset)],
                fill=guide_color,
                width=line_w,
            )

        self.preview_scale = new_w / preview_img.width if preview_img.width else 1.0
        self.preview_display_w = new_w
        self.preview_display_h = new_h
        return preview_resized, tile_idx

    def begin_draw(self):
        target = self.edit_image()
        if target is not None:
            self._draw_ctx = ImageDraw.Draw(target)

    def end_draw(self):
        self._draw_ctx = None

    def local_to_pixel_float(self, local_x, local_y):
        if self.base_image is None:
            return None
        origin_x, origin_y = self.preview_origin()
        fx = (local_x - origin_x) / self.preview_scale
        fy = (local_y - origin_y) / self.preview_scale
        if (
            local_x < origin_x
            or local_y < origin_y
            or local_x >= origin_x + self.preview_display_w
            or local_y >= origin_y + self.preview_display_h
        ):
            return None
        w, h = self.base_image.size
        if fx < 0 or fy < 0 or fx >= w or fy >= h:
            return None
        return fx, fy

    def local_to_pixel(self, local_x, local_y):
        coords = self.local_to_pixel_float(local_x, local_y)
        if coords is None:
            return None
        fx, fy = coords
        return int(round(fx)), int(round(fy))

    def draw_stroke(self, x0, y0, x1, y1):
        target = self.edit_image()
        if target is None:
            return False
        w, h = target.size
        x0, y0, x1, y1 = float(x0), float(y0), float(x1), float(y1)
        draw = self._draw_ctx or ImageDraw.Draw(target)
        color = (
            self.brush_color[0],
            self.brush_color[1],
            self.brush_color[2],
            int(self.brush_alpha),
        )

        def plot(px, py):
            px = max(0, min(w - 1, int(round(px))))
            py = max(0, min(h - 1, int(round(py))))
            return px, py

        dist = math.hypot(x1 - x0, y1 - y0)
        if dist < 1e-6:
            draw.point(plot(x0, y0), fill=color)
            return True

        steps = max(1, int(math.ceil(dist)))
        last = None
        for i in range(steps + 1):
            t = i / steps
            px, py = plot(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            if last is None:
                last = (px, py)
                continue
            if (px, py) != last:
                draw.line([last, (px, py)], fill=color, width=1)
                last = (px, py)
        return True

    @staticmethod
    def _colors_match(c1, c2, tolerance):
        if tolerance <= 0:
            return c1 == c2
        return max(abs(c1[i] - c2[i]) for i in range(4)) <= tolerance

    def flood_fill(self, x, y, tolerance=0):
        target = self.edit_image()
        if target is None:
            return False
        w, h = target.size
        x = max(0, min(w - 1, int(round(x))))
        y = max(0, min(h - 1, int(round(y))))
        pixels = target.load()
        target = pixels[x, y]
        fill = (
            self.brush_color[0],
            self.brush_color[1],
            self.brush_color[2],
            int(self.brush_alpha),
        )
        if self._colors_match(target, fill, tolerance):
            return False
        queue = deque([(x, y)])
        seen = {(x, y)}
        filled = 0
        while queue:
            cx, cy = queue.popleft()
            if not self._colors_match(pixels[cx, cy], target, tolerance):
                continue
            pixels[cx, cy] = fill
            filled += 1
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    queue.append((nx, ny))
        return filled > 0

    def set_brush_color(self, color):
        if isinstance(color, str):
            rgb, alpha = parse_hex_color(color)
        else:
            rgb = parse_rgb(color)
            alpha = None
        self.brush_color = rgb
        if alpha is not None:
            self.brush_alpha = alpha
        return rgb_to_hex(rgb), alpha

    def set_border_color(self, color):
        if isinstance(color, str):
            rgb, alpha = parse_hex_color(color)
        else:
            rgb = parse_rgb(color)
            alpha = None
        self.border_color = rgb
        if alpha is not None:
            self.border_alpha = alpha
        self.invalidate_border_cache()
        return rgb_to_hex(rgb), alpha

    def sample_color_at(self, local_x, local_y):
        pixel = self.local_to_pixel(local_x, local_y)
        if pixel is None:
            return None
        ix, iy = pixel
        tile_idx = max(0, min(46, int(self.preview_tile)))
        tile_img = self.create_tile(CTM_RULES[tile_idx], tile_idx)
        r, g, b, a = tile_img.getpixel((ix, iy))
        return f"{r:02X}{g:02X}{b:02X}{a:02X}", (ix, iy)

    def generate(self, save_dir):
        out_path = os.path.join(save_dir, self.base_filename)
        os.makedirs(out_path, exist_ok=True)
        for i, rule in enumerate(CTM_RULES):
            tile_img = self.create_tile(rule, tile_idx=i)
            if self.debug_tile_labels:
                tile_img = overlay_tile_index(tile_img, i, self.border_width)
            tile_img.save(os.path.join(out_path, f"{i}.png"))
        with open(os.path.join(out_path, f"{self.base_filename}.properties"), "w") as f:
            f.write(f"matchTiles={self.base_filename}\n")
            f.write("method=ctm\n")
            f.write("tiles=0-46\n")
            f.write("connect=tile\n")
        return out_path


def main(page: ft.Page):
    engine = CTMEngine()
    theme_id = load_settings().get("theme", DEFAULT_THEME)
    if theme_id not in THEMES:
        theme_id = DEFAULT_THEME
    apply_theme_colors(theme_id)
    picking_color = {"active": False, "for": "brush"}
    bucket_state = {"active": False}
    drawing_state = {"active": False, "last": None, "undo_snapshotted": False}
    syncing_hex = {"active": False}
    syncing_border_hex = {"active": False}
    edit_history = {"undo": [], "redo": [], "applying": False}
    picker_target = {"value": "brush"}
    draw_update_clock = {"t": 0.0}
    zoom_update_clock = {"t": 0.0}
    zoom_finalize_token = {"id": 0}
    syncing_zoom = {"active": False}
    syncing_border_value = {"active": False}
    syncing_alpha_value = {"active": False}
    ctrl_tracker = CtrlTracker()
    ctrl_tracker.start()
    preview_keyboard_listener = {"control": None}
    text_input_focus = {"depth": 0}

    def on_text_focus_in(_):
        text_input_focus["depth"] += 1

    def on_text_focus_out(_):
        text_input_focus["depth"] = max(0, text_input_focus["depth"] - 1)

    def text_field_shortcuts_blocked():
        return text_input_focus["depth"] > 0

    page.title = "CTM Generator"
    page.padding = 0
    page.spacing = 0
    page.bgcolor = C_BG
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed=C_ACCENT,
        visual_density=ft.VisualDensity.COMPACT,
    )
    page.window.min_width = 1100
    page.window.min_height = 700
    page.window.width = 1320
    page.window.height = 820

    INSPECTOR_W = 360
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    _blank_png = pil_to_src(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
    preview_image = ft.Image(
        src=_blank_png,
        fit=ft.BoxFit.FILL,
        gapless_playback=True,
    )
    preview_tile_layer = ft.Container(
        content=preview_image,
        left=0,
        top=0,
        width=1,
        height=1,
    )
    preview_stack = ft.Stack(controls=[preview_tile_layer], expand=True)
    preview_gesture = ft.GestureDetector(
        content=preview_stack,
        expand=True,
        on_scroll=lambda e: None,
    )
    preview_title = ft.Text("Preview", size=14, weight=ft.FontWeight.W_600, color=C_TEXT)
    status_toast = ft.Text(
        "",
        size=12,
        color=C_ACCENT,
        expand=True,
        max_lines=2,
        overflow=ft.TextOverflow.ELLIPSIS,
    )
    preview_meta = ft.Text("", size=12, color=C_MUTED)
    toast_token = {"id": 0}
    preview_viewport = {"w": 800, "h": 600}
    preview_has_texture = {"active": False}
    preview_camera_pan = {"active": False}

    def safe_page_update(*controls):
        try:
            page.update(*controls)
        except RuntimeError:
            pass

    def sync_preview_tile_layer():
        origin_x, origin_y = engine.preview_origin()
        preview_tile_layer.left = int(round(origin_x))
        preview_tile_layer.top = int(round(origin_y))
        preview_tile_layer.width = max(1, int(engine.preview_display_w))
        preview_tile_layer.height = max(1, int(engine.preview_display_h))

    def center_preview_in_viewport():
        if engine.base_image is None:
            return
        engine.set_preview_viewport(preview_viewport["w"], preview_viewport["h"])
        repaint_preview()
        engine.center_view()
        sync_preview_tile_layer()

    def repaint_preview(live=False):
        if engine.base_image is None:
            return None
        tile_img, tile_idx = engine.render_preview(
            preview_viewport["w"], preview_viewport["h"], live=live
        )
        preview_image.src = pil_to_src(tile_img, fast=live)
        sync_preview_tile_layer()
        return tile_idx

    empty_state_icon = ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, size=40, color=C_MUTED)
    empty_state_title = ft.Text(
        "No texture loaded", size=15, weight=ft.FontWeight.W_500, color=C_TEXT
    )
    empty_state_subtitle = ft.Text(
        "Open a PNG block texture to preview all 47 CTM tiles",
        size=13,
        color=C_MUTED,
        text_align=ft.TextAlign.CENTER,
    )
    empty_state = ft.Column(
        [
            empty_state_icon,
            empty_state_title,
            empty_state_subtitle,
            ft.Container(height=8),
            ft.FilledButton(
                "Open texture",
                icon=ft.Icons.FOLDER_OPEN_OUTLINED,
                height=40,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                on_click=lambda e: page.run_task(pick_texture),
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True,
    )
    border_value = slider_value_field("1", suffix="px")
    alpha_value = slider_value_field("255")
    zoom_value = ft.Text("100%", size=12, color=C_MUTED)
    tile_value = ft.Text("00 / 46", size=13, weight=ft.FontWeight.W_500, color=C_TEXT)
    hex_prefix = ft.Text("#", color=C_MUTED)
    hex_field = ft.TextField(
        value="000000",
        prefix=hex_prefix,
        width=96,
        height=CHIP_HEX_H,
        text_size=12,
        border_radius=4,
        bgcolor=C_SURFACE,
        border_color=C_BORDER,
        focused_border_color=C_ACCENT,
        content_padding=ft.Padding(left=6, right=6),
        on_change=lambda e: on_hex_change(e),
        on_focus=on_text_focus_in,
        on_blur=on_text_focus_out,
    )
    border_hex_prefix = ft.Text("#", color=C_MUTED)
    border_hex_field = ft.TextField(
        value="000000",
        prefix=border_hex_prefix,
        width=96,
        height=CHIP_HEX_H,
        text_size=12,
        border_radius=4,
        bgcolor=C_SURFACE,
        border_color=C_BORDER,
        focused_border_color=C_ACCENT,
        content_padding=ft.Padding(left=6, right=6),
        on_change=lambda e: on_border_hex_change(e),
        on_focus=on_text_focus_in,
        on_blur=on_text_focus_out,
    )
    color_swatch = ft.Container(
        width=CHIP_SWATCH,
        height=CHIP_SWATCH,
        border_radius=4,
        bgcolor="#000000",
        border=ft.Border.all(1, C_BORDER),
        ink=True,
        tooltip="Open paint color picker",
        on_click=lambda e: open_color_picker("brush"),
    )
    outline_swatch = ft.Container(
        width=CHIP_SWATCH,
        height=CHIP_SWATCH,
        border_radius=4,
        bgcolor="#000000",
        border=ft.Border.all(1, C_BORDER),
        ink=True,
        tooltip="Open frame color picker",
        on_click=lambda e: open_color_picker("border"),
    )
    border_slider = ft.Slider(
        min=0,
        max=16,
        divisions=16,
        value=1,
        active_color=C_ACCENT,
        inactive_color=C_BORDER,
        on_change=lambda e: on_border_change(e),
    )
    alpha_slider = ft.Slider(
        min=0,
        max=255,
        divisions=255,
        value=255,
        active_color=C_ACCENT,
        inactive_color=C_BORDER,
        on_change=lambda e: on_alpha_change(e),
    )
    guides_switch = ft.Switch(
        value=True,
        active_color=C_ACCENT,
        inactive_thumb_color=C_MUTED,
        on_change=lambda e: on_guides_change(e),
    )
    debug_tile_ids_switch = ft.Switch(
        value=False,
        active_color=C_ACCENT,
        inactive_thumb_color=C_MUTED,
        on_change=lambda e: on_debug_tile_ids_change(e),
    )
    EXPORT_BTN_H = 38
    export_btn_style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=ft.Padding(left=10, right=10),
        text_style=ft.TextStyle(size=12),
    )
    new_texture_btn = ft.OutlinedButton(
        "New texture",
        icon=ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED,
        height=EXPORT_BTN_H,
        expand=True,
        style=export_btn_style,
        on_click=lambda e: page.run_task(pick_texture),
    )
    generate_btn = ft.FilledButton(
        "Generate pack",
        height=EXPORT_BTN_H,
        expand=True,
        disabled=True,
        style=export_btn_style,
        on_click=lambda e: page.run_task(generate_pack),
    )

    frame_color_btn = ft.IconButton(
        icon=ft.Icons.PALETTE_OUTLINED,
        icon_size=18,
        icon_color=C_MUTED,
        tooltip="Choose frame color",
        style=ICON_BTN_STYLE,
        on_click=lambda e: open_color_picker("border"),
    )
    frame_pick_btn = ft.IconButton(
        icon=ft.Icons.COLORIZE_OUTLINED,
        icon_size=18,
        icon_color=C_MUTED,
        tooltip="Sample frame color from preview",
        style=ICON_BTN_STYLE,
        on_click=lambda e: toggle_frame_pick(),
    )
    frame_color_actions = ft.Row(
        [frame_color_btn, frame_pick_btn],
        spacing=0,
        tight=True,
    )
    frame_color_chip = color_chip_row(
        outline_swatch,
        border_hex_field,
        trailing=frame_color_actions,
    )
    frame_color_label = ft.Text("Frame color", size=12, color=C_TEXT)
    width_label = ft.Text("Width", size=12, color=C_TEXT, width=64)
    opacity_label = ft.Text("Opacity", size=12, color=C_TEXT, width=64)
    guides_label = ft.Text("Guide lines", size=12, color=C_TEXT, expand=True)
    color_frame_panel = ft.Column(
        [
            frame_color_label,
            frame_color_chip,
            ft.Row(
                [
                    width_label,
                    ft.Container(content=border_slider, expand=True),
                    border_value,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    opacity_label,
                    ft.Container(content=alpha_slider, expand=True),
                    alpha_value,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    guides_label,
                    guides_switch,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        spacing=8,
        visible=True,
    )
    outline_section = ft.Column(
        spacing=6,
        visible=False,
        controls=[
            ft.OutlinedButton(
                "Choose PNG frame…",
                height=34,
                tooltip="PNG with only the border — transparent center, same size as texture",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    text_style=ft.TextStyle(size=12),
                ),
                on_click=lambda e: page.run_task(pick_outline),
            ),
        ],
    )
    zoom_slider = ft.Slider(
        min=0,
        max=1,
        divisions=ZOOM_SLIDER_DIVISIONS,
        value=0.5,
        active_color=C_ACCENT,
        inactive_color=C_BORDER,
        on_change=lambda e: on_zoom_change(e),
        on_change_end=lambda e: on_zoom_change_end(e),
    )
    apply_all_tiles_switch = ft.Switch(
        value=False,
        active_color=C_ACCENT,
        inactive_thumb_color=C_MUTED,
        on_change=lambda e: on_apply_all_tiles_change(e),
    )
    tolerance_value = ft.Text("32", size=12, color=C_MUTED)
    tolerance_slider = ft.Slider(
        min=0,
        max=255,
        divisions=51,
        value=32,
        active_color=C_ACCENT,
        inactive_color=C_BORDER,
        on_change=lambda e: on_tolerance_change(e),
    )
    tolerance_label = ft.Text("Tolerance", size=12, color=C_TEXT, expand=True)
    tolerance_section = ft.Column(
        spacing=4,
        visible=False,
        controls=[
            ft.Row(
                [
                    tolerance_label,
                    tolerance_value,
                ],
            ),
            tolerance_slider,
        ],
    )
    paint_pick_btn = ft.IconButton(
        icon=ft.Icons.COLORIZE_OUTLINED,
        icon_size=17,
        icon_color=C_MUTED,
        tooltip="Pick color from texture",
        width=36,
        height=36,
        style=ICON_BTN_STYLE,
        on_click=lambda e: toggle_paint_pick(),
    )
    paint_brush_btn = ft.IconButton(
        icon=ft.Icons.BRUSH_OUTLINED,
        icon_size=17,
        icon_color=C_MUTED,
        tooltip="Paint on texture",
        width=36,
        height=36,
        style=ICON_BTN_STYLE,
        on_click=lambda e: toggle_brush(),
    )
    paint_fill_btn = ft.IconButton(
        icon=ft.Icons.FORMAT_COLOR_FILL,
        icon_size=17,
        icon_color=C_MUTED,
        tooltip="Fill area with paint color",
        width=36,
        height=36,
        style=ICON_BTN_STYLE,
        on_click=lambda e: toggle_fill(),
    )
    paint_edit_bar = ft.Container(
        border=ft.Border.all(1, C_BORDER),
        border_radius=8,
        bgcolor=C_CHIP,
        padding=ft.Padding(left=8, right=8, top=6, bottom=6),
        content=ft.Row(
            [
                color_swatch,
                hex_field,
                chip_divider(),
                paint_pick_btn,
                paint_brush_btn,
                paint_fill_btn,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    paint_tool_hint = ft.Text(
        "",
        size=11,
        color=C_ACCENT,
        visible=False,
    )
    edit_texture_title = ft.Text(
        "Edit texture",
        size=13,
        weight=ft.FontWeight.W_600,
        color=C_TEXT,
    )
    paint_toolbar = ft.Container(
        visible=False,
        bgcolor=C_SURFACE,
        border_radius=10,
        padding=ft.Padding(left=14, right=14, top=10, bottom=10),
        content=ft.Column(
            [
                ft.Row(
                    [
                        edit_texture_title,
                        paint_tool_hint,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                paint_edit_bar,
                tolerance_section,
            ],
            spacing=8,
        ),
    )
    undo_btn = ft.IconButton(
        icon=ft.Icons.UNDO,
        icon_size=18,
        icon_color=C_MUTED,
        disabled=True,
        tooltip="Undo (Ctrl+Z)",
        style=ft.ButtonStyle(
            padding=4,
            shape=ft.RoundedRectangleBorder(radius=6),
        ),
        on_click=lambda e: undo_edit(),
    )
    redo_btn = ft.IconButton(
        icon=ft.Icons.REDO,
        icon_size=18,
        icon_color=C_MUTED,
        disabled=True,
        tooltip="Redo (Ctrl+Y)",
        style=ft.ButtonStyle(
            padding=4,
            shape=ft.RoundedRectangleBorder(radius=6),
        ),
        on_click=lambda e: redo_edit(),
    )
    mode_color_text = ft.Text(
        "Colored frame",
        size=11,
        weight=ft.FontWeight.W_500,
        color=C_ON_ACCENT,
        text_align=ft.TextAlign.CENTER,
    )
    mode_png_text = ft.Text(
        "Custom PNG",
        size=11,
        color=C_MUTED,
        text_align=ft.TextAlign.CENTER,
    )
    mode_color_tab = ft.Container(
        expand=True,
        height=34,
        border_radius=6,
        bgcolor=C_ACCENT,
        alignment=ft.Alignment(0, 0),
        ink=True,
        on_click=lambda e: set_border_mode("color"),
        content=mode_color_text,
    )
    mode_png_tab = ft.Container(
        expand=True,
        height=34,
        border_radius=6,
        alignment=ft.Alignment(0, 0),
        ink=True,
        on_click=lambda e: set_border_mode("outline"),
        content=mode_png_text,
    )
    mode_selector = ft.Container(
        border=ft.Border.all(1, C_BORDER),
        border_radius=8,
        bgcolor=C_CHIP,
        padding=ft.Padding(left=3, right=3, top=3, bottom=3),
        content=ft.Row(
            [mode_color_tab, mode_png_tab],
            spacing=4,
        ),
    )

    def set_status(message):
        if message:
            preview_meta.value = message
        elif engine.base_image:
            preview_meta.value = (
                f"Tile {engine.preview_tile:02d} of 46  ·  "
                f"{engine.base_image.size[0]}×{engine.base_image.size[1]}"
            )
        else:
            preview_meta.value = ""
        safe_page_update(preview_meta)

    def show_toast(message, *, error=False, duration=None):
        if not message:
            status_toast.value = ""
            page.update(status_toast)
            return
        if duration is None:
            duration = 3.0 if error else 2.2
        toast_token["id"] += 1
        token = toast_token["id"]
        status_toast.value = message
        status_toast.color = "#f87171" if error else C_ACCENT
        page.update(status_toast)

        async def hide_toast():
            await asyncio.sleep(duration)
            if toast_token["id"] != token:
                return
            status_toast.value = ""
            safe_page_update(status_toast)

        page.run_task(hide_toast)

    def push_draw_preview(force=False):
        if engine.base_image is None:
            return
        now = time.monotonic()
        if not force and now - draw_update_clock["t"] < 0.016:
            return
        draw_update_clock["t"] = now
        repaint_preview(live=True)
        safe_page_update(preview_image, preview_tile_layer)

    def center_preview_surface():
        if engine.base_image is None:
            return
        engine.set_preview_viewport(preview_viewport["w"], preview_viewport["h"])
        engine.center_view()
        sync_preview_tile_layer()

    def refresh_preview():
        if engine.base_image is None:
            if preview_has_texture["active"]:
                preview_has_texture["active"] = False
                preview_surface.content = ft.Container(
                    content=empty_state,
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    on_size_change=on_preview_resize,
                )
            preview_meta.value = ""
            paint_toolbar.visible = False
            safe_page_update(
                preview_surface, preview_meta, paint_toolbar, preview_title
            )
            return

        layout_changed = False
        if not preview_has_texture["active"]:
            preview_has_texture["active"] = True
            preview_surface.content = ft.Container(
                content=preview_gesture,
                expand=True,
                on_size_change=on_preview_resize,
            )
            paint_toolbar.visible = True
            layout_changed = True

        tile_idx = repaint_preview()
        preview_title.value = "Preview"
        preview_meta.value = (
            f"Tile {tile_idx:02d} of 46  ·  "
            f"{engine.base_image.size[0]}×{engine.base_image.size[1]}"
        )
        tile_value.value = f"{tile_idx:02d} / 46"
        controls = [
            preview_image,
            preview_tile_layer,
            preview_meta,
            preview_title,
            tile_value,
            paint_toolbar,
        ]
        if layout_changed:
            controls.insert(0, preview_surface)
        safe_page_update(*controls)
        if layout_changed:
            page.run_task(remeasure_preview)

    def on_preview_resize(e: ft.LayoutSizeChangeEvent):
        w = sanitize_viewport_dim(e.width, 800)
        h = sanitize_viewport_dim(e.height, 600)
        changed = w != preview_viewport["w"] or h != preview_viewport["h"]
        preview_viewport["w"] = w
        preview_viewport["h"] = h
        engine.set_preview_viewport(w, h)
        if engine.base_image is None:
            return
        repaint_preview()
        sync_preview_tile_layer()
        if changed:
            safe_page_update(preview_image, preview_tile_layer)

    def on_page_resize(_=None):
        page.run_task(remeasure_preview)

    def on_hex_change(e):
        if syncing_hex["active"]:
            return
        value = (e.control.value or "").strip().lstrip("#")
        if len(value) not in (3, 4, 6, 8) or not all(
            c in "0123456789abcdefABCDEF" for c in value
        ):
            return
        try:
            old_color = engine.brush_color
            old_alpha = int(engine.brush_alpha)
            hex_value, alpha = engine.set_brush_color(value)
            if (engine.brush_color, int(engine.brush_alpha)) != (old_color, old_alpha):
                if not edit_history["applying"]:
                    push_undo_color("brush")
            syncing_hex["active"] = True
            hex_field.value = hex_value[1:].upper() + (
                f"{alpha:02X}" if alpha is not None else ""
            )
            syncing_hex["active"] = False
            color_swatch.bgcolor = ft.Colors.with_opacity(
                int(engine.brush_alpha) / 255, hex_value
            )
            if alpha is not None:
                engine.brush_alpha = alpha
            safe_page_update(color_swatch, hex_field)
            refresh_preview()
        except ValueError:
            pass

    def on_border_hex_change(e):
        if syncing_border_hex["active"]:
            return
        value = (e.control.value or "").strip().lstrip("#")
        if len(value) not in (3, 4, 6, 8) or not all(
            c in "0123456789abcdefABCDEF" for c in value
        ):
            return
        try:
            old_color = engine.border_color
            old_alpha = int(engine.border_alpha)
            hex_value, alpha = engine.set_border_color(value)
            if (engine.border_color, int(engine.border_alpha)) != (
                old_color,
                old_alpha,
            ):
                if not edit_history["applying"]:
                    push_undo_color("border")
            syncing_border_hex["active"] = True
            border_hex_field.value = hex_value[1:].upper() + (
                f"{alpha:02X}" if alpha is not None else ""
            )
            syncing_border_hex["active"] = False
            outline_swatch.bgcolor = ft.Colors.with_opacity(
                int(engine.border_alpha) / 255, hex_value
            )
            if alpha is not None:
                engine.border_alpha = alpha
                alpha_slider.value = alpha
                set_alpha_value_display(alpha)
            engine.invalidate_border_cache()
            safe_page_update(
                outline_swatch, border_hex_field, alpha_slider, alpha_value
            )
            refresh_preview()
        except ValueError:
            pass

    def apply_brush_color(hex_value, alpha=None):
        edit_history["applying"] = True
        syncing_hex["active"] = True
        hex_field.value = hex_value[1:].upper()
        syncing_hex["active"] = False
        a = int(alpha if alpha is not None else engine.brush_alpha)
        color_swatch.bgcolor = ft.Colors.with_opacity(a / 255, hex_value)
        if alpha is not None:
            engine.brush_alpha = alpha
        edit_history["applying"] = False
        safe_page_update(color_swatch, hex_field)

    def apply_border_color(hex_value, alpha=None):
        syncing_border_hex["active"] = True
        border_hex_field.value = hex_value[1:].upper()
        syncing_border_hex["active"] = False
        a = int(alpha if alpha is not None else engine.border_alpha)
        outline_swatch.bgcolor = ft.Colors.with_opacity(a / 255, hex_value)
        if alpha is not None:
            alpha_slider.value = alpha
            engine.border_alpha = alpha
            set_alpha_value_display(alpha)
        safe_page_update(outline_swatch, border_hex_field, alpha_slider, alpha_value)

    def apply_sampled_color(hex_raw, target):
        rgb, alpha = parse_hex_color(hex_raw)
        push_undo_color(target)
        if target == "border":
            engine.set_border_color(rgb)
            if alpha is not None:
                engine.border_alpha = alpha
            apply_border_color(rgb_to_hex(engine.border_color), engine.border_alpha)
        else:
            engine.set_brush_color(rgb)
            if alpha is not None:
                engine.brush_alpha = alpha
            apply_brush_color(rgb_to_hex(engine.brush_color), engine.brush_alpha)
        refresh_preview()

    def sync_history_buttons():
        can_undo = bool(edit_history["undo"])
        can_redo = bool(edit_history["redo"])
        undo_btn.disabled = not can_undo
        redo_btn.disabled = not can_redo
        undo_btn.icon_color = C_TEXT if can_undo else C_MUTED
        redo_btn.icon_color = C_TEXT if can_redo else C_MUTED
        page.update(undo_btn, redo_btn)

    def push_undo_image():
        if edit_history["applying"] or engine.base_image is None:
            return
        if engine.apply_all_tiles:
            edit_history["undo"].append(
                {"kind": "image", "scope": "all", "before": engine.base_image.copy()}
            )
        else:
            idx = engine.preview_tile
            before = (
                engine.tile_bases[idx].copy() if idx in engine.tile_bases else None
            )
            edit_history["undo"].append(
                {"kind": "image", "scope": "tile", "tile": idx, "before": before}
            )
        edit_history["redo"].clear()
        if len(edit_history["undo"]) > MAX_UNDO:
            edit_history["undo"].pop(0)
        sync_history_buttons()

    def _capture_image_state(scope, tile_idx=None):
        if scope == "all":
            return {
                "kind": "image",
                "scope": "all",
                "before": engine.base_image.copy(),
            }
        idx = tile_idx if tile_idx is not None else engine.preview_tile
        before = engine.tile_bases[idx].copy() if idx in engine.tile_bases else None
        return {"kind": "image", "scope": "tile", "tile": idx, "before": before}

    def _restore_image_undo(entry):
        if entry.get("scope") == "tile":
            idx = entry["tile"]
            if entry["before"] is None:
                engine.tile_bases.pop(idx, None)
            else:
                engine.tile_bases[idx] = entry["before"].copy()
        else:
            engine.base_image = entry["before"].copy()
            engine.clear_tile_bases()

    def _color_snapshot(target):
        if target == "border":
            return (engine.border_color, int(engine.border_alpha))
        return (engine.brush_color, int(engine.brush_alpha))

    def _restore_color_snapshot(target, color, alpha):
        if target == "border":
            engine.border_color = color
            engine.border_alpha = alpha
            engine.invalidate_border_cache()
            apply_border_color(rgb_to_hex(color), alpha)
        else:
            engine.brush_color = color
            engine.brush_alpha = alpha
            apply_brush_color(rgb_to_hex(color), alpha)

    def push_undo_color(target="brush"):
        if edit_history["applying"]:
            return
        edit_history["undo"].append(
            {
                "kind": "color",
                "target": target,
                "before": _color_snapshot(target),
            }
        )
        edit_history["redo"].clear()
        if len(edit_history["undo"]) > MAX_UNDO:
            edit_history["undo"].pop(0)
        sync_history_buttons()

    def undo_edit():
        if not edit_history["undo"]:
            return
        entry = edit_history["undo"].pop()
        edit_history["applying"] = True
        if entry["kind"] == "image" and engine.base_image is not None:
            edit_history["redo"].append(
                _capture_image_state(entry.get("scope"), entry.get("tile"))
            )
            _restore_image_undo(entry)
            if entry.get("scope") == "tile" and entry.get("tile") is not None:
                engine.preview_tile = entry["tile"]
            refresh_preview()
            set_status("Undid draw stroke")
        elif entry["kind"] == "color":
            target = entry.get("target", "brush")
            edit_history["redo"].append(
                {
                    "kind": "color",
                    "target": target,
                    "before": _color_snapshot(target),
                }
            )
            color, alpha = entry["before"]
            _restore_color_snapshot(target, color, alpha)
            refresh_preview()
            set_status(
                "Undid outline color change"
                if target == "border"
                else "Undid draw color change"
            )
        edit_history["applying"] = False
        sync_history_buttons()

    def redo_edit():
        if not edit_history["redo"]:
            return
        entry = edit_history["redo"].pop()
        edit_history["applying"] = True
        if entry["kind"] == "image" and engine.base_image is not None:
            edit_history["undo"].append(
                _capture_image_state(entry.get("scope"), entry.get("tile"))
            )
            _restore_image_undo(entry)
            if entry.get("scope") == "tile" and entry.get("tile") is not None:
                engine.preview_tile = entry["tile"]
            refresh_preview()
            set_status("Redid draw stroke")
        elif entry["kind"] == "color":
            target = entry.get("target", "brush")
            edit_history["undo"].append(
                {
                    "kind": "color",
                    "target": target,
                    "before": _color_snapshot(target),
                }
            )
            color, alpha = entry["before"]
            _restore_color_snapshot(target, color, alpha)
            refresh_preview()
            set_status(
                "Redid outline color change"
                if target == "border"
                else "Redid draw color change"
            )
        edit_history["applying"] = False
        sync_history_buttons()

    def focus_preview_keyboard():
        listener = preview_keyboard_listener["control"]
        if listener is None:
            return

        async def _focus():
            await listener.focus()

        page.run_task(_focus)

    page.on_keyboard_event = lambda e: None

    async def warm_picker_cache(_=None):
        get_hue_strip_src()
        get_checker_preview_src()
        for h in range(0, 360, 4):
            get_sv_plane_src(h)
            if h % 24 == 0:
                await asyncio.sleep(0)

    def open_color_picker(target="brush"):
        picker_target["value"] = target
        page.run_task(show_color_picker_dialog)

    async def show_color_picker_dialog(_=None):
        target = picker_target["value"]
        if target == "border":
            r, g, b = engine.border_color
            a0 = int(engine.border_alpha)
            picker_title = "Pick outline color"
            opacity_label = "Outline opacity"
        else:
            r, g, b = engine.brush_color
            a0 = int(engine.brush_alpha)
            picker_title = "Pick paint color"
            opacity_label = "Draw opacity"
        h0, s0, v0 = rgb_to_hsv255((r, g, b))
        picker_sync = {"active": False}
        picker_state = {"h": h0, "s": s0, "v": v0, "a": a0}
        last_sv_hue = {"h": int(round(h0)) % 360}
        update_clock = {"t": 0.0}

        picker_swatch_color = ft.Container(
            expand=True,
            bgcolor=ft.Colors.with_opacity(a0 / 255, rgb_to_hex((r, g, b))),
        )
        picker_swatch = ft.Container(
            width=PICKER_SWATCH,
            height=PICKER_SWATCH,
            shape=ft.BoxShape.CIRCLE,
            border=ft.Border.all(2, C_BORDER),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack(
                [
                    ft.Image(
                        src=get_checker_preview_src(),
                        expand=True,
                        fit=ft.BoxFit.COVER,
                    ),
                    picker_swatch_color,
                ],
            ),
        )
        sv_image = ft.Image(
            src=get_sv_plane_src(h0),
            width=PICKER_W,
            height=SV_PLANE_H,
            fit=ft.BoxFit.FILL,
            gapless_playback=True,
        )
        hue_image = ft.Image(
            src=get_hue_strip_src(),
            width=PICKER_SLIDER_W,
            height=PICKER_STRIP_H,
            fit=ft.BoxFit.FILL,
            gapless_playback=True,
        )
        alpha_image = ft.Image(
            src=get_alpha_strip_src((r, g, b)),
            width=PICKER_SLIDER_W,
            height=ALPHA_STRIP_H,
            fit=ft.BoxFit.FILL,
            gapless_playback=True,
        )
        sv_marker = ft.Container(
            width=12,
            height=12,
            border_radius=6,
            border=ft.Border.all(2, "#FFFFFF"),
            bgcolor=ft.Colors.with_opacity(0.15, "#000000"),
            left=max(0, min(PICKER_W - 12, s0 / 100 * PICKER_W - 6)),
            top=max(0, min(SV_PLANE_H - 12, (1 - v0 / 100) * SV_PLANE_H - 6)),
        )
        hue_pad = picker_track_pad(PICKER_STRIP_H)
        hue_marker = make_picker_marker(
            picker_marker_left(h0 / 360, PICKER_SLIDER_W),
            hue_pad + (PICKER_STRIP_H - PICKER_MARKER) // 2,
        )
        alpha_pad = picker_track_pad(ALPHA_STRIP_H)
        alpha_marker = make_picker_marker(
            picker_marker_left(a0 / 255, PICKER_SLIDER_W),
            alpha_pad + (ALPHA_STRIP_H - PICKER_MARKER) // 2,
        )
        picker_hex = ft.TextField(
            value=f"{r:02X}{g:02X}{b:02X}",
            prefix=ft.Text("#", color=C_MUTED),
            width=108,
            height=32,
            text_size=13,
            border_radius=8,
            bgcolor=C_SURFACE,
            border_color=C_BORDER,
            focused_border_color=C_ACCENT,
            content_padding=ft.Padding(left=8, right=8),
        )

        def picker_rgb():
            return hsv255_to_rgb(
                picker_state["h"], picker_state["s"], picker_state["v"]
            )

        def refresh_swatch_preview():
            cr, cg, cb = picker_rgb()
            hex_val = rgb_to_hex((cr, cg, cb))
            picker_swatch_color.bgcolor = ft.Colors.with_opacity(
                picker_state["a"] / 255, hex_val
            )

        def refresh_picker_preview(update_alpha_strip=True):
            cr, cg, cb = picker_rgb()
            hex_val = rgb_to_hex((cr, cg, cb))
            alpha = picker_state["a"] / 255
            picker_swatch_color.bgcolor = ft.Colors.with_opacity(alpha, hex_val)
            if update_alpha_strip:
                alpha_image.src = get_alpha_strip_src((cr, cg, cb))
            if not picker_sync["active"]:
                picker_sync["active"] = True
                picker_hex.value = hex_val[1:].upper()
                picker_sync["active"] = False

        def update_sv_marker():
            sv_marker.left = max(
                0, min(PICKER_W - 12, picker_state["s"] / 100 * PICKER_W - 6)
            )
            sv_marker.top = max(
                0,
                min(SV_PLANE_H - 12, (1 - picker_state["v"] / 100) * SV_PLANE_H - 6),
            )

        def update_hue_marker():
            hue_marker.left = picker_marker_left(
                picker_state["h"] / 360, PICKER_SLIDER_W
            )

        def update_alpha_marker():
            alpha_marker.left = picker_marker_left(
                picker_state["a"] / 255, PICKER_SLIDER_W
            )

        def update_sv_plane_if_needed(force=False):
            key = int(round(picker_state["h"])) % 360
            if not force and key == last_sv_hue["h"]:
                return False
            last_sv_hue["h"] = key
            sv_image.src = get_sv_plane_src(key)
            return True

        def picker_ui_update(*controls, force=False):
            now = time.monotonic()
            if not force and now - update_clock["t"] < 0.045:
                return
            update_clock["t"] = now
            if controls:
                page.update(*controls)
            else:
                page.update()

        def set_sv_from_pos(x, y, force=False):
            picker_state["s"] = max(0, min(100, round(x / PICKER_W * 100)))
            picker_state["v"] = max(0, min(100, round((1 - y / SV_PLANE_H) * 100)))
            update_sv_marker()
            refresh_swatch_preview()
            if force:
                refresh_picker_preview()
                picker_ui_update(
                    sv_marker,
                    picker_swatch_color,
                    alpha_image,
                    picker_hex,
                    force=True,
                )
            else:
                picker_ui_update(sv_marker, picker_swatch_color)

        def set_hue_from_pos(x, force=False):
            picker_state["h"] = max(0, min(360, round(x / PICKER_SLIDER_W * 360)))
            update_hue_marker()
            refresh_swatch_preview()
            if force:
                update_sv_plane_if_needed(force=True)
                refresh_picker_preview()
                picker_ui_update(
                    hue_marker,
                    picker_swatch_color,
                    alpha_image,
                    picker_hex,
                    sv_image,
                    force=True,
                )
            else:
                picker_ui_update(hue_marker, picker_swatch_color)

        def set_alpha_from_pos(x, force=False):
            picker_state["a"] = max(0, min(255, round(x / PICKER_SLIDER_W * 255)))
            update_alpha_marker()
            refresh_swatch_preview()
            picker_ui_update(alpha_marker, picker_swatch_color, force=force)

        def on_sv_interact(e):
            if e.local_position is None:
                return
            set_sv_from_pos(e.local_position.x, e.local_position.y)

        def on_sv_interact_end(_):
            refresh_picker_preview()
            picker_ui_update(
                sv_marker,
                picker_swatch_color,
                alpha_image,
                picker_hex,
                force=True,
            )

        def on_hue_interact(e):
            if e.local_position is None:
                return
            set_hue_from_pos(e.local_position.x)

        def on_hue_interact_end(_):
            update_sv_plane_if_needed(force=True)
            refresh_picker_preview()
            picker_ui_update(
                hue_marker,
                picker_swatch_color,
                alpha_image,
                picker_hex,
                sv_image,
                force=True,
            )

        def on_alpha_interact(e):
            if e.local_position is None:
                return
            set_alpha_from_pos(e.local_position.x)

        def on_alpha_interact_end(_):
            refresh_swatch_preview()
            picker_ui_update(alpha_marker, picker_swatch_color, force=True)

        def on_picker_hex_change(e):
            if picker_sync["active"]:
                return
            value = (e.control.value or "").strip().lstrip("#")
            if len(value) != 6 or not all(
                c in "0123456789abcdefABCDEF" for c in value
            ):
                return
            try:
                rgb, _ = parse_hex_color(value)
                picker_sync["active"] = True
                hh, ss, vv = rgb_to_hsv255(rgb)
                picker_state["h"] = hh
                picker_state["s"] = ss
                picker_state["v"] = vv
                picker_sync["active"] = False
                update_sv_plane_if_needed(force=True)
                update_sv_marker()
                update_hue_marker()
                refresh_picker_preview()
                picker_ui_update(
                    sv_image,
                    sv_marker,
                    hue_marker,
                    picker_swatch_color,
                    alpha_image,
                    force=True,
                )
            except ValueError:
                pass

        def pick_preset(hex_color):
            rgb, _ = parse_hex_color(hex_color.lstrip("#"))
            picker_sync["active"] = True
            hh, ss, vv = rgb_to_hsv255(rgb)
            picker_state["h"] = hh
            picker_state["s"] = ss
            picker_state["v"] = vv
            picker_sync["active"] = False
            update_sv_plane_if_needed(force=True)
            update_sv_marker()
            update_hue_marker()
            refresh_picker_preview()
            picker_ui_update(
                sv_image,
                sv_marker,
                hue_marker,
                picker_swatch_color,
                alpha_image,
                picker_hex,
                force=True,
            )

        picker_hex.on_change = on_picker_hex_change

        sv_field = ft.GestureDetector(
            on_tap_down=on_sv_interact,
            on_pan_update=on_sv_interact,
            on_pan_end=on_sv_interact_end,
            content=ft.Container(
                width=PICKER_W,
                height=SV_PLANE_H,
                border_radius=8,
                border=ft.Border.all(1, C_BORDER),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=ft.Stack(
                    width=PICKER_W,
                    height=SV_PLANE_H,
                    controls=[sv_image, sv_marker],
                ),
            ),
        )
        hue_field = make_picker_strip_field(
            hue_image,
            hue_marker,
            PICKER_SLIDER_W,
            PICKER_STRIP_H,
            on_hue_interact,
            on_hue_interact,
            on_hue_interact_end,
        )
        alpha_field = make_picker_strip_field(
            alpha_image,
            alpha_marker,
            PICKER_SLIDER_W,
            ALPHA_STRIP_H,
            on_alpha_interact,
            on_alpha_interact,
            on_alpha_interact_end,
        )

        preset_row = ft.Row(
            wrap=True,
            spacing=6,
            run_spacing=6,
            controls=[
                ft.Container(
                    width=24,
                    height=24,
                    border_radius=6,
                    bgcolor=color,
                    border=ft.Border.all(1, C_BORDER),
                    ink=True,
                    on_click=lambda e, c=color: pick_preset(c),
                )
                for color in PRESET_COLORS
            ],
        )

        def apply_picker_color(_=None):
            cr, cg, cb = picker_rgb()
            new_color = (cr, cg, cb)
            new_alpha = picker_state["a"]
            if target == "border":
                if (new_color, new_alpha) != (
                    engine.border_color,
                    int(engine.border_alpha),
                ):
                    push_undo_color("border")
                engine.set_border_color(new_color)
                engine.border_alpha = new_alpha
                apply_border_color(rgb_to_hex(engine.border_color), engine.border_alpha)
            else:
                if (new_color, new_alpha) != (
                    engine.brush_color,
                    int(engine.brush_alpha),
                ):
                    push_undo_color("brush")
                engine.set_brush_color(new_color)
                engine.brush_alpha = new_alpha
                apply_brush_color(rgb_to_hex(engine.brush_color), engine.brush_alpha)
            page.pop_dialog()
            refresh_preview()

        def close_picker(_=None):
            page.pop_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=C_SURFACE,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Text(picker_title, size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                width=PICKER_W + 8,
                padding=ft.Padding(left=4, right=4, top=0, bottom=0),
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        sv_field,
                        ft.Row(
                            [
                                picker_swatch,
                                ft.Column(
                                    spacing=6,
                                    expand=True,
                                    controls=[
                                        hue_field,
                                        ft.Text(
                                            opacity_label,
                                            size=11,
                                            color=C_MUTED,
                                        ),
                                        alpha_field,
                                    ],
                                ),
                            ],
                            spacing=12,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        picker_hex,
                        preset_row,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=close_picker),
                ft.FilledButton("Apply", on_click=apply_picker_color),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        get_sv_plane_src(h0)
        page.show_dialog(dialog)

    def set_border_width_display(width):
        syncing_border_value["active"] = True
        border_value.value = str(int(width))
        syncing_border_value["active"] = False

    def set_alpha_value_display(alpha):
        syncing_alpha_value["active"] = True
        alpha_value.value = str(int(alpha))
        syncing_alpha_value["active"] = False

    def border_width_limits():
        max_width = engine.ui_border_width_max()
        return 0, max_width

    def apply_border_width(width):
        min_w, max_w = border_width_limits()
        if engine.base_image:
            border_slider.max = max_w
            border_slider.divisions = border_slider_divisions(max_w)
        width = max(min_w, min(max_w, int(round(width))))
        engine.border_width = width
        engine.invalidate_border_cache()
        border_slider.value = width
        set_border_width_display(width)
        page.update(border_slider, border_value)
        refresh_preview()

    def apply_border_alpha(alpha):
        alpha = max(0, min(255, int(round(alpha))))
        engine.border_alpha = alpha
        engine.invalidate_border_cache()
        alpha_slider.value = alpha
        set_alpha_value_display(alpha)
        outline_swatch.bgcolor = ft.Colors.with_opacity(
            alpha / 255,
            rgb_to_hex(engine.border_color),
        )
        page.update(alpha_slider, alpha_value, outline_swatch)
        refresh_preview()

    def on_border_value_commit(_=None):
        if syncing_border_value["active"]:
            return
        try:
            text = (border_value.value or "").strip().lower().replace("px", "").strip()
            apply_border_width(int(text))
        except ValueError:
            set_border_width_display(engine.border_width)
            page.update(border_value)

    def on_alpha_value_commit(_=None):
        if syncing_alpha_value["active"]:
            return
        try:
            apply_border_alpha(int((alpha_value.value or "").strip()))
        except ValueError:
            set_alpha_value_display(engine.border_alpha)
            page.update(alpha_value)

    border_value.on_submit = on_border_value_commit

    def on_border_value_blur(e):
        on_text_focus_out(e)
        on_border_value_commit()

    def on_alpha_value_blur(e):
        on_text_focus_out(e)
        on_alpha_value_commit()

    border_value.on_blur = on_border_value_blur
    border_value.on_focus = on_text_focus_in
    alpha_value.on_submit = on_alpha_value_commit
    alpha_value.on_blur = on_alpha_value_blur
    alpha_value.on_focus = on_text_focus_in

    def sync_border_ui():
        border_slider.value = engine.border_width
        set_border_width_display(engine.border_width)

    def on_border_change(e):
        apply_border_width(e.control.value)

    def on_alpha_change(e):
        apply_border_alpha(e.control.value)

    alpha_slider.on_change_start = lambda e: push_undo_color("border")

    def zoom_from_slider_pos(pos):
        fit = fit_zoom_for_texture()
        pct = ZOOM_PERCENT_MIN + float(pos) * (
            ZOOM_PERCENT_MAX - ZOOM_PERCENT_MIN
        )
        min_z = fit * (ZOOM_PERCENT_MIN / 100)
        max_z = fit * (ZOOM_PERCENT_MAX / 100)
        zoom = fit * (pct / 100.0)
        return max(min_z, min(max_z, zoom))

    def slider_pos_from_zoom(zoom):
        fit = fit_zoom_for_texture()
        if fit <= 0:
            return 0.0
        pct = (zoom / fit) * 100
        pct = max(ZOOM_PERCENT_MIN, min(ZOOM_PERCENT_MAX, pct))
        return (pct - ZOOM_PERCENT_MIN) / (ZOOM_PERCENT_MAX - ZOOM_PERCENT_MIN)

    def zoom_percent_from_zoom(zoom):
        fit = fit_zoom_for_texture()
        if fit <= 0:
            return ZOOM_PERCENT_FIT
        pct = round((zoom / fit) * 100)
        return max(ZOOM_PERCENT_MIN, min(ZOOM_PERCENT_MAX, pct))

    def zoom_from_percent(percent):
        fit = fit_zoom_for_texture()
        percent = max(ZOOM_PERCENT_MIN, min(ZOOM_PERCENT_MAX, percent))
        return fit * (percent / 100.0)

    def zoom_limits_and_step():
        fit = fit_zoom_for_texture()
        min_z = fit * (ZOOM_PERCENT_MIN / 100)
        max_z = fit * (ZOOM_PERCENT_MAX / 100)
        step = zoom_step_for_span(max_z - min_z)
        return min_z, max_z, step, fit

    def fit_zoom_for_texture():
        if engine.base_image is None:
            return DEFAULT_PREVIEW_ZOOM
        tex_w, tex_h = engine.base_image.size
        vw = max(engine.preview_viewport_w, preview_viewport["w"], 200)
        vh = max(engine.preview_viewport_h, preview_viewport["h"], 200)
        fit = min(
            vw / (tex_w * PREVIEW_TEXEL_SCALE),
            vh / (tex_h * PREVIEW_TEXEL_SCALE),
        )
        return max(0.01, fit)

    def zoom_limits_for_texture():
        fit = fit_zoom_for_texture()
        min_z = fit * (ZOOM_PERCENT_MIN / 100)
        max_z = fit * (ZOOM_PERCENT_MAX / 100)
        return min_z, max(min_z, max_z)

    def update_zoom_slider_range():
        if engine.base_image is None:
            return
        syncing_zoom["active"] = True
        zoom_slider.value = slider_pos_from_zoom(engine.zoom)
        syncing_zoom["active"] = False

    def format_zoom(value):
        return f"{zoom_percent_from_zoom(value)}%"

    def sync_zoom_ui(update_slider=True):
        min_z, max_z, _step, _fit = zoom_limits_and_step()
        engine.zoom = max(min_z, min(max_z, engine.zoom))
        syncing_zoom["active"] = True
        update_zoom_slider_range()
        if update_slider:
            zoom_slider.value = slider_pos_from_zoom(engine.zoom)
        zoom_value.value = format_zoom(engine.zoom)
        syncing_zoom["active"] = False
        controls = [zoom_value]
        if update_slider:
            controls.append(zoom_slider)
        page.update(*controls)

    def reset_preview_zoom():
        if engine.base_image:
            engine.zoom = fit_zoom_for_texture()
            center_preview_in_viewport()
        else:
            engine.zoom = snap_zoom(DEFAULT_PREVIEW_ZOOM)
        sync_zoom_ui()

    def preview_center():
        return engine.preview_viewport_w / 2, engine.preview_viewport_h / 2

    def set_preview_zoom(new_zoom, focal_x, focal_y):
        min_z, max_z = zoom_limits_for_texture()
        engine.apply_zoom_at(new_zoom, focal_x, focal_y, max_zoom=max_z, min_zoom=min_z)

    def refresh_zoom_preview(live=False):
        if engine.base_image is None:
            return
        if live:
            now = time.monotonic()
            if now - zoom_update_clock["t"] < 0.04:
                return
            zoom_update_clock["t"] = now
        repaint_preview(live=live)
        safe_page_update(preview_image, preview_tile_layer)

    def schedule_zoom_finalize():
        zoom_finalize_token["id"] += 1
        token = zoom_finalize_token["id"]

        async def finalize(_=None):
            await asyncio.sleep(0.12)
            if zoom_finalize_token["id"] == token and engine.base_image is not None:
                try:
                    refresh_zoom_preview(live=False)
                except RuntimeError:
                    pass

        page.run_task(finalize)

    def on_zoom_change(e):
        if syncing_zoom["active"]:
            return
        cx, cy = preview_center()
        set_preview_zoom(zoom_from_slider_pos(e.control.value), cx, cy)
        zoom_value.value = format_zoom(engine.zoom)
        page.update(zoom_value)
        refresh_zoom_preview(live=True)
        schedule_zoom_finalize()

    def on_zoom_change_end(e):
        if syncing_zoom["active"]:
            return
        cx, cy = preview_center()
        set_preview_zoom(zoom_from_slider_pos(e.control.value), cx, cy)
        engine.center_view()
        sync_zoom_ui()
        refresh_zoom_preview(live=False)

    def on_preview_scroll(e: ft.ScrollEvent):
        if syncing_zoom["active"] or engine.base_image is None:
            return
        focus_preview_keyboard()
        if not ctrl_tracker.pressed:
            return
        if drawing_state["active"] and drawing_state["undo_snapshotted"]:
            return

        dy = float(e.scroll_delta.y or 0)
        if abs(dy) < 1e-6:
            dx = float(e.scroll_delta.x or 0)
            if abs(dx) < 1e-6:
                return
            dy = dx

        if e.local_position is not None:
            focal_x, focal_y = e.local_position.x, e.local_position.y
        else:
            focal_x, focal_y = preview_center()

        pct = zoom_percent_from_zoom(engine.zoom)
        zoom_in = scroll_wheel_zooms_in(dy)
        next_pct = pct + (ZOOM_SCROLL_STEP if zoom_in else -ZOOM_SCROLL_STEP)
        if next_pct == pct:
            return

        new_zoom = zoom_from_percent(next_pct)
        set_preview_zoom(new_zoom, focal_x, focal_y)
        sync_zoom_ui()
        refresh_zoom_preview(live=True)
        schedule_zoom_finalize()

    def on_guides_change(e):
        engine.show_guides = e.control.value
        refresh_preview()

    def on_debug_tile_ids_change(e):
        engine.debug_tile_labels = e.control.value
        refresh_preview()

    def sync_border_mode_ui():
        color_active = not engine.use_custom_outline
        mode_color_tab.bgcolor = C_ACCENT if color_active else None
        mode_png_tab.bgcolor = C_ACCENT if not color_active else None
        if color_active:
            mode_color_text.color = C_ON_ACCENT
            mode_png_text.color = C_MUTED
        else:
            mode_color_text.color = C_MUTED
            mode_png_text.color = C_ON_ACCENT
        mode_color_text.weight = (
            ft.FontWeight.W_500 if color_active else ft.FontWeight.W_400
        )
        mode_png_text.weight = (
            ft.FontWeight.W_500 if not color_active else ft.FontWeight.W_400
        )

    def set_border_mode(mode):
        outline = mode == "outline"
        if engine.use_custom_outline == outline:
            return
        engine.use_custom_outline = outline
        engine.invalidate_border_cache()
        sync_border_mode_ui()
        color_frame_panel.visible = not outline
        outline_section.visible = outline
        deactivate_tools()
        page.update(
            mode_color_tab,
            mode_png_tab,
            mode_color_text,
            mode_png_text,
            color_frame_panel,
            outline_section,
        )
        refresh_preview()

    def on_apply_all_tiles_change(e):
        engine.apply_all_tiles = e.control.value
        if engine.apply_all_tiles:
            engine.clear_tile_bases()
        refresh_preview()

    def sync_paint_tool_buttons():
        picking_frame = picking_color["active"] and picking_color["for"] == "border"
        picking_paint = picking_color["active"] and picking_color["for"] == "brush"
        frame_pick_btn.icon_color = C_ACCENT if picking_frame else C_MUTED
        paint_pick_btn.icon_color = C_ACCENT if picking_paint else C_MUTED
        paint_brush_btn.icon_color = C_ACCENT if drawing_state["active"] else C_MUTED
        paint_fill_btn.icon_color = C_ACCENT if bucket_state["active"] else C_MUTED
        paint_tool_hint.visible = picking_paint
        paint_tool_hint.value = (
            "Click texture to sample paint color" if picking_paint else ""
        )

    def start_color_pick(target):
        if engine.base_image is None:
            show_toast("Load a texture first", error=True)
            return
        if target == "border" and engine.use_custom_outline:
            show_toast("Switch to colored frame mode first", error=True)
            return
        deactivate_tools()
        picking_color["active"] = True
        picking_color["for"] = target
        sync_paint_tool_buttons()
        sync_preview_gestures()
        if target == "border":
            show_toast("Click the preview to sample frame color")
        page.update(
            frame_pick_btn,
            paint_pick_btn,
            paint_brush_btn,
            paint_fill_btn,
            paint_tool_hint,
        )

    def toggle_frame_pick():
        if picking_color["active"] and picking_color["for"] == "border":
            deactivate_tools()
            page.update(frame_pick_btn, paint_tool_hint)
            return
        start_color_pick("border")

    def toggle_paint_pick():
        if picking_color["active"] and picking_color["for"] == "brush":
            deactivate_tools()
            page.update(paint_pick_btn, paint_tool_hint)
            return
        start_color_pick("brush")

    def toggle_brush():
        if engine.base_image is None:
            show_toast("Load a texture first", error=True)
            return
        if drawing_state["active"]:
            deactivate_tools()
            page.update(paint_brush_btn, paint_tool_hint)
            return
        deactivate_tools()
        drawing_state["active"] = True
        sync_paint_tool_buttons()
        sync_preview_gestures()
        page.update(
            paint_brush_btn,
            paint_fill_btn,
            paint_pick_btn,
            paint_tool_hint,
        )

    def toggle_fill():
        if engine.base_image is None:
            show_toast("Load a texture first", error=True)
            return
        if bucket_state["active"]:
            deactivate_tools()
            page.update(paint_fill_btn, paint_tool_hint)
            return
        deactivate_tools()
        bucket_state["active"] = True
        sync_tools_ui()
        sync_paint_tool_buttons()
        sync_preview_gestures()
        page.update(
            paint_fill_btn,
            paint_brush_btn,
            paint_pick_btn,
            paint_tool_hint,
        )

    def step_tile(delta):
        engine.preview_tile = max(0, min(46, engine.preview_tile + delta))
        refresh_preview()

    def adjust_zoom_shortcut(delta_percent):
        if engine.base_image is None:
            return
        cx, cy = preview_center()
        pct = zoom_percent_from_zoom(engine.zoom)
        next_pct = max(
            ZOOM_PERCENT_MIN,
            min(ZOOM_PERCENT_MAX, pct + delta_percent),
        )
        if next_pct == pct:
            return
        set_preview_zoom(zoom_from_percent(next_pct), cx, cy)
        sync_zoom_ui()
        refresh_zoom_preview(live=False)

    def on_keyboard(e: ft.KeyboardEvent):
        ctrl_tracker.on_flet_keyboard(e)

        if not text_field_shortcuts_blocked():
            if (
                e.key == "Arrow Left"
                and not (e.ctrl or e.meta or e.alt or e.shift)
                and engine.base_image is not None
            ):
                step_tile(-1)
                return
            if (
                e.key == "Arrow Right"
                and not (e.ctrl or e.meta or e.alt or e.shift)
                and engine.base_image is not None
            ):
                step_tile(1)
                return
            if e.key == "[" and not (e.ctrl or e.meta or e.alt):
                adjust_zoom_shortcut(-ZOOM_SCROLL_STEP)
                return
            if e.key == "]" and not (e.ctrl or e.meta or e.alt):
                adjust_zoom_shortcut(ZOOM_SCROLL_STEP)
                return

        if not (e.ctrl or e.meta):
            return
        key = e.key.lower()
        if key == "z" and not e.shift:
            undo_edit()
        elif key == "y" or (key == "z" and e.shift):
            redo_edit()

    page.on_keyboard_event = on_keyboard

    def on_preview_tap(e: ft.TapEvent):
        focus_preview_keyboard()
        if bucket_state["active"]:
            on_preview_bucket(e)
            return
        if not picking_color["active"]:
            return
        if e.local_position is None:
            return
        target = picking_color["for"]
        if target == "border" and engine.use_custom_outline:
            show_toast("Switch to colored frame mode first", error=True)
            return
        sampled = engine.sample_color_at(e.local_position.x, e.local_position.y)
        if not sampled:
            return
        hex_raw, (ix, iy) = sampled
        apply_sampled_color(hex_raw, target)
        picking_color["active"] = False
        sync_paint_tool_buttons()
        sync_preview_gestures()
        page.update(
            frame_pick_btn,
            paint_pick_btn,
            paint_brush_btn,
            paint_fill_btn,
            paint_tool_hint,
        )

    def on_preview_bucket(e: ft.TapEvent):
        if not bucket_state["active"] or e.local_position is None:
            return
        pixel = engine.local_to_pixel(e.local_position.x, e.local_position.y)
        if not pixel:
            return
        ix, iy = pixel
        push_undo_image()
        if engine.flood_fill(ix, iy, engine.fill_tolerance):
            refresh_preview()
            set_status(f"Filled from ({ix}, {iy})")
        else:
            edit_history["undo"].pop()
            sync_history_buttons()

    def on_preview_camera_pan_start(_: ft.PointerEvent):
        if engine.base_image is None:
            return
        focus_preview_keyboard()
        preview_camera_pan["active"] = True
        preview_gesture.mouse_cursor = ft.MouseCursor.GRABBING
        page.update(preview_gesture)

    def on_preview_camera_pan_update(e: ft.PointerEvent):
        if not preview_camera_pan["active"] or engine.base_image is None:
            return
        delta = e.local_delta
        if delta is None:
            return
        engine.preview_pan_x += float(delta.x)
        engine.preview_pan_y += float(delta.y)
        sync_preview_tile_layer()
        safe_page_update(preview_tile_layer)

    def on_preview_camera_pan_end(_: ft.PointerEvent):
        preview_camera_pan["active"] = False
        sync_preview_gestures()

    def on_preview_pan_start(e: ft.DragStartEvent):
        if not drawing_state["active"] or e.local_position is None:
            return
        focus_preview_keyboard()
        if not drawing_state["undo_snapshotted"]:
            push_undo_image()
            drawing_state["undo_snapshotted"] = True
        engine.begin_draw()
        drawing_state["last"] = None
        pixel = engine.local_to_pixel_float(e.local_position.x, e.local_position.y)
        if not pixel:
            return
        fx, fy = pixel
        drawing_state["last"] = (fx, fy)
        engine.draw_stroke(fx, fy, fx, fy)
        push_draw_preview(force=True)

    def on_preview_pan_update(e: ft.DragUpdateEvent):
        if not drawing_state["active"] or e.local_position is None:
            return
        pixel = engine.local_to_pixel_float(e.local_position.x, e.local_position.y)
        if not pixel:
            return
        fx, fy = pixel
        if drawing_state["last"]:
            lx, ly = drawing_state["last"]
            engine.draw_stroke(lx, ly, fx, fy)
        else:
            engine.draw_stroke(fx, fy, fx, fy)
        drawing_state["last"] = (fx, fy)
        push_draw_preview()

    def on_preview_pan_end(_: ft.DragEndEvent):
        engine.end_draw()
        drawing_state["last"] = None
        drawing_state["undo_snapshotted"] = False
        if drawing_state["active"]:
            refresh_preview()

    def sync_preview_gestures():
        drawing = drawing_state["active"]
        picking = picking_color["active"]
        bucketing = bucket_state["active"]
        preview_gesture.on_pan_start = on_preview_pan_start if drawing else None
        preview_gesture.on_pan_update = on_preview_pan_update if drawing else None
        preview_gesture.on_pan_end = on_preview_pan_end if drawing else None
        preview_gesture.on_tap_down = (
            on_preview_tap if picking or bucketing else None
        )
        preview_gesture.on_scroll = on_preview_scroll
        preview_gesture.on_right_pan_start = (
            on_preview_camera_pan_start if engine.base_image is not None else None
        )
        preview_gesture.on_right_pan_update = (
            on_preview_camera_pan_update if engine.base_image is not None else None
        )
        preview_gesture.on_right_pan_end = (
            on_preview_camera_pan_end if engine.base_image is not None else None
        )
        preview_gesture.mouse_cursor = (
            ft.MouseCursor.GRABBING
            if preview_camera_pan["active"]
            else ft.MouseCursor.PRECISE
            if drawing or picking or bucketing
            else ft.MouseCursor.BASIC
        )
        page.update(preview_gesture)

    preview_surface = ft.Container(
        content=ft.Container(
            content=empty_state,
            alignment=ft.Alignment(0, 0),
            expand=True,
            on_size_change=on_preview_resize,
        ),
        expand=True,
    )
    preview_inner = ft.Container(content=preview_surface, expand=True)
    preview_checker = ft.Container(
        content=preview_inner,
        expand=True,
        border_radius=12,
        border=ft.Border.all(1, C_BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        image=ft.DecorationImage(
            src=get_checker_tile_src(),
            repeat=ft.ImageRepeat.REPEAT,
            fit=ft.BoxFit.NONE,
        ),
    )

    def on_ctrl_key_down(e: ft.KeyDownEvent):
        ctrl_tracker.on_flet_key_down(e)

    def on_ctrl_key_up(e: ft.KeyUpEvent):
        ctrl_tracker.on_flet_key_up(e)

    if ctrl_tracker.use_flet_fallback:
        preview_body = ft.KeyboardListener(
            content=preview_checker,
            autofocus=True,
            on_key_down=on_ctrl_key_down,
            on_key_up=on_ctrl_key_up,
        )
        preview_keyboard_listener["control"] = preview_body
    else:
        preview_body = preview_checker
        preview_keyboard_listener["control"] = None

    preview_frame = ft.Container(
        content=preview_body,
        expand=True,
    )

    def sync_tools_ui():
        tolerance_section.visible = bucket_state["active"]
        page.update(tolerance_section)

    def deactivate_tools():
        picking_color["active"] = False
        bucket_state["active"] = False
        drawing_state["active"] = False
        drawing_state["last"] = None
        drawing_state["undo_snapshotted"] = False
        sync_paint_tool_buttons()
        sync_tools_ui()
        sync_preview_gestures()

    def on_tolerance_change(e):
        engine.fill_tolerance = int(e.control.value)
        tolerance_value.value = str(engine.fill_tolerance)

    def load_texture_path(path):
        try:
            img = Image.open(path).convert("RGBA")
            _apply_base_texture(img, os.path.basename(path).rsplit(".", 1)[0])
        except Exception as ex:
            show_toast(str(ex), error=True)

    def load_texture_bytes(data, name):
        try:
            img = Image.open(io.BytesIO(data)).convert("RGBA")
            _apply_base_texture(img, name.rsplit(".", 1)[0])
        except Exception as ex:
            show_toast(str(ex), error=True)

    def _apply_base_texture(img, filename):
        engine.base_image = img
        engine.base_filename = filename
        engine.clear_tile_bases()
        engine.invalidate_border_cache()
        edit_history["undo"].clear()
        edit_history["redo"].clear()
        sync_history_buttons()
        max_width = engine.ui_border_width_max()
        border_slider.max = max_width
        border_slider.min = 0
        border_slider.divisions = border_slider_divisions(max_width)
        if engine.border_width > max_width:
            engine.border_width = max_width
        if max_width == 0:
            engine.border_width = 0
        elif engine.border_width < 1:
            engine.border_width = 1
        sync_border_ui()
        alpha_slider.value = engine.border_alpha
        set_alpha_value_display(engine.border_alpha)
        outline_swatch.bgcolor = ft.Colors.with_opacity(
            int(engine.border_alpha) / 255,
            rgb_to_hex(engine.border_color),
        )
        color_swatch.bgcolor = ft.Colors.with_opacity(
            int(engine.brush_alpha) / 255,
            rgb_to_hex(engine.brush_color),
        )
        border_hex_field.value = rgb_to_hex(engine.border_color)[1:].upper()
        hex_field.value = rgb_to_hex(engine.brush_color)[1:].upper()
        generate_btn.disabled = False
        set_status(f"{engine.base_filename} · {img.size[0]}×{img.size[1]}")
        reset_preview_zoom()
        refresh_preview()
        sync_preview_gestures()
        safe_page_update(
            outline_swatch,
            color_swatch,
            border_hex_field,
            hex_field,
            generate_btn,
            border_slider,
            border_value,
            alpha_slider,
            alpha_value,
        )
        page.run_task(remeasure_preview)

    async def remeasure_preview(_=None):
        last_size = None
        for _ in range(10):
            await asyncio.sleep(0.05)
            if engine.base_image is None:
                return
            try:
                page.update(preview_surface, paint_toolbar)
            except RuntimeError:
                pass
            engine.set_preview_viewport(preview_viewport["w"], preview_viewport["h"])
            size = (preview_viewport["w"], preview_viewport["h"])
            center_preview_in_viewport()
            safe_page_update(preview_image, preview_tile_layer)
            if size == last_size:
                break
            last_size = size

    def load_outline_path(path):
        try:
            img = Image.open(path).convert("RGBA")
            _apply_outline_image(img)
        except Exception as ex:
            show_toast(str(ex), error=True)

    def load_outline_bytes(data, name):
        try:
            img = Image.open(io.BytesIO(data)).convert("RGBA")
            _apply_outline_image(img)
        except Exception as ex:
            show_toast(str(ex), error=True)

    def _apply_outline_image(img):
        if img.size != engine.base_image.size:
            show_toast(
                f"Outline must be {engine.base_image.size[0]}×{engine.base_image.size[1]}",
                error=True,
            )
            return
        engine.custom_outline_image = img
        engine.invalidate_border_cache()
        if engine.border_width == 0:
            engine.border_width = min(
                max(1, engine.ui_border_width_max()),
                max(1, img.width // 8),
            )
        sync_border_ui()
        set_status("Outline loaded")
        refresh_preview()

    async def _pick_png_file(dialog_title):
        return await file_picker.pick_files(
            dialog_title=dialog_title,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["png"],
            with_data=True,
        )

    def _use_picked_png(files, on_path, on_bytes):
        if not files:
            return
        picked = files[0]
        if picked.path:
            on_path(picked.path)
        elif picked.bytes:
            on_bytes(picked.bytes, picked.name)
        else:
            show_toast("Could not read the selected file", error=True)

    async def pick_texture(_=None):
        try:
            files = await _pick_png_file("Open texture")
            _use_picked_png(files, load_texture_path, load_texture_bytes)
        except Exception as ex:
            show_toast(f"File dialog failed: {ex}", error=True)

    async def pick_outline(_=None):
        if engine.base_image is None:
            show_toast("Load a texture first", error=True)
            return
        try:
            files = await _pick_png_file("Open outline")
            _use_picked_png(files, load_outline_path, load_outline_bytes)
        except Exception as ex:
            show_toast(f"File dialog failed: {ex}", error=True)

    async def open_save_folder(_=None):
        folder = engine.last_save_directory
        if not folder:
            try:
                folder = await file_picker.get_directory_path(
                    dialog_title="Open folder",
                )
            except Exception as ex:
                show_toast(f"File dialog failed: {ex}", error=True)
                return
            if not folder:
                return
            engine.last_save_directory = folder
            save_last_save_directory(folder)
        if not open_path_in_file_manager(folder):
            show_toast("Could not open folder", error=True)

    async def confirm_overwrite_dialog(folder_path):
        future = asyncio.get_running_loop().create_future()
        overwrite_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Overwrite existing pack?"),
            content=ft.Text(
                f'"{folder_path}" already exists. Generating will replace its files.'
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: close_overwrite_dialog(False),
                ),
                ft.TextButton(
                    "Overwrite",
                    on_click=lambda e: close_overwrite_dialog(True),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def close_overwrite_dialog(confirmed):
            if not future.done():
                future.set_result(confirmed)
            page.close(overwrite_dlg)

        page.open(overwrite_dlg)
        return await future

    async def write_generated_pack(save_dir):
        set_status("Generating…")
        page.update()
        try:
            out_path = engine.generate(save_dir)
            set_status("Pack generated")
            show_toast(f"Saved to {out_path}", duration=4.0)
        except Exception as ex:
            show_toast(str(ex), error=True)
            set_status("Generation failed")

    async def generate_pack(_=None):
        if engine.base_image is None:
            return
        try:
            save_dir = await file_picker.get_directory_path(
                dialog_title="Save CTM pack",
                initial_directory=engine.last_save_directory,
            )
        except Exception as ex:
            show_toast(f"File dialog failed: {ex}", error=True)
            return
        if not save_dir:
            return
        engine.last_save_directory = save_dir
        save_last_save_directory(save_dir)
        out_path = os.path.join(save_dir, engine.base_filename)
        if os.path.isdir(out_path):
            if not await confirm_overwrite_dialog(out_path):
                return
        await write_generated_pack(save_dir)

    appearance_icon = ft.Icon(ft.Icons.PALETTE_OUTLINED, size=16, color=C_MUTED)
    appearance_label = ft.Text("Appearance", size=12, color=C_TEXT, expand=True)
    appearance_chevron = ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=C_MUTED)
    appearance_btn = ft.Container(
        height=38,
        border_radius=8,
        border=ft.Border.all(1, C_BORDER),
        bgcolor=C_CHIP,
        ink=True,
        padding=ft.Padding(left=12, right=8, top=0, bottom=0),
        content=ft.Row(
            [
                appearance_icon,
                appearance_label,
                appearance_chevron,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    paint_all_label = ft.Text("Paint on all tiles", size=12, color=C_TEXT, expand=True)
    settings_divider_1 = ft.Divider(height=1, color=C_BORDER)
    settings_divider_2 = ft.Divider(height=1, color=C_BORDER)
    settings_divider_3 = ft.Divider(height=1, color=C_BORDER)
    settings_card = ft.Container(
        expand=True,
        bgcolor=C_SURFACE,
        border_radius=10,
        padding=ft.Padding(left=14, right=14, top=12, bottom=12),
        content=ft.Column(
            [
                mode_selector,
                color_frame_panel,
                outline_section,
                settings_divider_1,
                ft.Row(
                    [
                        paint_all_label,
                        apply_all_tiles_switch,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                settings_divider_2,
                ft.Container(expand=True),
                settings_divider_3,
                appearance_btn,
            ],
            spacing=10,
            expand=True,
        ),
    )

    export_title = ft.Text(
        "Export",
        size=13,
        weight=ft.FontWeight.W_600,
        color=C_TEXT,
    )
    export_subtitle = ft.Text(
        "47 tiles + .properties file",
        size=11,
        color=C_MUTED,
    )
    debug_tile_ids_label = ft.Text("Debug tile IDs", size=12, color=C_TEXT, expand=True)
    debug_tile_ids_hint = ft.Text(
        "Red ID on each tile — regenerate and reload the pack in-game",
        size=11,
        color=C_MUTED,
    )
    pack_card = ft.Container(
        bgcolor=C_SURFACE,
        border_radius=10,
        padding=ft.Padding(left=14, right=14, top=10, bottom=10),
        content=ft.Column(
            [
                ft.Row(
                    [
                        export_title,
                        export_subtitle,
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        debug_tile_ids_label,
                        debug_tile_ids_switch,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                debug_tile_ids_hint,
                ft.Row(
                    [new_texture_btn, generate_btn],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=8,
        ),
    )

    border_heading = ft.Text(
        "Border",
        size=14,
        weight=ft.FontWeight.W_600,
        color=C_TEXT,
    )
    border_subtitle = ft.Text(
        "How edges are drawn on each CTM tile",
        size=11,
        color=C_MUTED,
    )
    inspector = ft.Container(
        width=INSPECTOR_W,
        bgcolor=C_PANEL,
        border=ft.Border.only(left=ft.BorderSide(1, C_BORDER)),
        padding=ft.Padding(left=16, right=16, top=16, bottom=12),
        content=ft.Column(
            [
                border_heading,
                border_subtitle,
                settings_card,
                pack_card,
            ],
            expand=True,
            spacing=10,
        ),
    )

    tile_label = ft.Text("Tile", size=12, color=C_MUTED)
    tile_prev_btn = ft.IconButton(
        icon=ft.Icons.CHEVRON_LEFT,
        icon_size=18,
        icon_color=C_TEXT,
        style=ft.ButtonStyle(
            padding=4,
            shape=ft.RoundedRectangleBorder(radius=6),
        ),
        on_click=lambda e: step_tile(-1),
    )
    tile_next_btn = ft.IconButton(
        icon=ft.Icons.CHEVRON_RIGHT,
        icon_size=18,
        icon_color=C_TEXT,
        style=ft.ButtonStyle(
            padding=4,
            shape=ft.RoundedRectangleBorder(radius=6),
        ),
        on_click=lambda e: step_tile(1),
    )
    toolbar_divider_1 = ft.Container(width=1, height=22, bgcolor=C_BORDER)
    zoom_label = ft.Text("Zoom", size=12, color=C_MUTED)
    toolbar_divider_2 = ft.Container(width=1, height=22, bgcolor=C_BORDER)
    preview_toolbar = ft.Container(
        bgcolor=C_SURFACE,
        border_radius=10,
        padding=ft.Padding(left=14, right=14, top=10, bottom=10),
        content=ft.Row(
            [
                tile_label,
                tile_prev_btn,
                tile_value,
                tile_next_btn,
                toolbar_divider_1,
                zoom_label,
                ft.Container(content=zoom_slider, expand=True),
                zoom_value,
                toolbar_divider_2,
                undo_btn,
                redo_btn,
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    preview_area = ft.Container(
        expand=True,
        bgcolor=C_PANEL,
        padding=ft.Padding(left=24, right=24, top=20, bottom=16),
        content=ft.Column(
            [
                ft.Row(
                    [
                        preview_title,
                        status_toast,
                        preview_meta,
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                preview_frame,
                paint_toolbar,
                preview_toolbar,
            ],
            expand=True,
            spacing=12,
        ),
    )

    def apply_theme_to_ui(new_theme_id):
        nonlocal theme_id
        theme_id = new_theme_id
        apply_theme_colors(theme_id)
        save_settings(theme=theme_id)
        t = get_theme(theme_id)
        page.bgcolor = C_BG
        page.theme_mode = (
            ft.ThemeMode.LIGHT if t.get("mode") == "light" else ft.ThemeMode.DARK
        )
        page.theme = ft.Theme(
            color_scheme_seed=C_ACCENT,
            visual_density=ft.VisualDensity.COMPACT,
        )
        preview_area.bgcolor = C_PANEL
        inspector.bgcolor = C_PANEL
        inspector.border = ft.Border.only(left=ft.BorderSide(1, C_BORDER))
        settings_card.bgcolor = C_SURFACE
        pack_card.bgcolor = C_SURFACE
        paint_toolbar.bgcolor = C_SURFACE
        preview_toolbar.bgcolor = C_SURFACE
        paint_edit_bar.bgcolor = C_CHIP
        paint_edit_bar.border = ft.Border.all(1, C_BORDER)
        frame_color_chip.bgcolor = C_CHIP
        frame_color_chip.border = ft.Border.all(1, C_BORDER)
        appearance_btn.bgcolor = C_CHIP
        appearance_btn.border = ft.Border.all(1, C_BORDER)
        mode_selector.bgcolor = C_CHIP
        mode_selector.border = ft.Border.all(1, C_BORDER)
        preview_title.color = C_TEXT
        preview_meta.color = C_MUTED
        if status_toast.value:
            status_toast.color = C_ACCENT
        paint_tool_hint.color = C_ACCENT
        empty_state_icon.color = C_MUTED
        empty_state_title.color = C_TEXT
        empty_state_subtitle.color = C_MUTED
        border_heading.color = C_TEXT
        border_subtitle.color = C_MUTED
        export_title.color = C_TEXT
        export_subtitle.color = C_MUTED
        edit_texture_title.color = C_TEXT
        frame_color_label.color = C_TEXT
        width_label.color = C_TEXT
        opacity_label.color = C_TEXT
        guides_label.color = C_TEXT
        tolerance_label.color = C_TEXT
        paint_all_label.color = C_TEXT
        appearance_label.color = C_TEXT
        tile_label.color = C_MUTED
        zoom_label.color = C_MUTED
        for value in (zoom_value, tolerance_value):
            value.color = C_MUTED
        for field in (border_value, alpha_value):
            field.bgcolor = C_CHIP
            field.border_color = C_BORDER
            field.focused_border_color = C_ACCENT
            field.color = C_TEXT
            if field.suffix is not None:
                field.suffix.color = C_MUTED
        tile_value.color = C_TEXT
        appearance_icon.color = C_MUTED
        appearance_chevron.color = C_MUTED
        tile_prev_btn.icon_color = C_TEXT
        tile_next_btn.icon_color = C_TEXT
        for divider in (settings_divider_1, settings_divider_2, settings_divider_3):
            divider.color = C_BORDER
        for divider in (toolbar_divider_1, toolbar_divider_2):
            divider.bgcolor = C_BORDER
        for field, prefix in (
            (hex_field, hex_prefix),
            (border_hex_field, border_hex_prefix),
        ):
            field.bgcolor = C_CHIP
            field.border_color = C_BORDER
            field.focused_border_color = C_ACCENT
            field.color = C_TEXT
            prefix.color = C_MUTED
        frame_color_btn.icon_color = C_MUTED
        for slider in (border_slider, alpha_slider, zoom_slider, tolerance_slider):
            slider.active_color = C_ACCENT
            slider.inactive_color = C_BORDER
        for switch in (guides_switch, apply_all_tiles_switch):
            switch.active_color = C_ACCENT
            switch.inactive_thumb_color = C_MUTED
        sync_history_buttons()
        sync_border_mode_ui()
        sync_paint_tool_buttons()
        if page.controls:
            page.update()

    def show_theme_dialog(_=None):
        cards = []
        for tid, meta in iter_themes():
            selected = tid == theme_id

            def pick_theme(e, picked=tid):
                apply_theme_to_ui(picked)
                page.pop_dialog()

            cards.append(build_theme_card(meta, selected, pick_theme))

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                bgcolor=C_SURFACE,
                shape=ft.RoundedRectangleBorder(radius=16),
                title=ft.Text(
                    "Themes",
                    size=18,
                    weight=ft.FontWeight.W_600,
                    color=C_TEXT,
                ),
                content=ft.Container(
                    width=theme_grid_width(),
                    content=ft.Column(
                        tight=True,
                        spacing=10,
                        controls=[
                            ft.Text(
                                "Click a theme to recolor the app",
                                size=11,
                                color=C_MUTED,
                            ),
                            ft.Row(
                                cards,
                                wrap=True,
                                spacing=THEME_GRID_GAP,
                                run_spacing=THEME_GRID_GAP,
                                width=theme_grid_width(),
                            ),
                        ],
                    ),
                ),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: page.pop_dialog()),
                ],
            )
        )

    appearance_btn.on_click = lambda e: show_theme_dialog()

    page.add(
        ft.Row(
            [preview_area, inspector],
            expand=True,
            spacing=0,
        )
    )
    page.on_resize = on_page_resize
    apply_theme_to_ui(theme_id)
    refresh_preview()
    sync_border_mode_ui()
    sync_preview_gestures()

    page.run_task(warm_picker_cache)

    def guide_step(icon, title, body):
        return ft.Row(
            [
                ft.Container(
                    width=36,
                    height=36,
                    border_radius=8,
                    bgcolor=C_BG,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Icon(icon, size=18, color=C_ACCENT),
                ),
                ft.Column(
                    [
                        ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=C_TEXT),
                        ft.Text(body, size=12, color=C_MUTED),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def show_welcome_dialog():
        if load_settings().get("welcome_dismissed"):
            return

        dismiss_forever = ft.Checkbox(
            label="Don't show again",
            value=False,
            active_color=C_ACCENT,
            label_style=ft.TextStyle(size=12, color=C_MUTED),
        )

        def close_welcome(_=None):
            if dismiss_forever.value:
                save_settings(welcome_dismissed=True)
            page.pop_dialog()

        welcome_body = ft.Column(
            [
                ft.Text(
                    "Turn one block texture into a full 47-tile CTM pack. "
                    "Here's how the workflow fits together.",
                    size=13,
                    color=C_MUTED,
                ),
                ft.Divider(height=1, color=C_BORDER),
                guide_step(
                    ft.Icons.FOLDER_OPEN_OUTLINED,
                    "Load a texture",
                    "Open a PNG with the button in the preview area. The checkerboard shows transparency.",
                ),
                guide_step(
                    ft.Icons.GRID_VIEW_ROUNDED,
                    "Preview tiles",
                    "Use the tile arrows below the preview to step through all 47 CTM variants.",
                ),
                guide_step(
                    ft.Icons.BORDER_OUTER,
                    "Border (right panel)",
                    "Choose colored or custom PNG frame, then set color, width, and opacity. "
                    "Palette and eyedropper icons sample from the preview.",
                ),
                guide_step(
                    ft.Icons.BRUSH_OUTLINED,
                    "Edit texture (below preview)",
                    "Set paint color with the swatch or hex field, then Pick, Paint, or Fill. "
                    "Toggle \"All tiles\" to apply edits across every variant.",
                ),
                guide_step(
                    ft.Icons.SAVE_ALT_OUTLINED,
                    "Generate the pack",
                    "Click Generate pack, choose a folder, and drop the output into your resource pack.",
                ),
                dismiss_forever,
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        )

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                bgcolor=C_PANEL,
                shape=ft.RoundedRectangleBorder(radius=16),
                title=ft.Column(
                    [
                        ft.Text(
                            "Welcome to CTM Generator",
                            size=22,
                            weight=ft.FontWeight.W_600,
                            color=C_TEXT,
                        ),
                        ft.Text(
                            "Connected Texture Mod pack builder",
                            size=13,
                            color=C_MUTED,
                        ),
                    ],
                    spacing=4,
                    tight=True,
                ),
                content=ft.Container(
                    width=520,
                    height=430,
                    padding=ft.Padding(left=4, right=4, top=0, bottom=0),
                    content=welcome_body,
                ),
                actions=[
                    ft.FilledButton(
                        "Get started",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=close_welcome,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    async def show_welcome_later():
        await asyncio.sleep(0.3)
        show_welcome_dialog()

    page.run_task(show_welcome_later)


def run_app(page: ft.Page):
    try:
        main(page)
    except Exception:
        import traceback

        page.controls.clear()
        page.add(
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column(
                    [
                        ft.Text(
                            "CTM Generator failed to start",
                            size=18,
                            weight=ft.FontWeight.W_600,
                            color="#ef4444",
                        ),
                        ft.Text(
                            traceback.format_exc(),
                            size=11,
                            selectable=True,
                            color="#fca5a5",
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            )
        )
        page.update()


def clear_flet_cache() -> None:
    if os.environ.get("CTM_KEEP_CACHE") == "1":
        return
    cache_root = Path.home() / ".local/share/com.ctmgenerator.ctm-generator/flet"
    if not cache_root.is_dir():
        return
    app_dir = cache_root / "app"
    if app_dir.is_dir() and not (app_dir / "main.py").is_file():
        shutil.rmtree(cache_root, ignore_errors=True)


def launch() -> int:
    os.chdir(ROOT)
    clear_flet_cache()
    ft.run(run_app)
    return 0


if __name__ == "__main__":
    raise SystemExit(launch())
