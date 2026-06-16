<p align="center">
  <strong>CTM Generator</strong><br>
  Connected textures for Minecraft — from one PNG to 47 tiles.
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square" alt="Python 3.10+"></a>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License">
  <img src="https://img.shields.io/badge/UI-Flet-3776AB?style=flat-square" alt="Flet UI">
</p>

<p align="center">
  <img src="assets/demo.png" alt="CTM Generator — preview, paint tools, and export panel" width="920">
</p>

<p align="center">
  <sub>Replace <code>assets/demo.png</code> with your own screenshot anytime.</sub>
</p>

---

A desktop tool for Minecraft resource pack artists. Load a block texture, define borders (procedural color or a custom PNG frame), preview the result, and export a complete **OptiFine CTM** folder — **47 tile images** plus a ready-made `.properties` file.

Modern rewrite of the [Auto-CTM](https://github.com/22or/Auto-CTM) workflow: real-time preview, zoom, paint tools, undo/redo, and multiple themes.

## Features

| | |
|---|---|
| **One-click export** | Generates tiles `0.png`–`46.png` and the matching `.properties` file. |
| **Live preview** | See the assembled CTM layout before saving; zoom in for pixel work. |
| **Colored frame** | Adjustable border width, alpha, and color — with eyedropper sampling from the preview. |
| **Custom PNG frame** | Upload a hand-drawn outline; the slicer handles the tile math. |
| **Paint tools** | Pick, brush, and fill on the loaded texture with undo/redo. |
| **Guide overlay** | Optional red lines show exactly where borders are cut. |
| **Themes** | Moonlight, Light, Dark, Obsidian, Catppuccin, Dracula, Nord. |
| **Status feedback** | Inline messages next to the preview (e.g. `Saved to /path/to/pack`). |

## Quick start

**Requirements:** Python 3.10+

```bash
git clone https://github.com/Rostezkiy/Minecraft-Connected-Textures-Generator-CTM.git
cd Minecraft-Connected-Textures-Generator-CTM

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

That’s it — no Flutter SDK, no build step. The app is a single `main.py` with two dependencies: [Flet](https://flet.dev) and Pillow.

## How to use

1. **Open texture** — Load your base block PNG (16×16 or larger).
2. **Pick a mode**
   - **Colored frame** — Set border color, width, and transparency.
   - **Custom PNG** — Load a separate image with only the frame (transparent center).
3. **Tune the preview** — Toggle guide lines, zoom, and use paint tools if you need small fixes.
4. **Generate pack** — Choose an output folder. The app creates a subfolder with all tiles and the properties file.
5. **Install in Minecraft** — Copy the generated folder into your resource pack:

   ```
   assets/minecraft/optifine/ctm/<your_texture_name>/
   ```

Settings (theme, last save directory) are stored in `~/.config/ctm-generator/settings.json`.

## Project layout

```
CTM-Generator/
├── main.py              # Application (UI + CTM engine)
├── requirements.txt
├── assets/
│   └── demo.png         # README screenshot (you provide this)
└── README.md
```

## Credits

Inspired by **[Auto-CTM](https://github.com/22or/Auto-CTM)** by 22or. This project is a full rewrite with a new UI, preview pipeline, and editing tools; the core CTM tile indexing idea remains the same.

## License

MIT
