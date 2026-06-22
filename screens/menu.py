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
        self.options = ['Biblioteca', 'Guardats', 'Puja un llibre', 'Configuració']

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        # Header bar — filled black strip (+ 4px bottom border for weight)
        draw.rectangle((0, 0, _W, _HEADER_H + 4), fill=0)
        draw.text((_MARGIN, 8), "Pi Reader", font=font_title, fill=0xFF)
        draw_battery_icon(draw, x=_W - 68, y=16, inverted=True)

        # Menu items
        item_h = 40
        top = _HEADER_H + 10
        for i, opt in enumerate(self.options):
            y = top + i * item_h
            if i == self.menu:
                draw.rectangle((0, y - 2, _W, y + item_h - 4), fill=0)
                draw.text((_MARGIN, y + 2), f"› {opt}", font=font_options_24, fill=0xFF)
            else:
                draw.text((_MARGIN, y + 2), f"  {opt}", font=font_options_24, fill=0)
            # Separator line between items (not after last)
            if i < len(self.options) - 1:
                sep_y = y + item_h - 4
                draw.line((_MARGIN, sep_y, _W - _MARGIN, sep_y), fill=0, width=1)

        # Footer rule
        draw.line((0, _H - 16, _W, _H - 16), fill=0, width=1)
        draw.text((_MARGIN, _H - 14), "w/s=navegar  p=seleccionar", font=font_text_10, fill=0)

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
                from screens.saved_screen import SavedScreen
                self.ereader.switch_to(SavedScreen)
            elif self.menu == 2:
                from screens.upload_screen import UploadScreen
                self.ereader.switch_to(UploadScreen)
            elif self.menu == 3:
                pass  # Configuració — Phase 2
