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
        from utils.stats import (streak_days, total_pages, total_words, total_hours,
                                  last_session, avg_s_per_page, total_rsvp_words, rsvp_time_pct)
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Statistics", w=_W, h=_HEADER_H)

        streak  = streak_days()
        pages   = total_pages()
        words   = total_words()
        hours   = total_hours()
        last    = last_session()
        avg_spp = avg_s_per_page()
        rsvp_w  = total_rsvp_words()
        rsvp_pct = rsvp_time_pct()

        lw = 168   # label column width

        avg_str = f"{avg_spp:.0f} s/page" if avg_spp else "—"
        rsvp_str = f"{rsvp_w:,} words  ({rsvp_pct:.0f}% of time)" if rsvp_w else "—"

        rows = [
            ("Streak",          f"{streak} day{'s' if streak != 1 else ''}"),
            ("Total pages",     f"{pages:,}"),
            ("Total words",     f"{words:,}"),
            ("Hours reading",   f"{hours:.1f} h"),
            ("Avg time/page",   avg_str),
            ("RSVP words",      rsvp_str),
        ]

        y = _HEADER_H + 8
        for label, value in rows:
            draw.text((_MARGIN, y + 2), label, font=font_text_10, fill=0)
            draw.text((_MARGIN + lw, y), value, font=font_medium_18, fill=0)
            y += _ROW_H

        if last:
            try:
                from datetime import datetime
                d = datetime.fromisoformat(last['date']).strftime('%d %b %Y')
            except Exception:
                d = last['date']
            last_line = f"Last: {d}  ·  {last['book']}  ·  {last['pages']}p"
            max_w = _W - _MARGIN * 2
            while last_line and draw.textlength(last_line, font=font_text_10) > max_w:
                last_line = last_line[:-1]
            draw.text((_MARGIN, y + 2), last_line, font=font_text_10, fill=0)

        draw_footer(draw, "", "q = back", w=_W, h=_H, margin=_MARGIN)
        display.draw_screen(img)

    def handle_key(self, key):
        if key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=4)
