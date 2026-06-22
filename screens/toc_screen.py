from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_text_10
from config.ui_components import draw_header, draw_footer

_W = 480
_H = 280
_MARGIN = 16
_HEADER_H = 48
_PAGE_SIZE = 6
_ITEM_H = 34


def _truncate(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + '…', font=font) > max_w:
        text = text[:-1]
    return text + '…'


class TocScreen:
    def __init__(self, ereader, toc, reader_screen):
        self.ereader = ereader
        self.toc = toc          # [(heading_text, page_index), ...]
        self.reader = reader_screen
        self.menu = 0
        self.page = 0
        self.draw()

    def _total_pages(self):
        return max(1, (len(self.toc) + _PAGE_SIZE - 1) // _PAGE_SIZE)

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Contents", w=_W, h=_HEADER_H)

        start = self.page * _PAGE_SIZE
        visible = self.toc[start:start + _PAGE_SIZE]

        # Max width for title — leave room for right-aligned page number (~40px)
        max_title_w = _W - _MARGIN * 2 - 50

        top = _HEADER_H + 4
        for i, (title, page_idx) in enumerate(visible):
            y = top + i * _ITEM_H
            label = _truncate(draw, title, font_medium_18, max_title_w)
            page_label = str(page_idx + 1)
            page_label_w = int(font_text_10.getlength(page_label))

            if i == self.menu:
                draw.rectangle((0, y, 4, y + _ITEM_H - 2), fill=0)
                draw.text((_MARGIN, y + 8), label, font=font_medium_18, fill=0)
                draw.text((_W - _MARGIN - page_label_w, y + 11), page_label, font=font_text_10, fill=0)
            else:
                draw.text((_MARGIN, y + 8), label, font=font_medium_18, fill=0)
                draw.text((_W - _MARGIN - page_label_w, y + 11), page_label, font=font_text_10, fill=0)

        if not visible:
            draw.text((_MARGIN, _HEADER_H + 40), "No chapters detected.", font=font_medium_18, fill=0)

        total = self._total_pages()
        left = f"{self.page + 1} / {total}" if total > 1 else ""
        draw_footer(draw, left, "p = jump   q = back", w=_W, h=_H, margin=_MARGIN)

        display.draw_screen(img)

    def handle_key(self, key):
        count = len(self.toc[self.page * _PAGE_SIZE:(self.page + 1) * _PAGE_SIZE])

        if key == 'w':
            if self.menu > 0:
                self.menu -= 1
                self.draw()
            elif self.page > 0:
                self.page -= 1
                self.menu = _PAGE_SIZE - 1
                self.draw()
        elif key == 's':
            if self.menu < count - 1:
                self.menu += 1
                self.draw()
            elif self.page < self._total_pages() - 1:
                self.page += 1
                self.menu = 0
                self.draw()
        elif key == 'p':
            flat_idx = self.page * _PAGE_SIZE + self.menu
            if flat_idx < len(self.toc):
                _, page_idx = self.toc[flat_idx]
                self.reader.current_page = page_idx
                self.ereader.current_screen = self.reader
                self.reader.draw()
        elif key == 'q':
            self.ereader.current_screen = self.reader
            self.reader.draw()
