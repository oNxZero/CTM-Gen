# 🧱 CTM Generator

> **Turn one Minecraft block texture into a full OptiFine CTM pack — 47 tiles, zero manual slicing.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey.svg)

A desktop app for resource pack artists. Load a PNG, set up borders, preview the result live, and export everything OptiFine needs — tile images `0.png` through `46.png` plus the `.properties` file.

Built with [Flet](https://flet.dev) and Pillow. One file (`main.py`), two dependencies, no build step.

---

## 📸 Demo

![CTM Generator UI Demo](assets/demo.png)

Drop your own screenshot in as `assets/demo.png` whenever you want to update this.

---

## 🔥 Features

* **Instant CTM export:** Slices and assembles all 47 standard tiles from a single source image.
* **Live preview:** See the full CTM layout before saving, with zoom for pixel-level work.
* **Colored frame mode:** Procedural borders with adjustable width, alpha, and color — eyedropper included.
* **Custom PNG mode:** Bring your own hand-drawn frame texture; the tool handles the slicing logic.
* **Paint tools:** Pick, brush, and fill on the loaded texture, with undo/redo.
* **Guide overlay:** Optional red lines show exactly where borders get cut.
* **Debug tile IDs:** Optional export mode stamps each tile with its index (`0`–`46`) in bright red — load the pack in-game to see which CTM tile OptiFine picks on each face.
* **Themes:** Moonlight, Light, Dark, Obsidian, Catppuccin, Dracula, and Nord — palettes adapted from [Moonlight](https://github.com/oNxZero/Moonlight).
* **Inline status:** Save confirmations show next to the preview (`Saved to /path/to/pack`).

---

## 🚀 Installation

```bash
git clone https://github.com/oNxZero/CTM-Gen.git
cd CTM-Gen

pip install -r requirements.txt
python main.py
```

Works the same on Linux and Windows — just use `python` instead of `python3` if that's what your system has.

---

## 📖 Usage

### 1. Load a texture

Click **Open texture** and pick your base block PNG.

### 2. Choose a border mode

* **Colored frame** — Set border color, width, and transparency. Use the eyedropper to sample from the preview.
* **Custom PNG** — Load a separate image with only the frame (transparent center).

### 3. Preview and tweak

Zoom in, toggle **Show guide lines**, and use the paint toolbar if you need small fixes on the texture.

### 4. Generate the pack

Click **Generate pack**, pick an output folder, and the app creates a subfolder with all 47 tiles and the properties file.

Turn on **Debug tile IDs** (in the Export panel) when troubleshooting CTM in-game. Each exported tile gets a small red pixel number centered inside the border area. Place blocks in Minecraft, note which numbers appear on broken faces, then turn debug off and regenerate a clean pack when you're done.

### 5. Drop it in your resource pack

```
assets/minecraft/optifine/ctm/<your_texture_name>/
```

---

## 🎨 Themes

Switch themes from the **Appearance** panel in the sidebar. The default **Moonlight** palette comes from [oNxZero/Moonlight](https://github.com/oNxZero/Moonlight).

Settings (theme, last save folder) live in:

```
~/.config/ctm-generator/settings.json
```

---

## 🤝 Credits

* **[Minecraft-Connected-Textures-Generator-CTM](https://github.com/Rostezkiy/Minecraft-Connected-Textures-Generator-CTM)** by Rostezkiy — original CTM tile indexing concept.
* **[Moonlight](https://github.com/oNxZero/Moonlight)** by oNxZero — theme palette inspiration.

This is a full rewrite: new UI, preview engine, paint tools, and export flow.

---

## 📜 License

Distributed under the MIT License.
