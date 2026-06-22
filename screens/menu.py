from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_options_24, font_medium_18, font_text_10
from config.ui_components import draw_header, draw_footer

_W = 480
_H = 280
_MARGIN = 28
_HEADER_H = 54
_ITEM_H = 36
_SPLIT_X = 220   # left nav column ends here


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

        # Measure once: actual rendered bounds of font_options_24 text
        _bb = font_options_24.getbbox("Ag")
        _text_h = _bb[3] - _bb[1]
        _text_offset = _bb[1]  # negative ascender offset PIL applies at draw.text

        top = _HEADER_H + 6
        for i, opt in enumerate(self.options):
            y = top + i * _ITEM_H
            text_y = y + (_ITEM_H - _text_h) // 2 - _text_offset
            if i == self.menu:
                draw.rectangle((0, y, 4, y + _ITEM_H - 2), fill=0)
                draw.text((_MARGIN, text_y), opt, font=font_options_24, fill=0)
            else:
                draw.text((_MARGIN, text_y), opt, font=font_options_24, fill=0)

        # Vertical divider
        draw.line((_SPLIT_X, _HEADER_H + 4, _SPLIT_X, _H - 22), fill=0, width=1)

        # Right panel: reading stats
        try:
            from utils.stats import streak_days, total_pages, total_hours, read_today, last_session
            streak = streak_days()
            pages  = total_pages()
            hours  = total_hours()
            did_read = read_today()
            last   = last_session()
        except Exception:
            streak = pages = 0
            hours = 0.0
            did_read = False
            last = None

        rx = _SPLIT_X + 16
        ry = _HEADER_H + 10
        panel_w = _W - rx - 12

        def _stat(val, lbl, y):
            draw.text((rx, y), val, font=font_options_24, fill=0)
            bb = font_options_24.getbbox(val)
            draw.text((rx, y + (bb[3] - bb[1]) + 2), lbl, font=font_text_10, fill=0)

        streak_val = f"{streak}" if streak else "—"
        streak_lbl = f"day{'s' if streak != 1 else ''} streak" + (" ✓" if did_read else "  read today?")
        _stat(streak_val, streak_lbl, ry)

        draw.line((rx, ry + 46, _W - 12, ry + 46), fill=0, width=1)

        _stat(f"{pages:,}", "pages read", ry + 54)

        draw.line((rx, ry + 100, _W - 12, ry + 100), fill=0, width=1)

        if last:
            book_short = last['book']
            while book_short and draw.textlength(book_short, font=font_text_10) > panel_w:
                book_short = book_short[:-1]
            draw.text((rx, ry + 108), "last read", font=font_text_10, fill=0)
            draw.text((rx, ry + 120), book_short, font=font_text_10, fill=0)
        else:
            draw.text((rx, ry + 108), "no sessions yet", font=font_text_10, fill=0)

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
