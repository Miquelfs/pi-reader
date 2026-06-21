import os
import zipfile
import io
from PIL import Image, ImageDraw, ImageOps
from config.display_manager import display
from config.fonts import font_text_10, font_medium_18
from config.ui_components import draw_battery_icon
from config.paths import COMICS_PATH

_W = 480
_H = 280
_FOOTER_H = 18
_IMG_H = _H - _FOOTER_H   # pixel rows available for the comic page image


def _dither(img):
    """
    Convert any image to 1-bit e-ink ready bitmap.
    Greyscale → Floyd-Steinberg dither → 1-bit.
    This preserves perceived shading in colour/greyscale comics.
    """
    grey = img.convert('L')
    dithered = grey.convert('1', dither=Image.Dither.FLOYDSTEINBERG)
    return dithered


def _fit(img, w, h):
    """Resize image to fit within (w, h) preserving aspect ratio, no upscaling beyond display size."""
    img.thumbnail((w, h), Image.LANCZOS)
    # Centre on a white canvas
    canvas = Image.new('1', (w, h), 0xFF)
    x = (w - img.width) // 2
    y = (h - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def _load_pages_cbz(path):
    """Return list of PIL Images from a CBZ (or CBR treated as zip) file."""
    pages = []
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            names = sorted(
                n for n in zf.namelist()
                if n.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'))
                and not os.path.basename(n).startswith('.')
            )
            for name in names:
                data = zf.read(name)
                img = Image.open(io.BytesIO(data))
                img.load()
                pages.append(_fit(_dither(img), _W, _IMG_H))
    except Exception as e:
        print(f"CBZ load error: {e}")
    return pages


def _load_pages_pdf(path):
    """Return list of PIL Images from a PDF using pdf2image (requires poppler)."""
    try:
        from pdf2image import convert_from_path
        raw_pages = convert_from_path(path, dpi=150, fmt='jpeg')
        return [_fit(_dither(p), _W, _IMG_H) for p in raw_pages]
    except ImportError:
        return _error_page("pdf2image not installed.\nRun: pip3 install pdf2image\nand: sudo apt install poppler-utils")
    except Exception as e:
        return _error_page(f"PDF error: {e}")


def _error_page(msg):
    """Return a single 'error' page image with the given message."""
    img = Image.new('1', (_W, _IMG_H), 0xFF)
    draw = ImageDraw.Draw(img)
    y = 20
    for line in msg.split('\n'):
        draw.text((16, y), line, font=font_medium_18, fill=0)
        y += 26
    return [img]


def load_comic(filename):
    """Load all pages from a comic file. Returns list of PIL Images (1-bit, display-sized)."""
    path = os.path.join(COMICS_PATH, filename)
    ext = filename.rsplit('.', 1)[-1].lower()

    if ext in ('cbz', 'cbr'):
        pages = _load_pages_cbz(path)
    elif ext == 'pdf':
        pages = _load_pages_pdf(path)
    else:
        pages = _error_page(f"Unsupported format: .{ext}")

    if not pages:
        pages = _error_page("No pages found in this file.")

    return pages


class ComicReaderScreen:
    def __init__(self, ereader, comic_file):
        self.ereader = ereader
        self.comic_file = comic_file
        self.current_page = 0

        # Show a loading message immediately while pages render
        self._draw_loading()
        self.pages = load_comic(comic_file)
        self.total_pages = len(self.pages)
        self.draw()

    def _draw_loading(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)
        draw.text((_W // 2 - 60, _H // 2 - 10), "Carregant còmic…", font=font_medium_18, fill=0)
        display.draw_screen(img)

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)

        # Paste the comic page in the upper region
        page_img = self.pages[self.current_page]
        img.paste(page_img, (0, 0))

        # Footer bar
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, _IMG_H, _W, _H), fill=0xFF)
        draw.line((0, _IMG_H, _W, _IMG_H), fill=0, width=1)
        progress = f"{self.current_page + 1} / {self.total_pages}"
        name = os.path.splitext(self.comic_file)[0]
        # Truncate title if long
        if len(name) > 40:
            name = name[:38] + '…'
        draw.text((16, _IMG_H + 3), name, font=font_text_10, fill=0)
        draw.text((_W - 70, _IMG_H + 3), progress, font=font_text_10, fill=0)
        draw_battery_icon(draw, x=_W - 68, y=_IMG_H + 3)

        display.draw_screen(img)

    def handle_key(self, key):
        if key == 's':  # next page
            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                self.draw()
        elif key == 'w':  # previous page
            if self.current_page > 0:
                self.current_page -= 1
                self.draw()
        elif key == 'q':
            from screens.comics import ComicScreen
            self.ereader.switch_to(ComicScreen)
