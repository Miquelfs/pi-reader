from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_options_24, font_medium_18, font_text_10
from config.ui_components import draw_header, draw_footer

_W = 480
_H = 280
_MARGIN = 28
_HEADER_H = 54
_ROW_H = 32


class StatsScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.draw()

    def draw(self):
        from utils.stats import streak_days, total_pages, total_words, total_hours, last_session
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Statistics", w=_W, h=_HEADER_H)

        streak = streak_days()
        pages  = total_pages()
        words  = total_words()
        hours  = total_hours()
        last   = last_session()

        # Label column width
        lw = 160

        rows = [
            ("Current streak",  f"{streak} day{'s' if streak != 1 else ''}"),
            ("Total pages",     f"{pages:,}"),
            ("Total words",     f"{words:,}"),
            ("Hours reading",   f"{hours:.1f} h"),
        ]

        y = _HEADER_H + 10
        for label, value in rows:
            draw.text((_MARGIN, y), label, font=font_text_10, fill=0)
            draw.text((_MARGIN + lw, y - 2), value, font=font_medium_18, fill=0)
            y += _ROW_H

        # Thin separator
        draw.line((_MARGIN, y, _W - _MARGIN, y), fill=0, width=1)
        y += 6

        if last:
            from datetime import date as _date
            d = last['date']
            try:
                from datetime import datetime
                d = datetime.fromisoformat(last['date']).strftime('%d %b %Y')
            except Exception:
                pass
            last_line = f"{d}  ·  {last['book']}  ·  {last['pages']} pages"
            # Truncate if too wide
            max_w = _W - _MARGIN * 2
            while last_line and draw.textlength(last_line, font=font_text_10) > max_w:
                last_line = last_line[:-1]
            draw.text((_MARGIN, y), last_line, font=font_text_10, fill=0)
        else:
            draw.text((_MARGIN, y), "No sessions recorded yet.", font=font_text_10, fill=0)

        draw_footer(draw, "", "q = back", w=_W, h=_H, margin=_MARGIN)

        display.draw_screen(img)

    def handle_key(self, key):
        if key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=4)
