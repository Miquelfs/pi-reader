import os
import json
import time as _time
from bisect import bisect_right
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_small_14, font_large_22, font_options_24, font_text_10
from config.paths import LIBRARY_PATH, BOOKMARKS_FILE
from config.ui_components import draw_footer
from utils.text_parser import parse

_W = 480
_H = 280
_MARGIN = 12
_HEADER_H = 0
_FOOTER_H = 18
_GAP_H = 8
_TEXT_AREA = _H - _FOOTER_H - 8
_TEXT_W = _W - _MARGIN - 8

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


def _save_bookmark(book_file, word, font_size):
    """Position is a body-word index so it survives font-size changes and RSVP."""
    bookmarks = _load_bookmarks()
    entry = _book_entry(bookmarks, book_file)
    entry.pop('page', None)
    entry['word'] = word
    entry['font_size'] = font_size
    bookmarks[book_file] = entry
    bookmarks['_last_opened'] = book_file
    # Written on every page turn, so a power cut mid-write must not leave a
    # truncated file behind.
    tmp = BOOKMARKS_FILE + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(bookmarks, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, BOOKMARKS_FILE)


def get_last_opened():
    """Return the filename of the last opened book, or None."""
    return _load_bookmarks().get('_last_opened')


def _cached_measure(font):
    # The font's own space is ~3px at 14px, which disappears on a 1-bit panel;
    # wrapping and drawing both use a wider minimum gap instead.
    widths = {' ': max(int(font.getlength(' ')), round(getattr(font, 'size', 14) / 3))}

    def measure(word):
        w = widths.get(word)
        if w is None:
            w = widths[word] = int(font.getlength(word))
        return w
    return measure


def _build_pages(lines, line_h_body, line_h_heading):
    """
    Group Line objects into pages based on pixel height budget.
    Returns (pages, toc) where toc is [(heading_text, page_index), ...].
    """
    pages = []
    toc = []
    current_page = []
    used_h = 0
    prev_kind = None

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

        if line.kind == 'heading' and prev_kind != 'heading':
            toc.append((line.text, len(pages)))

        current_page.append(line)
        used_h += h
        prev_kind = line.kind

    if current_page:
        pages.append(current_page)

    return (pages if pages else [[]]), toc


