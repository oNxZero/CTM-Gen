import asyncio
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import main as app
from PIL import Image
from tools.capture_demo import build_context, sample_texture


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.engine = app.CTMEngine()
        self.engine.base_image = sample_texture()
        self.engine.base_filename = "stone"

    def test_exports_all_47_tiles_and_matching_rule(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(self.engine.generate(temp))
            self.assertEqual({p.name for p in output.glob("*.png")}, {f"{i}.png" for i in range(47)})
            for path in output.glob("*.png"):
                with Image.open(path) as tile:
                    self.assertEqual(tile.size, (16, 16))
                    self.assertEqual(tile.mode, "RGBA")
            self.assertEqual((output / "stone.properties").read_text(),
                             "matchTiles=stone\nmethod=ctm\ntiles=0-46\nconnect=tile\n")

    def test_zero_width_preserves_source_for_every_connection(self):
        self.engine.border_width = 0
        for i, rule in enumerate(app.CTM_RULES):
            self.assertEqual(self.engine.create_tile(rule, i).tobytes(), self.engine.base_image.tobytes())

    def test_single_tile_edits_do_not_modify_the_source_or_other_tiles(self):
        self.engine.border_width = 0
        original = self.engine.base_image.tobytes()
        self.engine.preview_tile = 17
        self.engine.set_brush_color("#F08020")
        self.engine.begin_draw()
        self.engine.draw_stroke(5, 5, 5, 5)
        self.engine.end_draw()
        self.assertEqual(self.engine.base_image.tobytes(), original)
        self.assertEqual(self.engine.create_tile(app.CTM_RULES[16], 16).tobytes(), original)
        self.assertNotEqual(self.engine.create_tile(app.CTM_RULES[17], 17).tobytes(), original)

    def test_shared_edits_apply_to_all_tiles(self):
        self.engine.border_width = 0
        self.engine.apply_all_tiles = True
        self.engine.set_brush_color("#00FF00")
        self.engine.begin_draw()
        self.engine.draw_stroke(4, 4, 4, 4)
        self.engine.end_draw()
        for i, rule in enumerate(app.CTM_RULES):
            self.assertEqual(self.engine.create_tile(rule, i).getpixel((4, 4)), (0, 255, 0, 255))

    def test_exported_debug_labels_do_not_modify_the_texture(self):
        original = self.engine.base_image.tobytes()
        with tempfile.TemporaryDirectory() as temp:
            plain = Path(self.engine.generate(temp)) / "0.png"
            before = plain.read_bytes()
            self.engine.debug_tile_labels = True
            self.engine.generate(temp)
            self.assertNotEqual(plain.read_bytes(), before)
        self.assertEqual(self.engine.base_image.tobytes(), original)

    def test_zoom_keeps_the_focal_texture_position_fixed(self):
        engine = self.engine
        engine.set_preview_viewport(800, 600)
        engine.center_view()
        x, y = 300, 240
        w, h, scale = engine.preview_display_metrics()
        ox, oy = engine.preview_origin(w, h)
        texture_point = ((x - ox) / scale, (y - oy) / scale)
        engine.apply_zoom_at(1.5, x, y)
        w, h, scale = engine.preview_display_metrics()
        ox, oy = engine.preview_origin(w, h)
        self.assertAlmostEqual((x - ox) / scale, texture_point[0])
        self.assertAlmostEqual((y - oy) / scale, texture_point[1])


class TestPage:
    def __init__(self):
        self.controls = []
        self.services = []
        self.dialogs = []
        self.window = SimpleNamespace()

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self, *controls):
        pass

    def run_task(self, *args, **kwargs):
        pass

    def show_dialog(self, dialog):
        self.dialogs.append(dialog)

    def pop_dialog(self):
        return self.dialogs.pop()


class DialogTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = patch.multiple(app, CONFIG_DIR=self.temp.name,
                                     CONFIG_PATH=str(Path(self.temp.name) / "settings.json"))
        self.config.start()
        self.addCleanup(self.config.stop)
        self.page = TestPage()
        with patch.object(app.CtrlTracker, "start"):
            self.context = build_context(self.page)

    async def test_overwrite_cancel_keeps_existing_files(self):
        ctx = self.context
        ctx["_apply_base_texture"](sample_texture(), "stone")
        directory = Path(self.temp.name) / "stone"
        directory.mkdir()
        existing = directory / "0.png"
        existing.write_bytes(b"keep existing file")
        with patch.object(ctx["file_picker"], "get_directory_path", return_value=self.temp.name):
            task = asyncio.create_task(ctx["generate_pack"]())
            await asyncio.sleep(0)
            self.assertEqual(len(self.page.dialogs), 1)
            self.page.dialogs[-1].actions[0].on_click(None)
            await task
        self.assertEqual(existing.read_bytes(), b"keep existing file")
        self.assertFalse(self.page.dialogs)

    async def test_confirmed_overwrite_exports_new_tiles(self):
        ctx = self.context
        ctx["_apply_base_texture"](sample_texture(), "stone")
        (Path(self.temp.name) / "stone").mkdir()
        with patch.object(ctx["file_picker"], "get_directory_path", return_value=self.temp.name):
            task = asyncio.create_task(ctx["generate_pack"]())
            await asyncio.sleep(0)
            self.page.dialogs[-1].actions[1].on_click(None)
            await task
        self.assertEqual(len(list((Path(self.temp.name) / "stone").glob("*.png"))), 47)
        self.assertFalse(self.page.dialogs)


if __name__ == "__main__":
    unittest.main()
