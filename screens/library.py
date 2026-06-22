import os
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_text_10
from utils.scanner import get_books_list
from config.ui_components import draw_header, draw_footer

_W = 480
_H = 280
_MARGIN = 16
_HEADER_H = 44
_FOOTER_H = 18
_PAGE_SIZE = 5
_ITEM_H = 42          # room for 2-line items
_MAX_W = _W - _MARGIN * 2 - 8


def _truncate(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + '…', font=font) > max_w:
        text = text[:-1]
    return text + '…'


class LibraryScreen:
    def __init__(self, ereader, start_index=0):
        self.ereader = ereader
        self.books = get_books_list()
        self.page = start_index // _PAGE_SIZE + 1
        self.menu = start_index % _PAGE_SIZE
        self.draw()

    def _total_pages(self):
        return max(1, (len(self.books) + _PAGE_SIZE - 1) // _PAGE_SIZE)

    def _flat_index(self):
        return (self.page - 1) * _PAGE_SIZE + self.menu

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Library", w=_W, h=_HEADER_H)

        start = (self.page - 1) * _PAGE_SIZE
        current_books = self.books[start:start + _PAGE_SIZE]
        top = _HEADER_H + 4

        if not current_books:
            draw.text((_MARGIN, top + 40), "No books in your library.", font=font_medium_18, fill=0)
            draw.text((_MARGIN, top + 66), "Upload a book via Wi-Fi.", font=font_text_10, fill=0)
        else:
            for i, book in enumerate(current_books):
                y = top + i * _ITEM_H
                title = _truncate(draw, book.title, font_medium_18, _MAX_W)
                author = _truncate(draw, book.author, font_text_10, _MAX_W) if book.author else ''

                if i == self.menu:
                    draw.rectangle((0, y, _W, y + _ITEM_H - 2), fill=0)
                    draw.text((_MARGIN, y + 4), title, font=font_medium_18, fill=0xFF)
                    if author:
                        draw.text((_MARGIN, y + 26), author, font=font_text_10, fill=0xFF)
                else:
                    draw.text((_MARGIN, y + 4), title, font=font_medium_18, fill=0)
                    if author:
                        draw.text((_MARGIN, y + 26), author, font=font_text_10, fill=0)

        page_label = f"{self.page} / {self._total_pages()}"
        draw_footer(draw, page_label, "p = open   q = back", w=_W, h=_H, margin=_MARGIN)

        display.draw_screen(img, use_partial=True)

    def handle_key(self, key):
        start = (self.page - 1) * _PAGE_SIZE
        page_count = len(self.books[start:start + _PAGE_SIZE])

        if key == 'w':
            if self.menu > 0:
                self.menu -= 1
                self.draw()
            elif self.page > 1:
                self.page -= 1
                self.menu = _PAGE_SIZE - 1
                self.draw()
        elif key == 's':
            if self.menu < page_count - 1:
                self.menu += 1
                self.draw()
            elif self.page < self._total_pages():
                self.page += 1
                self.menu = 0
                self.draw()
        elif key == 'p':
            if self.books:
                from screens.reader import BookScreenReader
                self.ereader.switch_to(BookScreenReader,
                                       book_file=self.books[self._flat_index()].filename)
        elif key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=0)
