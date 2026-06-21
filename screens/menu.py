from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_options_24, font_text_10
from config.ui_components import draw_battery_icon

_W = 480  # canvas width  (epd.height in landscape)
_H = 280  # canvas height (epd.width  in landscape)
_MARGIN = 16
_HEADER_H = 48  # height of the title bar area


class MenuScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.menu = 0
        self.options = ['Biblioteca', 'Guardats', 'Mode de Lectura', 'Configuració']

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        # Header bar — filled black strip
        draw.rectangle((0, 0, _W, _HEADER_H), fill=0)
        draw.text((_MARGIN, 8), "Pi Reader", font=font_title, fill=0xFF)
        draw_battery_icon(draw, x=_W - 68, y=16, inverted=True)

        # Menu items — inverted highlight on selected row
        item_h = 36
        top = _HEADER_H + 8
        for i, opt in enumerate(self.options):
            y = top + i * item_h
            if i == self.menu:
                draw.rectangle((_MARGIN - 4, y - 2, _W - _MARGIN, y + item_h - 6), fill=0)
                draw.text((_MARGIN + 4, y), opt, font=font_options_24, fill=0xFF)
            else:
                draw.text((_MARGIN + 4, y), opt, font=font_options_24, fill=0)

        # Footer rule
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
                from screens.librarymenu import LibraryMenuScreen
                self.ereader.switch_to(LibraryMenuScreen)
            elif self.menu == 1:
                from screens.librarymenu import LibraryMenuScreen
                self.ereader.switch_to(LibraryMenuScreen)
            elif self.menu == 2:
                pass  # RSVP — Phase 2
            elif self.menu == 3:
                pass  # Configuració — Phase 2
