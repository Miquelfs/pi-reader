import os
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_medium_18, font_text_10
from config.ui_components import draw_battery_icon
from config.paths import COMICS_PATH

_W = 480
_H = 280
_MARGIN = 16
_HEADER_H = 48
_FOOTER_H = 16


class ComicScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.menu = 0
        self.page = 1
        self.page_size = 6
        try:
            self.books = [f for f in sorted(os.listdir(COMICS_PATH)) if not f.startswith('.')]
        except FileNotFoundError:
            self.books = []

    def _total_pages(self):
        return max(1, (len(self.books) + self.page_size - 1) // self.page_size)

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw.rectangle((0, 0, _W, _HEADER_H + 4), fill=0)
        draw.text((_MARGIN, 8), "Còmics", font=font_title, fill=0xFF)
        draw_battery_icon(draw, x=_W - 68, y=16, inverted=True)

        start = (self.page - 1) * self.page_size
        current_books = self.books[start:start + self.page_size]
        item_h = 32
        top = _HEADER_H + 6

        if not current_books:
            draw.text((_MARGIN, top + 32), "No hi ha còmics.", font=font_medium_18, fill=0)
        else:
            for i, book in enumerate(current_books):
                y = top + i * item_h
                label = os.path.splitext(book)[0]
                if i == self.menu:
                    draw.rectangle((_MARGIN - 4, y - 2, _W - _MARGIN, y + item_h - 4), fill=0)
                    draw.text((_MARGIN + 4, y), label, font=font_medium_18, fill=0xFF)
                else:
                    draw.text((_MARGIN + 4, y), label, font=font_medium_18, fill=0)

        draw.line((0, _H - _FOOTER_H, _W, _H - _FOOTER_H), fill=0, width=1)
        page_label = f"Pàgina {self.page} / {self._total_pages()}"
        draw.text((_MARGIN, _H - 14), page_label, font=font_text_10, fill=0)
        draw.text((_W - 120, _H - 14), "p=obrir  q=enrere", font=font_text_10, fill=0)

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
            pass  # comic viewer — Phase 2
        elif key == 'q':
            from screens.librarymenu import LibraryMenuScreen
            self.ereader.switch_to(LibraryMenuScreen)
