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
from PIL import Image
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


def main():
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ctm-demo-") as temp:
        temp = Path(temp)
        app.CONFIG_DIR = str(temp)
        app.CONFIG_PATH = str(temp / "settings.json")
        Path(app.CONFIG_PATH).write_text(json.dumps({"theme": "moonlight", "welcome_dismissed": True}))
        workflow = temp / "workflow"
        tiles = temp / "tiles"
        workflow.mkdir()
        tiles.mkdir()

        async def run(page):
            page.enable_screenshots = True
            with patch.object(app.CtrlTracker, "start"):
                ctx = build_context(page)
            engine = ctx["engine"]
            await asyncio.sleep(1)

            async def shot(folder, index):
                (folder / f"{index:03d}.png").write_bytes(
                    await page.take_screenshot(pixel_ratio=1, delay=150))

            try:
                await shot(workflow, 1)
                ctx["_apply_base_texture"](sample_texture(), "stone")
                await asyncio.sleep(0.5)
                await shot(workflow, 2)
                ctx["border_hex_field"].value = "8BD5CA"
                ctx["on_border_hex_change"](SimpleNamespace(control=ctx["border_hex_field"]))
                ctx["border_slider"].value = 2
                ctx["on_border_change"](SimpleNamespace(control=ctx["border_slider"]))
                ctx["guides_switch"].value = False
                ctx["guides_switch"].on_change(SimpleNamespace(control=ctx["guides_switch"]))
                page.update(ctx["guides_switch"])
                await shot(workflow, 3)
                for i, tile in enumerate([0, 3, 7, 12, 17, 26, 34, 46], start=4):
                    ctx["step_tile"](tile - engine.preview_tile)
                    await shot(workflow, i)
                ctx["step_tile"](-engine.preview_tile)
                overview = await page.take_screenshot(pixel_ratio=1, delay=150)
                (docs / "editor.png").write_bytes(overview)
                (workflow / "000.png").write_bytes(overview)
                for i in range(47):
                    ctx["step_tile"](i - engine.preview_tile)
                    await shot(tiles, i)
                await ctx["write_generated_pack"](str(temp / "export"))
                await shot(workflow, 12)
                assert len(list((temp / "export/stone").glob("*.png"))) == 47
                encode_gif(workflow, docs / "workflow.gif", 1.5)
                encode_gif(tiles, docs / "tiles.gif", 5)
                print("Captured docs/editor.png, docs/workflow.gif and docs/tiles.gif", flush=True)
            finally:
                await page.window.destroy()

        ft.run(run, assets_dir=str(ROOT / "assets"))


if __name__ == "__main__":
    main()
