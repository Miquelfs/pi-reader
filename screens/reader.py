import os
import json
import time as _time
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_small_14, font_large_22, font_options_24, font_text_10
from config.paths import LIBRARY_PATH, BOOKMARKS_FILE
from config.ui_components import draw_header, draw_footer
from utils.text_parser import parse

_W = 480
_H = 280
_MARGIN = 16
_HEADER_H = 40
_FOOTER_H = 18
_GAP_H = 8
_TEXT_AREA = _H - _HEADER_H - _FOOTER_H
_TEXT_W = _W - (_MARGIN * 2)

# Per font-size: (body_font, line_h_body, line_h_heading)
_FONT_SIZES = {
    'small':  (font_small_14,  18, 26),
    'medium': (font_medium_18, 24, 32),
    'large':  (font_large_22,  30, 38),
}
_SIZE_CYCLE = ['small', 'medium', 'large']


def _load_bookmarks():
    try:
        with open(BOOKMARKS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _book_entry(bookmarks, book_file):
    """Return the per-book dict, upgrading old bare-int entries."""
    val = bookmarks.get(book_file, {})
    if isinstance(val, int):
        return {'page': val, 'font_size': 'medium'}
    return val


def _save_bookmark(book_file, page, font_size='medium'):
    bookmarks = _load_bookmarks()
    entry = _book_entry(bookmarks, book_file)
    entry['page'] = page
    entry['font_size'] = font_size
    bookmarks[book_file] = entry
    bookmarks['_last_opened'] = book_file
    with open(BOOKMARKS_FILE, 'w') as f:
        json.dump(bookmarks, f)


def get_last_opened():
    """Return (book_file, page) of the last opened book, or (None, 0)."""
    bookmarks = _load_bookmarks()
    book = bookmarks.get('_last_opened')
    if not book:
        return None, 0
    entry = _book_entry(bookmarks, book)
    return book, entry.get('page', 0)


def _build_pages(lines, line_h_body, line_h_heading):
    """
    Group Line objects into pages based on pixel height budget.
    Returns (pages, toc) where toc is [(heading_text, page_index), ...].
    """
    pages = []
    toc = []
    current_page = []
    used_h = 0

    for line in lines:
        if line.kind == 'gap':
            h = _GAP_H
        elif line.kind == 'heading':
            h = line_h_heading
        else:
            h = line_h_body

        if used_h + h > _TEXT_AREA and current_page:
            pages.append(current_page)
            current_page = []
            used_h = 0
            if line.kind == 'gap':
                continue

        if line.kind == 'heading' and not current_page:
            toc.append((line.text, len(pages)))

        current_page.append(line)
        used_h += h

    if current_page:
        pages.append(current_page)

    return (pages if pages else [[]]), toc


class BookScreenReader:
    def __init__(self, ereader, book_file, start_page=None, font_size=None):
        self.ereader = ereader
        self.book_file = book_file

        bookmarks = _load_bookmarks()
        entry = _book_entry(bookmarks, book_file)

        # font_size kwarg overrides bookmark; bookmark overrides default 'medium'
        self.font_size = font_size or entry.get('font_size', 'medium')
        if self.font_size not in _FONT_SIZES:
            self.font_size = 'medium'

        body_font, line_h_body, line_h_heading = _FONT_SIZES[self.font_size]
        self._body_font = body_font
        self._line_h_body = line_h_body
        self._line_h_heading = line_h_heading

        wrap_chars = max(20, int(_TEXT_W / body_font.getlength('n')))

        with open(os.path.join(LIBRARY_PATH, book_file), 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        parsed = parse(content, wrap_width=wrap_chars)
        self.pages, self.toc = _build_pages(parsed, line_h_body, line_h_heading)
        self.total_pages = len(self.pages)
        self._words = [w for line in parsed if line.kind == 'body' for w in line.text.split()]

        if start_page is not None:
            self.current_page = min(start_page, self.total_pages - 1)
        else:
            self.current_page = min(entry.get('page', 0), self.total_pages - 1)

        self._session_start_page = self.current_page
        self._session_start_time = _time.time()

    def _render_page(self, draw):
        y = _HEADER_H + 4
        for line in self.pages[self.current_page]:
            if line.kind == 'gap':
                y += _GAP_H
            elif line.kind == 'heading':
                draw.text((_MARGIN, y), line.text, font=font_options_24, fill=0)
                y += self._line_h_heading
            else:
                draw.text((_MARGIN, y), line.text, font=self._body_font, fill=0)
                y += self._line_h_body

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        title = os.path.splitext(self.book_file)[0]
        draw_header(draw, title, w=_W, h=_HEADER_H)
        self._render_page(draw)

        progress = f"{self.current_page + 1} / {self.total_pages}"
        draw_footer(draw, progress, "p = options   q = back", w=_W, h=_H, margin=_MARGIN)

        display.draw_screen(img, use_partial=True)

    def _draw_saved_confirmation(self):
        import time
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)
        title = os.path.splitext(self.book_file)[0]
        draw_header(draw, title, w=_W, h=_HEADER_H)
        self._render_page(draw)
        draw.rectangle((80, 100, 400, 148), fill=0)
        draw.text((110, 112), "Highlight saved ✓", font=font_options_24, fill=0xFF)
        display.draw_screen(img)
        time.sleep(1.2)
        self.draw()

    def _approx_word_for_page(self):
        """Estimate which word index corresponds to the start of the current page."""
        words_before = 0
        for page in self.pages[:self.current_page]:
            for line in page:
                if line.kind == 'body':
                    words_before += len(line.text.split())
        return words_before

    def handle_key(self, key):
        if key == 's':  # next page
            if self.current_page < self.total_pages - 1:
                self.current_page += 1
                self.draw()
        elif key == 'w':  # previous page
            if self.current_page > 0:
                self.current_page -= 1
                self.draw()
        elif key == 'p':  # open reader action menu (save / RSVP)
            from screens.reader_menu import ReaderMenuScreen
            self.ereader.current_screen = ReaderMenuScreen(self.ereader, self)
            return
        elif key == 'q':
            _save_bookmark(self.book_file, self.current_page, self.font_size)
            # Record reading session
            pages_read = abs(self.current_page - self._session_start_page)
            duration = _time.time() - self._session_start_time
            words_read = sum(
                len(line.text.split())
                for pg in self.pages[self._session_start_page:self.current_page + 1]
                for line in pg if line.kind == 'body'
            )
            from utils.stats import record_session
            record_session(
                book=os.path.splitext(self.book_file)[0],
                pages=pages_read,
                words=words_read,
                duration_s=duration,
            )
            from screens.library import LibraryScreen
            from utils.scanner import get_books_list
            books = get_books_list()
            filenames = [b.filename for b in books]
            idx = filenames.index(self.book_file) if self.book_file in filenames else 0
            self.ereader.switch_to(LibraryScreen, start_index=idx)