class BookScreenReader:
    def __init__(self, ereader, book_file, start_word=None, font_size=None):
        self.ereader = ereader
        self.book_file = book_file

        bookmarks = _load_bookmarks()
        entry = _book_entry(bookmarks, book_file)

        # font_size kwarg > this book's last size > Settings default
        if not font_size:
            from utils.config_manager import get as cfg_get
            font_size = entry.get('font_size') or cfg_get('default_font_size')
        self.font_size = font_size if font_size in _FONT_SIZES else 'medium'

        body_font, line_h_body, line_h_heading = _FONT_SIZES[self.font_size]
        self._body_font = body_font
        self._line_h_body = line_h_body
        self._line_h_heading = line_h_heading
        self._measure = _cached_measure(body_font)

        with open(os.path.join(LIBRARY_PATH, book_file), 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        parsed = parse(content, measure=self._measure, max_w=_TEXT_W,
                       heading_measure=_cached_measure(font_options_24))
        self.pages, self.toc = _build_pages(parsed, line_h_body, line_h_heading)
        self.total_pages = len(self.pages)
        self._words = [w for line in parsed if line.kind == 'body' for w in line.text.split()]

        self._page_starts = []
        n = 0
        for page in self.pages:
            self._page_starts.append(n)
            n += sum(len(line.text.split()) for line in page if line.kind == 'body')

        if start_word is None:
            start_word = entry.get('word')
        if start_word is not None:
            self.current_page = self.page_for_word(start_word)
        else:
            self.current_page = min(entry.get('page', 0), self.total_pages - 1)

        self._session_start = None   # set on draw, cleared while in sub-screens / asleep
        self._session_pages = 0
        self._session_words = 0

    def page_for_word(self, word):
        return max(0, bisect_right(self._page_starts, word) - 1)

    @property
    def current_word(self):
        return self._page_starts[self.current_page]

    def _flush_session(self):
        if self._session_start is None:
            return
        from utils.stats import record_session
        record_session(
            book=os.path.splitext(self.book_file)[0],
            pages=self._session_pages,
            words=self._session_words,
            duration_s=_time.time() - self._session_start,
        )
        self._session_start = None
        self._session_pages = 0
        self._session_words = 0

    def on_sleep(self):
        self._flush_session()

    def _justify_line(self, draw, text, y, font, is_last_line):
        """Draw text justified to _TEXT_W. Last lines in a paragraph stay left-aligned,
        and so do lines that would need very wide gaps (no hyphenation here)."""
        words = text.split()
        gap_count = len(words) - 1
        min_gap = self._measure(' ')
        extra = _TEXT_W - sum(self._measure(w) for w in words)
        if is_last_line or gap_count == 0 or extra > gap_count * min_gap * 4:
            base_gap, remainder = min_gap, 0
        else:
            base_gap = extra // gap_count
            remainder = extra % gap_count
        x = _MARGIN
        for idx, word in enumerate(words):
            draw.text((x, y), word, font=font, fill=0)
            x += self._measure(word)
            if idx < gap_count:
                x += base_gap + (1 if idx < remainder else 0)

    def _render_page(self, draw):
        y = 6
        page_lines = self.pages[self.current_page]
        for idx, line in enumerate(page_lines):
            if line.kind == 'gap':
                y += _GAP_H
            elif line.kind == 'heading':
                draw.text((_MARGIN, y), line.text, font=font_options_24, fill=0)
                y += self._line_h_heading
            else:
                # A line is "last" if it's the last body line before a gap/heading/end
                next_line = page_lines[idx + 1] if idx + 1 < len(page_lines) else None
                is_last = next_line is None or next_line.kind != 'body'
                self._justify_line(draw, line.text, y, self._body_font, is_last)
                y += self._line_h_body

    def draw(self):
        if self._session_start is None:
            self._session_start = _time.time()
        _save_bookmark(self.book_file, self.current_word, self.font_size)

        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        self._render_page(draw)

        progress = f"{self.current_page + 1} / {self.total_pages}"
        draw_footer(draw, progress, "p = options   q = back", w=_W, h=_H, margin=_MARGIN)

        display.draw_screen(img, use_partial=True)

    def _draw_saved_confirmation(self):
        import time
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)
        self._render_page(draw)
        draw_footer(draw, f"{self.current_page + 1} / {self.total_pages}", "p = options   q = back", w=_W, h=_H, margin=_MARGIN)
        draw.rectangle((80, 100, 400, 148), fill=0)
        draw.text((110, 112), "Highlight saved ✓", font=font_options_24, fill=0xFF)
        display.draw_screen(img)
        time.sleep(1.2)
        self.draw()

    def handle_key(self, key):
        if key == 's':  # next page
            if self.current_page < self.total_pages - 1:
                self._session_pages += 1
                self._session_words += self._page_starts[self.current_page + 1] - self.current_word
                self.current_page += 1
                self.draw()
        elif key == 'w':  # previous page
            if self.current_page > 0:
                self.current_page -= 1
                self.draw()
        elif key == 'p':  # open reader action menu (save / RSVP)
            self._flush_session()
            from screens.reader_menu import ReaderMenuScreen
            self.ereader.current_screen = ReaderMenuScreen(self.ereader, self)
            return
        elif key == 'q':
            self._flush_session()
            from screens.library import LibraryScreen
            from utils.scanner import get_books_list
            books = get_books_list()
            filenames = [b.filename for b in books]
            idx = filenames.index(self.book_file) if self.book_file in filenames else 0
            self.ereader.switch_to(LibraryScreen, start_index=idx)
