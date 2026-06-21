import os
import zipfile
import io
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_text_10, font_medium_18
from config.paths import COMICS_PATH

_W = 480
_H = 280
_FOOTER_H = 18
_IMG_H = _H - _FOOTER_H  # 262px for the image area

# Zone grid: 2 columns × 3 rows = 6 zones per page, Western reading order
_GRID_COLS = 2
_GRID_ROWS = 3
_ZONES_PER_PAGE = _GRID_COLS * _GRID_ROWS  # 6


def _dither(img):
    """Greyscale → Floyd-Steinberg dither → 1-bit."""
    return img.convert('L').convert('1', dither=Image.Dither.FLOYDSTEINBERG)


def _fit_to_display(img):
    """Scale a raw page image down to fit the display area, centred, 1-bit."""
    img = img.copy()
    img.thumbnail((_W, _IMG_H), Image.LANCZOS)
    canvas = Image.new('RGB', (_W, _IMG_H), (255, 255, 255))
    x = (_W - img.width) // 2
    y = (_IMG_H - img.height) // 2
    canvas.paste(img, (x, y))
    return _dither(canvas)


def _crop_zone(img, zone_index):
    """
    Crop one zone from a raw page image and scale it up to fill the display.
    Zones are ordered left→right, top→bottom (Western reading order).
    """
    col = zone_index % _GRID_COLS
    row = zone_index // _GRID_COLS
    iw, ih = img.size

    zone_w = iw // _GRID_COLS
    zone_h = ih // _GRID_ROWS

    x0 = col * zone_w
    y0 = row * zone_h
    x1 = x0 + zone_w
    y1 = y0 + zone_h

    cropped = img.crop((x0, y0, x1, y1))
    # Scale up to fill display area
    cropped = cropped.resize((_W, _IMG_H), Image.LANCZOS)
    return _dither(cropped)


def _error_page(msg):
    img = Image.new('1', (_W, _IMG_H), 0xFF)
    draw = ImageDraw.Draw(img)
    y = 20
    for line in msg.split('\n'):
        draw.text((16, y), line, font=font_medium_18, fill=0)
        y += 26
    return img


# ── Page sources ──────────────────────────────────────────────────────────────

class CbzSource:
    """Raw page loader for CBZ/CBR."""
    def __init__(self, path):
        self._zf = zipfile.ZipFile(path, 'r')
        self._names = sorted(
            n for n in self._zf.namelist()
            if n.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp'))
            and not os.path.basename(n).startswith('.')
        )
        self.total = len(self._names)
        self._cache = {}

    def get_raw(self, index):
        """Return the raw PIL Image (full resolution, RGB) for page index."""
        if index in self._cache:
            return self._cache[index]
        data = self._zf.read(self._names[index])
        img = Image.open(io.BytesIO(data)).convert('RGB')
        img.load()
        self._cache[index] = img
        return img

    def close(self):
        self._zf.close()
        self._cache.clear()


class PdfSource:
    """Raw page loader for PDF comics."""
    def __init__(self, path):
        self._path = path
        self._cache = {}
        self.total = self._count_pages()

    def _count_pages(self):
        try:
            import subprocess
            r = subprocess.run(['pdfinfo', self._path], capture_output=True, text=True)
            for line in r.stdout.splitlines():
                if line.startswith('Pages:'):
                    return int(line.split(':')[1].strip())
        except Exception:
            pass
        return 1

    def get_raw(self, index):
        if index in self._cache:
            return self._cache[index]
        try:
            from pdf2image import convert_from_path
            # Render at higher DPI so zone crops look sharp when scaled up
            pages = convert_from_path(
                self._path, dpi=150, fmt='jpeg',
                first_page=index + 1, last_page=index + 1
            )
            img = pages[0].convert('RGB')
        except ImportError:
            return None  # handled by caller
        except Exception as e:
            return None
        self._cache[index] = img
        return img

    def close(self):
        self._cache.clear()


