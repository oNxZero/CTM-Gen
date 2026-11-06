#!/usr/bin/env python3
"""Capture the real Flet app with sample data. Requires a desktop and FFmpeg."""

import asyncio
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import flet as ft
from PIL import Image, ImageDraw, ImageFont
import main as app


def sample_texture():
    rng = random.Random(42)
    image = Image.new("RGBA", (16, 16))
    image.putdata([(shade, shade + 5, shade + 12, 255)
                   for shade in [rng.randrange(82, 108) for _ in range(256)]])
    return image


def build_context(page):
    """Retain the app's callbacks for repeatable UI captures without adding demo code to the app."""
    context = {}
    previous = sys.getprofile()

    def capture(frame, event, value):
        if event == "return" and frame.f_code is app.main.__code__:
            context.update(frame.f_locals)

    try:
        sys.setprofile(capture)
        app.main(page)
    finally:
        sys.setprofile(previous)
    return context


def encode_gif(frames, output, fps):
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
        "-i", str(frames / "%03d.png"), "-filter_complex",
        "scale=1000:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];"
        "[b][p]paletteuse=dither=bayer:bayer_scale=3", "-loop", "0", str(output),
    ], check=True)


def tile_for_cell(cells, x, y):
    top, right, bottom, left = [(x + dx, y + dy) in cells
                                 for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]]
    rule = (
        not (top and left and (x - 1, y - 1) in cells),
        not (top and right and (x + 1, y - 1) in cells),
        not (bottom and left and (x - 1, y + 1) in cells),
        not (bottom and right and (x + 1, y + 1) in cells),
        not top, not right, not bottom, not left,
    )
    return app.CTM_RULES.index(rule)


def render_connections(folder, output):
    """Render a labeled flat-layout comparison from actual exported PNGs."""
    engine = app.CTMEngine()
    engine.base_image = sample_texture()
    engine.base_filename = "stone"
    engine.border_width = 1
    engine.set_border_color("#8BD5CA")
    exported = Path(engine.generate(str(folder / "export")))
    tiles = []
    for i in range(47):
        with Image.open(exported / f"{i}.png") as tile:
            tiles.append(tile.convert("RGBA").resize((64, 64), Image.Resampling.NEAREST))

    def font(size):
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

    panel = {(x, y) for x in range(6) for y in range(4)}
    layouts = [
        ("A solid panel", panel),
        ("Inner corners around a window", panel - {(2, 1), (3, 1), (2, 2), (3, 2)}),
        ("An L-shaped border", {(x, 3) for x in range(6)} | {(0, y) for y in range(4)}),
        ("Long edges", {(x, 1) for x in range(6)}),
        ("Two separate groups", {(x, y) for x in [0, 1, 4, 5] for y in [1, 2]}),
        ("Corners meeting in the middle", {(x, y) for x in range(6) for y in range(4)
                                           if x in [2, 3] or y in [1, 2]}),
    ]
    frames = folder / "frames"
    frames.mkdir()
    for index, (label, cells) in enumerate(layouts):
        canvas = Image.new("RGB", (1000, 620), "#24273a")
        draw = ImageDraw.Draw(canvas)
        draw.text((30, 24), "One texture. Different connections.", fill="#cad3f5", font=font(32))
        draw.text((32, 74), "Flat layout preview assembled from CTM Generator exports",
                  fill="#a5adcb", font=font(18))
        for x in [24, 512]:
            draw.rounded_rectangle((x, 126, x + 464, 556), radius=16,
                                   fill="#1e2030", outline="#494d64", width=2)
        draw.text((44, 146), "Single tile repeated", fill="#ed8796", font=font(23))
        draw.text((532, 146), "Matching CTM tiles", fill="#8bd5ca", font=font(23))
        for x, y in sorted(cells):
            canvas.paste(tiles[0], (64 + x * 64, 204 + y * 64), tiles[0])
            tile = tiles[tile_for_cell(cells, x, y)]
            canvas.paste(tile, (552 + x * 64, 204 + y * 64), tile)
        draw.text((32, 580), label, fill="#cad3f5", font=font(22))
        draw.text((950, 580), f"{index + 1}/6", fill="#a5adcb", font=font(18), anchor="ra")
        canvas.save(frames / f"{index:03d}.png")
    encode_gif(frames, output, 0.8)


def main():
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ctm-demo-") as temp:
        temp = Path(temp)
        app.CONFIG_DIR = str(temp)
        app.CONFIG_PATH = str(temp / "settings.json")
        Path(app.CONFIG_PATH).write_text(json.dumps({"theme": "moonlight", "welcome_dismissed": True}))
        workflow = temp / "workflow"
        workflow.mkdir()
        connections = temp / "connections"
        connections.mkdir()
        render_connections(connections, docs / "connected-layouts.gif")

        async def run(page):
            page.enable_screenshots = True
            with patch.object(app.CtrlTracker, "start"):
                ctx = build_context(page)
            engine = ctx["engine"]
            await asyncio.sleep(1)

            frame = 1

            async def shot():
                nonlocal frame
                (workflow / f"{frame:03d}.png").write_bytes(
                    await page.take_screenshot(pixel_ratio=1, delay=150))
                frame += 1

            try:
                await shot()
                ctx["_apply_base_texture"](sample_texture(), "stone")
                await asyncio.sleep(0.5)
                await shot()
                ctx["guides_switch"].value = False
                ctx["guides_switch"].on_change(SimpleNamespace(control=ctx["guides_switch"]))
                page.update(ctx["guides_switch"])
                for color, width in [("8BD5CA", 1), ("8BD5CA", 3), ("C6A0F6", 3), ("A6DA95", 2)]:
                    ctx["border_hex_field"].value = color
                    ctx["on_border_hex_change"](SimpleNamespace(control=ctx["border_hex_field"]))
                    ctx["border_slider"].value = width
                    ctx["on_border_change"](SimpleNamespace(control=ctx["border_slider"]))
                    page.update(ctx["border_hex_field"], ctx["border_slider"])
                    await shot()
                overview = await page.take_screenshot(pixel_ratio=1, delay=150)
                (workflow / "000.png").write_bytes(overview)
                ctx["hex_field"].value = "EED49F"
                ctx["on_hex_change"](SimpleNamespace(control=ctx["hex_field"]))
                page.update(ctx["hex_field"])
                ctx["toggle_brush"]()
                await shot()

                def point(x, y):
                    width, height, scale = engine.preview_display_metrics()
                    ox, oy = engine.preview_origin(width, height)
                    return SimpleNamespace(local_position=SimpleNamespace(
                        x=ox + (x + 0.5) * scale, y=oy + (y + 0.5) * scale))

                ctx["on_preview_pan_start"](point(5, 8))
                ctx["on_preview_pan_update"](point(8, 8))
                await shot()
                ctx["on_preview_pan_update"](point(10, 8))
                ctx["on_preview_pan_end"](None)
                await shot()
                ctx["undo_edit"]()
                await shot()
                ctx["redo_edit"]()
                await shot()
                ctx["toggle_brush"]()
                await ctx["write_generated_pack"](str(temp / "export"))
                await shot()
                assert len(list((temp / "export/stone").glob("*.png"))) == 47
                encode_gif(workflow, docs / "editing-workflow.gif", 1.25)
                print("Captured distinct editing and connected-layout GIFs", flush=True)
            finally:
                await page.window.destroy()

        ft.run(run, assets_dir=str(ROOT / "assets"))


if __name__ == "__main__":
    main()
