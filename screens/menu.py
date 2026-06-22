from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_options_24
from config.ui_components import draw_header, draw_footer

_W = 480
_H = 280
_MARGIN = 28
_HEADER_H = 48
_ITEM_H = 36


class MenuScreen:
    def __init__(self, ereader, start_index=0):
        self.ereader = ereader
        self.menu = start_index
        self.options = ['Library', 'Highlights', 'Statistics', 'Upload', 'Settings']
        self.draw()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Pi Reader", w=_W, h=_HEADER_H)

        top = _HEADER_H + 6
        for i, opt in enumerate(self.options):
            y = top + i * _ITEM_H
            text_y = y + (_ITEM_H - 24) // 2
            if i == self.menu:
                draw.rectangle((0, y, 4, y + _ITEM_H - 2), fill=0)
                draw.text((_MARGIN, text_y), opt, font=font_options_24, fill=0)
            else:
                draw.text((_MARGIN, text_y), opt, font=font_options_24, fill=0)

        draw_footer(draw, "w/s = navigate", "p = open", w=_W, h=_H, margin=_MARGIN)

        display.draw_screen(img, use_partial=True)

    def handle_key(self, key):
        if key == 'w':
            self.menu = max(0, self.menu - 1)
            self.draw()
        elif key == 's':
            self.menu = min(len(self.options) - 1, self.menu + 1)
            self.draw()
        elif key == 'p':
            selected = self.options[self.menu]
            if selected == 'Library':
                from screens.library import LibraryScreen
                self.ereader.switch_to(LibraryScreen)
            elif selected == 'Highlights':
                from screens.saved_screen import SavedScreen
                self.ereader.switch_to(SavedScreen)
            elif selected == 'Statistics':
                from screens.stats_screen import StatsScreen
                self.ereader.switch_to(StatsScreen)
            elif selected == 'Upload':
                from screens.upload_screen import UploadScreen
                self.ereader.switch_to(UploadScreen)
            elif selected == 'Settings':
                from screens.config_screen import ConfigScreen
                self.ereader.switch_to(ConfigScreen)
