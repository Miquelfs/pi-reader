import os
import json
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_options_24, font_text_10
from config.paths import LIBRARY_PATH, BOOKMARKS_FILE
from utils.text_parser import parse

_W = 480
_H = 280
_MARGIN = 16
_TOP = 10
_BOTTOM_BAR = 20
_LINE_H_BODY = 24
_LINE_H_HEADING = 32
_GAP_H = 8
_TEXT_AREA = _H - _TOP - _BOTTOM_BAR
_TEXT_W = _W - (_MARGIN * 2)  # usable pixel width for text

# Derive character wrap width from the font's average character width.
# Using 'n' as a representative mid-width character for Literata.
_CHAR_W = font_medium_18.getlength('n')
_WRAP_CHARS = max(20, int(_TEXT_W / _CHAR_W))


def _load_bookmarks():
    try:
        with open(BOOKMARKS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_bookmark(book_file, page):
    bookmarks = _load_bookmarks()
    bookmarks[book_file] = page
    bookmarks['_last_opened'] = book_file
    with open(BOOKMARKS_FILE, 'w') as f:
        json.dump(bookmarks, f)


def get_last_opened():
    """Return (book_file, page) of the last opened book, or (None, 0)."""
    bookmarks = _load_bookmarks()
    book = bookmarks.get('_last_opened')
    if not book:
        return None, 0
    page = bookmarks.get(book, 0)
    return book, page


def _build_pages(lines):
    """
    Group Line objects into pages based on pixel height budget.
    Returns a list of pages, each page is a list of Line objects.
    """
    pages = []
    current_page = []
    used_h = 0

    for line in lines:
        if line.kind == 'gap':
            h = _GAP_H
        elif line.kind == 'heading':
            h = _LINE_H_HEADING
        else:
            h = _LINE_H_BODY

        if used_h + h > _TEXT_AREA and current_page:
            pages.append(current_page)
            current_page = []
            used_h = 0
            # Don't start a new page with a gap
            if line.kind == 'gap':
                continue

        current_page.append(line)
        used_h += h

    if current_page:
        pages.append(current_page)

    return pages if pages else [[]]


class BookScreenReader:
    def __init__(self, ereader, book_file, start_page=None):
        self.ereader = ereader
        self.book_file = book_file

        with open(os.path.join(LIBRARY_PATH, book_file), 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        parsed = parse(content, wrap_width=_WRAP_CHARS)
        self.pages = _build_pages(parsed)
        self.total_pages = len(self.pages)
        # Flat word list for RSVP — only body text, no gaps/headings
        self._words = [w for line in parsed if line.kind == 'body' for w in line.text.split()]

        if start_page is not None:
            self.current_page = min(start_page, self.total_pages - 1)
        else:
            saved = _load_bookmarks().get(book_file, 0)
            self.current_page = min(saved, self.total_pages - 1)

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        y = _TOP
        for line in self.pages[self.current_page]:
            if line.kind == 'gap':
                y += _GAP_H
            elif line.kind == 'heading':
                draw.text((_MARGIN, y), line.text, font=font_options_24, fill=0)
                y += _LINE_H_HEADING
            else:
                draw.text((_MARGIN, y), line.text, font=font_medium_18, fill=0)
                y += _LINE_H_BODY

        # Footer bar
        draw.line((0, _H - _BOTTOM_BAR, _W, _H - _BOTTOM_BAR), fill=0, width=1)
        progress = f"{self.current_page + 1} / {self.total_pages}"
        draw.text((_MARGIN, _H - 14), progress, font=font_text_10, fill=0)
        draw.text((_W // 2 - 40, _H - 14), "p=opcions  q=enrere", font=font_text_10, fill=0)

        display.draw_screen(img, use_partial=True)

    def _draw_saved_confirmation(self):
        """Briefly show a 'Guardat!' overlay then redraw the page."""
        import time
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)
        # Redraw current page content
        y = _TOP
        for line in self.pages[self.current_page]:
            if line.kind == 'gap':
                y += _GAP_H
            elif line.kind == 'heading':
                draw.text((_MARGIN, y), line.text, font=font_options_24, fill=0)
                y += _LINE_H_HEADING
            else:
                draw.text((_MARGIN, y), line.text, font=font_medium_18, fill=0)
                y += _LINE_H_BODY
        # Overlay banner
        draw.rectangle((80, 100, 400, 148), fill=0)
        draw.text((130, 112), "Fragment guardat ✓", font=font_options_24, fill=0xFF)
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
            _save_bookmark(self.book_file, self.current_page)
            from screens.library import LibraryScreen
            from utils.scanner import get_books_list
            books = get_books_list()
            idx = books.index(self.book_file) if self.book_file in books else 0
            self.ereader.switch_to(LibraryScreen, start_index=idx)
