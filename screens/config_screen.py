import socket
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_text_10
from config.ui_components import draw_header, draw_footer, get_battery_percent
from utils.scanner import get_books_list

_W = 480
_H = 280
_MARGIN = 16
_HEADER_H = 48
_ITEM_H = 36
_LABEL_W = 160    # pixels reserved for the label column


def _get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return 'no network'


# Setting definitions: (key, label, options_list)
# options_list = None means read-only info row
_SETTINGS = [
    ('sleep_timeout_min', 'Sleep timeout', [5, 10, 20, 30]),
    ('default_font_size', 'Default font',  ['small', 'medium', 'large']),
    ('daily_goal_pages',  'Daily goal',    [5, 10, 20, 30]),
    ('daybook_url',       'Daybook URL',   None),   # read-only display
]


class ConfigScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.cursor = 0   # which row is focused (only editable rows)
        self._editable = [i for i, (_, _, opts) in enumerate(_SETTINGS) if opts is not None]
        self._cursor_pos = 0  # index into _editable
        self.draw()

    @property
    def _focused_row(self):
        return self._editable[self._cursor_pos]

    def draw(self):
        from utils.config_manager import all_settings
        cfg = all_settings()

        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Settings", w=_W, h=_HEADER_H)

        ip = _get_ip()
        book_count = len(get_books_list())
        pct = get_battery_percent()
        battery_str = f"{pct}%" if pct is not None else "unavailable"

        # Info row at top
        info_y = _HEADER_H + 6
        draw.text((_MARGIN, info_y), f"IP: {ip}", font=font_text_10, fill=0)
        draw.text((_W // 2, info_y), f"Books: {book_count}  ·  Battery: {battery_str}", font=font_text_10, fill=0)

        y = info_y + 18
        draw.line((_MARGIN, y, _W - _MARGIN, y), fill=0, width=1)
        y += 6

        for row_idx, (key, label, options) in enumerate(_SETTINGS):
            focused = (row_idx == self._focused_row)
            value = cfg.get(key, '')

            # Format value for display
            if key == 'sleep_timeout_min':
                display_val = f"{value} min"
            elif key == 'default_font_size':
                display_val = str(value).capitalize()
            elif key == 'daily_goal_pages':
                display_val = f"{value} pages/day"
            else:
                # daybook_url — truncate if needed
                display_val = str(value)
                max_val_w = _W - _MARGIN - _LABEL_W - 8
                while display_val and draw.textlength(display_val, font=font_text_10) > max_val_w:
                    display_val = display_val[:-1]

            if focused:
                draw.rectangle((0, y, _W, y + _ITEM_H - 2), fill=0)
                draw.text((_MARGIN, y + 8), label, font=font_text_10, fill=0xFF)
                if options:
                    draw.text((_MARGIN + _LABEL_W, y + 4), display_val, font=font_medium_18, fill=0xFF)
                    # Arrows hint
                    draw.text((_W - 50, y + 8), "w/s", font=font_text_10, fill=0xFF)
                else:
                    draw.text((_MARGIN + _LABEL_W, y + 8), display_val, font=font_text_10, fill=0xFF)
            else:
                draw.text((_MARGIN, y + 8), label, font=font_text_10, fill=0)
                if options:
                    draw.text((_MARGIN + _LABEL_W, y + 4), display_val, font=font_medium_18, fill=0)
                else:
                    draw.text((_MARGIN + _LABEL_W, y + 8), display_val, font=font_text_10, fill=0)

            y += _ITEM_H

        draw_footer(draw, "w/s = change value", "p = next   q = back", w=_W, h=_H, margin=_MARGIN)

        display.draw_screen(img)

    def handle_key(self, key):
        from utils.config_manager import get as cfg_get, set as cfg_set
        row_idx = self._focused_row
        _, _, options = _SETTINGS[row_idx]

        if key == 'w' and options:
            current = cfg_get(_SETTINGS[row_idx][0])
            try:
                idx = list(options).index(current)
            except ValueError:
                idx = 0
            cfg_set(_SETTINGS[row_idx][0], options[(idx - 1) % len(options)])
            self.draw()

        elif key == 's' and options:
            current = cfg_get(_SETTINGS[row_idx][0])
            try:
                idx = list(options).index(current)
            except ValueError:
                idx = 0
            cfg_set(_SETTINGS[row_idx][0], options[(idx + 1) % len(options)])
            self.draw()

        elif key == 'p':
            self._cursor_pos = (self._cursor_pos + 1) % len(self._editable)
            self.draw()

        elif key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=4)
