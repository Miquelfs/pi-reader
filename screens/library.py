import os
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_text_10
from utils.scanner import get_books_list
from config.ui_components import draw_header

_W = 480
_H = 280
_MARGIN = 28
_HEADER_H = 44
_FOOTER_H = 18
_MAX_TITLE_W = _W - _MARGIN * 2 - 20


def _truncate(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + '…', font=font) > max_w:
        text = text[:-1]
    return text + '…'


def _clean_name(filename):
    return os.path.splitext(filename)[0]


class LibraryScreen:
    def __init__(self, ereader, start_index=0):
        self.ereader = ereader
        self.page_size = 6
        self.books = get_books_list()
        # Restore position: convert flat index back to page + menu
        self.page = start_index // self.page_size + 1
        self.menu = start_index % self.page_size
        self.draw()

    def _total_pages(self):
        return max(1, (len(self.books) + self.page_size - 1) // self.page_size)

    def _flat_index(self):
        return (self.page - 1) * self.page_size + self.menu

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Biblioteca", w=_W, h=_HEADER_H)

        # Book list
        start = (self.page - 1) * self.page_size
        current_books = self.books[start:start + self.page_size]
        item_h = 34
        top = _HEADER_H + 4

        if not current_books:
            draw.text((_MARGIN, top + 40), "No hi ha llibres a la biblioteca.", font=font_medium_18, fill=0)
        else:
            for i, book in enumerate(current_books):
                y = top + i * item_h
                label = _truncate(draw, _clean_name(book), font_medium_18, _MAX_TITLE_W)
                if i == self.menu:
                    draw.rectangle((0, y + 2, 5, y + item_h - 2), fill=0)
                draw.text((_MARGIN + 10, y + 7), label, font=font_medium_18, fill=0)

        # Footer
        draw.line((0, _H - _FOOTER_H, _W, _H - _FOOTER_H), fill=0, width=1)
        page_label = f"{self.page} / {self._total_pages()}"
        draw.text((_MARGIN, _H - 14), page_label, font=font_text_10, fill=0)
        draw.text((_W // 2 - 50, _H - 14), "p=obrir   q=enrere", font=font_text_10, fill=0)

        display.draw_screen(img, use_partial=True)

    def handle_key(self, key):
        start = (self.page - 1) * self.page_size
        page_count = len(self.books[start:start + self.page_size])

        if key == 'w':
            if self.menu > 0:
                self.menu -= 1
                self.draw()
            elif self.page > 1:
                self.page -= 1
                self.menu = self.page_size - 1
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
                self.ereader.switch_to(BookScreenReader, book_file=self.books[self._flat_index()])
        elif key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=0)
