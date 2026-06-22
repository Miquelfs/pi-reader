from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_options_24, font_text_10
from config.ui_components import draw_battery_icon

_W = 480
_H = 280
_MARGIN = 28
_HEADER_H = 44


class MenuScreen:
    def __init__(self, ereader, start_index=0):
        self.ereader = ereader
        self.menu = start_index
        self.options = ['Biblioteca', 'Guardats', 'Puja un llibre', 'Configuració']
        self.draw()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        # Header: title text with black fill behind it only, battery right
        title = "Pi Reader"
        tw = int(font_title.getlength(title))
        draw.rectangle((_MARGIN - 6, 6, _MARGIN + tw + 6, _HEADER_H - 6), fill=0)
        draw.text((_MARGIN, 8), title, font=font_title, fill=0xFF)
        draw_battery_icon(draw, x=_W - 72, y=14)
        draw.line((0, _HEADER_H, _W, _HEADER_H), fill=0, width=1)

        # Menu items
        item_h = 44
        top = _HEADER_H + 6
        for i, opt in enumerate(self.options):
            y = top + i * item_h
            if i == self.menu:
                draw.rectangle((0, y + 2, 5, y + item_h - 4), fill=0)
                draw.text((_MARGIN + 10, y + 10), opt, font=font_options_24, fill=0)
            else:
                draw.text((_MARGIN + 10, y + 10), opt, font=font_options_24, fill=0)

        # Footer
        draw.line((0, _H - 18, _W, _H - 18), fill=0, width=1)
        draw.text((_MARGIN, _H - 14), "w/s=navegar   p=obrir", font=font_text_10, fill=0)

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
                from screens.config_screen import ConfigScreen
                self.ereader.switch_to(ConfigScreen)
