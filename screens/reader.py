import os
import json
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_options_24, font_text_10
from config.ui_components import draw_battery_icon
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


def _save_bookmark(book_file, line):
    bookmarks = _load_bookmarks()
    bookmarks[book_file] = line
    with open(BOOKMARKS_FILE, 'w') as f:
        json.dump(bookmarks, f)


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
    def __init__(self, ereader, book_file):
        self.ereader = ereader
        self.book_file = book_file

        with open(os.path.join(LIBRARY_PATH, book_file), 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        self.pages = _build_pages(parse(content, wrap_width=_WRAP_CHARS))
        self.total_pages = len(self.pages)

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
        draw_battery_icon(draw, x=_W - 68, y=_H - 16)

        display.draw_screen(img, use_partial=True)

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
            _save_bookmark(self.book_file, self.current_page)
            from screens.library import LibraryScreen
            self.ereader.switch_to(LibraryScreen)
