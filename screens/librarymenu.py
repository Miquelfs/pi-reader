from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_options_24, font_text_10
from config.ui_components import draw_battery_icon

_W = 480
_H = 280
_MARGIN = 16
_HEADER_H = 48


class LibraryMenuScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.menu = 0
        self.options = ['Llibres', 'Còmics', 'Mode de Lectura']

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw.rectangle((0, 0, _W, _HEADER_H + 4), fill=0)
        draw.text((_MARGIN, 8), "Biblioteca", font=font_title, fill=0xFF)
        draw_battery_icon(draw, x=_W - 68, y=16, inverted=True)

        item_h = 36
        top = _HEADER_H + 8
        for i, opt in enumerate(self.options):
            y = top + i * item_h
            if i == self.menu:
                draw.rectangle((_MARGIN - 4, y - 2, _W - _MARGIN, y + item_h - 6), fill=0)
                draw.text((_MARGIN + 4, y), opt, font=font_options_24, fill=0xFF)
            else:
                draw.text((_MARGIN + 4, y), opt, font=font_options_24, fill=0)

        draw.line((0, _H - 16, _W, _H - 16), fill=0, width=1)
        draw.text((_MARGIN, _H - 14), "p=select  q=back", font=font_text_10, fill=0)

        display.draw_screen(img, use_partial=True)

    def handle_key(self, key):
        if key == 'w':
            self.menu = max(0, self.menu - 1)
            self.draw()
        elif key == 's':
            self.menu = min(len(self.options) - 1, self.menu + 1)
            self.draw()
        elif key == 'p':
            if self.menu == 0:
                from screens.library import LibraryScreen
                self.ereader.switch_to(LibraryScreen)
            elif self.menu == 1:
                from screens.comics import ComicScreen
                self.ereader.switch_to(ComicScreen)
            elif self.menu == 2:
                pass  # Mode de lectura — Phase 2
        elif key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen)