def _make_source(filename):
    path = os.path.join(COMICS_PATH, filename)
    ext = filename.rsplit('.', 1)[-1].lower()
    try:
        if ext in ('cbz', 'cbr'):
            return CbzSource(path)
        elif ext == 'pdf':
            return PdfSource(path)
    except Exception:
        pass
    return None


# ── Screen ────────────────────────────────────────────────────────────────────

class ComicReaderScreen:
    """
    Comic reader with 2×3 zone grid.

    State:
      current_page  — which PDF/CBZ page (0-indexed)
      current_zone  — which of the 6 zones on that page (0-5), or -1 = overview
      overview_mode — True = show full page; False = show zoomed zone
    """

    def __init__(self, ereader, comic_file):
        self.ereader = ereader
        self.comic_file = comic_file
        self.current_page = 0
        self.current_zone = 0
        self.overview_mode = False
        self._source = None

        self._draw_status("Carregant còmic…")
        self._source = _make_source(comic_file)

        if self._source is None or self._source.total == 0:
            self._draw_status(f"No s'ha pogut obrir:\n{comic_file}\n\nq = tornar")
        else:
            self.draw()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw_status(self, msg):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)
        y = _H // 2 - 20
        for line in msg.split('\n'):
            draw.text((16, y), line, font=font_medium_18, fill=0)
            y += 28
        display.draw_screen(img)

    def draw(self):
        if self._source is None:
            return

        # Loading indicator for uncached pages
        if isinstance(self._source, PdfSource) and self.current_page not in self._source._cache:
            self._draw_status(f"Renderitzant pàgina {self.current_page + 1}…")

        raw = self._source.get_raw(self.current_page)

        if raw is None:
            content = _error_page(
                "pdf2image no instal·lat.\n"
                "Executa:\npip3 install pdf2image\n--break-system-packages"
            )
        elif self.overview_mode:
            content = _fit_to_display(raw)
        else:
            content = _crop_zone(raw, self.current_zone)

        # Compose final image with footer
        img = Image.new('1', (_W, _H), 0xFF)
        img.paste(content, (0, 0))

        draw = ImageDraw.Draw(img)
        draw.line((0, _IMG_H, _W, _IMG_H), fill=0, width=1)

        # Footer: title | zone indicator | page indicator
        name = os.path.splitext(self.comic_file)[0]
        if len(name) > 28:
            name = name[:26] + '…'
        draw.text((8, _IMG_H + 4), name, font=font_text_10, fill=0)

        if self.overview_mode:
            zone_label = "vista general"
        else:
            zone_label = f"zona {self.current_zone + 1}/{_ZONES_PER_PAGE}"
        draw.text((_W // 2 - 28, _IMG_H + 4), zone_label, font=font_text_10, fill=0)

        page_label = f"pàg {self.current_page + 1}/{self._source.total}"
        draw.text((_W - 72, _IMG_H + 4), page_label, font=font_text_10, fill=0)

        display.draw_screen(img)

    # ── Navigation ────────────────────────────────────────────────────────────

    def handle_key(self, key):
        if self._source is None:
            if key == 'q':
                self._go_back()
            return

        if key == 'p':
            # Toggle overview / zone mode
            self.overview_mode = not self.overview_mode
            self.draw()

        elif key == 's':
            if self.overview_mode:
                # In overview: advance to next page
                self._next_page()
            else:
                # In zone mode: next zone, or next page if on last zone
                if self.current_zone < _ZONES_PER_PAGE - 1:
                    self.current_zone += 1
                    self.draw()
                else:
                    self._next_page()

        elif key == 'w':
            if self.overview_mode:
                self._prev_page()
            else:
                if self.current_zone > 0:
                    self.current_zone -= 1
                    self.draw()
                else:
                    self._prev_page()

        elif key == 'q':
            self._go_back()

    def _next_page(self):
        if self.current_page < self._source.total - 1:
            self.current_page += 1
            self.current_zone = 0
            self.draw()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.current_zone = _ZONES_PER_PAGE - 1 if not self.overview_mode else 0
            self.draw()

    def _go_back(self):
        if self._source:
            self._source.close()
        from screens.comics import ComicScreen
        self.ereader.switch_to(ComicScreen)
