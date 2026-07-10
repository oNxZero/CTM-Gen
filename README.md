# CTM Generator

Desktop tool for making OptiFine connected texture packs from a single block PNG. You load the texture, set up borders, preview the layout, and export tiles `0.png`–`46.png` plus the `.properties` file.

Python + [Flet](https://flet.dev) + Pillow. Everything lives in `main.py`.

![CTM Generator UI Demo](assets/demo.png)

## Guide video

[![Watch the guide on YouTube](https://img.youtube.com/vi/WXpYSz8xrRo/hqdefault.jpg)](https://youtu.be/WXpYSz8xrRo)

## What it does

- Slices one source image into all 47 standard CTM tiles
- Live preview with zoom and right-click pan
- Colored frame borders (width up to 16 px, alpha, color, eyedropper) or a custom frame PNG
- Basic paint tools on the loaded texture: pick, brush, fill, undo/redo
- Red guide lines for where borders get cut
- **Debug tile IDs**: stamps each tile with its index in red so you can see what OptiFine picks in-game, then regenerate without debug when you're done
- A handful of UI themes (Moonlight is the default; also Light, Dark, Obsidian, Catppuccin, Dracula, Nord)

## Install

```bash
git clone https://github.com/oNxZero/CTM-Gen.git
cd CTM-Gen
pip install -r requirements.txt
python main.py
```

Linux and Windows. Use `python` or `python3` depending on what your system has.

## Quick start

1. **Open texture**: click **Open texture** or use **New texture**.
2. Pick a border mode:
   - **Colored frame**: procedural border. Eyedropper samples from the preview.
   - **Custom PNG**: separate image with just the frame (transparent center). Use **Open outline** while this mode is active.
3. Preview controls:
   - **Zoom slider** or **Ctrl + scroll** (50%–500%)
   - **← / →** to change tiles
   - **[ / ]** to zoom out / in
   - **Ctrl+Z / Ctrl+Y** for undo / redo
4. Toggle guide lines, paint if something needs a touch-up.
5. **Generate pack**: choose a folder. If that pack folder already exists, the app asks before overwriting.
6. Copy the output into your resource pack:

```
assets/minecraft/optifine/ctm/<your_texture_name>/
```

If CTM looks wrong in-game, turn on **Debug tile IDs** in the Export panel, place blocks, note which numbers show up on bad faces, fix the source, turn debug off, and export again.

## Settings

Theme and last save folder are stored in `~/.config/ctm-generator/settings.json`.

Moonlight palette is from [oNxZero/Moonlight](https://github.com/oNxZero/Moonlight).

## Credits

Tile indexing idea from [Minecraft-Connected-Textures-Generator-CTM](https://github.com/Rostezkiy/Minecraft-Connected-Textures-Generator-CTM) by Rostezkiy. This repo is a rewrite with a new UI, preview, paint tools, and export flow.

## License

MIT
