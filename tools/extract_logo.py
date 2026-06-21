"""
Generates assets/sleep_logo.png from assets/obelix_source.png.

Run on any machine (Mac or Pi):
    python3 tools/extract_logo.py

Layout (480x280, 1-bit):
    Left 52%  — Obelix figure, full height, white background
    Right 48% — "Pi Reader" title, separator line, name, date placeholder
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw
from config.paths import BASE_DIR
from config.fonts import font_title, font_options_24, font_text_10

_W = 480
_H = 280

_SOURCE = os.path.join(BASE_DIR, 'assets', 'obelix_source.png')
_OUT    = os.path.join(BASE_DIR, 'assets', 'sleep_logo.png')

# Text block X start (right of separator line)
_TX = int(_W * 0.52) + 20


def _threshold(img):
    """Hard threshold — keeps cartoon line art crisp (no dithering noise)."""
    return img.convert('L').point(lambda p: 0 if p < 210 else 255, '1')


def build():
    if not os.path.exists(_SOURCE):
        print(f"Source image not found: {_SOURCE}")
        print("Save the Obelix image as assets/obelix_source.png and retry.")
        sys.exit(1)

    source = Image.open(_SOURCE).convert('RGBA')

    # --- White canvas ---
    canvas = Image.new('RGB', (_W, _H), (255, 255, 255))

    # --- Obelix: fit into left 52%, full height with padding ---
    fig_max_w = int(_W * 0.50)
    fig_max_h = _H - 8  # 4px padding top + bottom

    obelix = source.copy()
    obelix.thumbnail((fig_max_w, fig_max_h), Image.LANCZOS)

    # Paste onto white background (handle transparency)
    bg = Image.new('RGB', obelix.size, (255, 255, 255))
    if obelix.mode == 'RGBA':
        bg.paste(obelix, mask=obelix.split()[3])
    else:
        bg.paste(obelix)

    # Centre vertically, align left
    fy = (_H - bg.height) // 2
    canvas.paste(bg, (0, fy))

    # --- Separator line ---
    sep_x = int(_W * 0.52)
    draw = ImageDraw.Draw(canvas)
    draw.line((sep_x, 28, sep_x, _H - 28), fill=0, width=1)

    # --- Text block ---
    # "Pi" on one line, "Reader" on next — gives the stacked title look
    draw.text((_TX, 30), "Pi", font=font_title, fill=0)
    draw.text((_TX, 68), "Reader", font=font_title, fill=0)

    # Horizontal rule — a bit more space below "Reader"
    rule_y = 118
    draw.line((_TX, rule_y, _W - 12, rule_y), fill=0, width=1)

    # Name
    draw.text((_TX, rule_y + 12), "Miquel Farré", font=font_options_24, fill=0)

    # Date placeholder — replaced at runtime by sleep_screen.py
    draw.text((_TX, rule_y + 48), "── ── ────", font=font_text_10, fill=200)

    # --- Convert to 1-bit ---
    logo = _threshold(canvas)

    os.makedirs(os.path.dirname(_OUT), exist_ok=True)
    logo.save(_OUT)
    print(f"Saved: {_OUT}")


if __name__ == '__main__':
    build()
