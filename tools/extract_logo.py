"""
Run once on the Pi to generate assets/sleep_logo.png from the Asterix PDF.

Usage:
    python3 tools/extract_logo.py

The script renders page 5 of the Asterix PDF at high DPI, crops tightly
around the Asterix figure, and composes a clean sleep screen with text.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw
from config.paths import COMICS_PATH, BASE_DIR
from config.fonts import font_title, font_options_24, font_text_10

_W = 480
_H = 280

# Manual crop of Asterix figure from page 5 at 200 DPI.
# Page 5 rendered at 200 DPI = ~1654x2339px.
# Asterix running figure is in the top-right panel, roughly:
_PAGE = 5
_DPI  = 200

# Tight crop around the Asterix figure (right panel, top portion).
# These are fractions of the full page: (left, top, right, bottom)
# Adjust if the result isn't right — run with DEBUG=1 to see the full page.
_CROP_FRAC = (0.48, 0.02, 0.98, 0.52)


def _threshold(img):
    """
    Convert to 1-bit using a hard threshold — better than dithering for
    clean cartoon line art. White background stays white, lines stay black.
    """
    grey = img.convert('L')
    return grey.point(lambda p: 0 if p < 200 else 255, '1')


def extract():
    pdf_path = os.path.join(COMICS_PATH, 'Asterix_01_-_Asterix_el_galo_por_AlienkavCRG.pdf')
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        print("Place the Asterix PDF in content/comics/ and retry.")
        sys.exit(1)

    print(f"Rendering page {_PAGE} at {_DPI} DPI...")
    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(pdf_path, dpi=_DPI, fmt='jpeg',
                                  first_page=_PAGE, last_page=_PAGE)
        full = pages[0].convert('RGB')
    except ImportError:
        print("Run: pip3 install pdf2image --break-system-packages")
        sys.exit(1)

    iw, ih = full.size
    print(f"Full page size: {iw}x{ih}")

    # Save full page for inspection if DEBUG=1
    if os.environ.get('DEBUG'):
        full.save(os.path.join(BASE_DIR, 'assets', 'debug_page.jpg'))
        print("Saved debug_page.jpg")

    # Crop tight around Asterix
    x0 = int(_CROP_FRAC[0] * iw)
    y0 = int(_CROP_FRAC[1] * ih)
    x1 = int(_CROP_FRAC[2] * iw)
    y1 = int(_CROP_FRAC[3] * ih)
    print(f"Cropping ({x0},{y0}) → ({x1},{y1})")
    figure = full.crop((x0, y0, x1, y1))

    # --- Compose the sleep screen ---
    # Layout: figure on left 55% | text block on right 45%
    canvas = Image.new('RGB', (_W, _H), (255, 255, 255))

    fig_w = int(_W * 0.52)
    fig_h = _H - 16  # small padding top+bottom
    figure.thumbnail((fig_w, fig_h), Image.LANCZOS)
    # Paste vertically centred on left side
    fy = (_H - figure.height) // 2
    canvas.paste(figure, (0, fy))

    # Text block — right side
    draw = ImageDraw.Draw(canvas)
    tx = fig_w + 16
    text_w = _W - tx - 12

    # Thin vertical separator line
    draw.line((fig_w + 8, 24, fig_w + 8, _H - 24), fill=180, width=1)

    # "Pi Reader" — title
    draw.text((tx, 48), "Pi", font=font_title, fill=0)
    draw.text((tx, 86), "Reader", font=font_title, fill=0)

    # Horizontal rule under title
    draw.line((tx, 128, _W - 12, 128), fill=0, width=1)

    # Name
    draw.text((tx, 138), "Miquel Farré", font=font_options_24, fill=0)

    # Date — drawn at render time in sleep_screen.py, leave space here
    draw.text((tx, 175), "── ── ────", font=font_text_10, fill=180)

    # Convert: use threshold for line art, not dithering
    logo = _threshold(canvas)

    out_dir = os.path.join(BASE_DIR, 'assets')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'sleep_logo.png')
    logo.save(out_path)
    print(f"\nSaved: {out_path}")
    print("Run 'scp' to pull it to your Mac, then commit it.")


if __name__ == '__main__':
    extract()
