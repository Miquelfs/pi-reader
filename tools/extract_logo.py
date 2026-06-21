"""
Run this once on the Pi to extract the Asterix logo from the comic PDF
and save it as assets/sleep_logo.png (1-bit, 480x280).

Usage:
    python3 tools/extract_logo.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from config.paths import COMICS_PATH, BASE_DIR
from config.fonts import font_title, font_text_10

_W = 480
_H = 280

# Zone 1 of page 5 = top-left quarter of the page (2x3 grid, col=0, row=0)
_PAGE   = 5   # 1-indexed
_COLS   = 2
_ROWS   = 3
_ZONE   = 0   # 0 = top-left


def extract():
    pdf_path = os.path.join(COMICS_PATH, 'Asterix_01_-_Asterix_el_galo_por_AlienkavCRG.pdf')
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        print("Make sure the Asterix PDF is in content/comics/")
        sys.exit(1)

    print(f"Rendering page {_PAGE}...")
    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(pdf_path, dpi=200, fmt='jpeg',
                                  first_page=_PAGE, last_page=_PAGE)
        raw = pages[0].convert('RGB')
    except ImportError:
        print("pdf2image not installed. Run: pip3 install pdf2image --break-system-packages")
        sys.exit(1)

    iw, ih = raw.size
    zone_w = iw // _COLS
    zone_h = ih // _ROWS
    col = _ZONE % _COLS
    row = _ZONE // _COLS

    x0, y0 = col * zone_w, row * zone_h
    x1, y1 = x0 + zone_w, y0 + zone_h

    print(f"Cropping zone {_ZONE+1} ({x0},{y0} → {x1},{y1}) from {iw}x{ih} image...")
    cropped = raw.crop((x0, y0, x1, y1))

    # Scale to display size preserving aspect ratio, centred on white
    cropped.thumbnail((_W, _H - 60), Image.LANCZOS)  # leave room for text overlay
    canvas = Image.new('RGB', (_W, _H), (255, 255, 255))
    px = (_W - cropped.width) // 2
    py = (_H - 60 - cropped.height) // 2
    canvas.paste(cropped, (px, py))

    # Text overlay
    draw = ImageDraw.Draw(canvas)
    # Separator line above text area
    draw.line((0, _H - 55, _W, _H - 55), fill=0, width=1)
    draw.text((20, _H - 48), "Pi Reader", font=font_title, fill=0)
    draw.text((20, _H - 16), "Miquel Farré", font=font_text_10, fill=0)

    # Convert to 1-bit with dithering
    logo_1bit = canvas.convert('L').convert('1', dither=Image.Dither.FLOYDSTEINBERG)

    out_dir = os.path.join(BASE_DIR, 'assets')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'sleep_logo.png')
    logo_1bit.save(out_path)
    print(f"Saved: {out_path}")
    print("Now commit and push this file, then it will be used as the sleep screen.")


if __name__ == '__main__':
    extract()
