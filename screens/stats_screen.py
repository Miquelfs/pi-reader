from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_options_24, font_medium_18, font_small_14, font_text_10
from config.ui_components import draw_header, draw_footer

_W = 480
_H = 280
_MARGIN = 28
_HEADER_H = 54
_COL = _W // 2   # two-column layout split


class StatsScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.draw()

    def _stat(self, draw, x, y, value, label):
        """Draw a big value + small label pair."""
        draw.text((x, y), value, font=font_options_24, fill=0)
        bb = font_options_24.getbbox(value)
        val_h = bb[3] - bb[1]
        draw.text((x, y + val_h + 2), label, font=font_text_10, fill=0)

    def draw(self):
        from utils.stats import (streak_days, total_pages, total_words, total_hours,
                                  last_session, avg_s_per_page, total_rsvp_words, rsvp_time_pct)
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Statistics", w=_W, h=_HEADER_H)

        streak   = streak_days()
        pages    = total_pages()
        words    = total_words()
        hours    = total_hours()
        last     = last_session()
        avg_spp  = avg_s_per_page()
        rsvp_w   = total_rsvp_words()
        rsvp_pct = rsvp_time_pct()

        # Two-column grid: 3 rows × 2 cols
        row_h = 56
        y0 = _HEADER_H + 10
        lx = _MARGIN          # left column x
        rx = _COL + _MARGIN   # right column x

        self._stat(draw, lx, y0,          f"{streak}", f"day streak")
        self._stat(draw, rx, y0,          f"{pages:,}", "pages read")

        self._stat(draw, lx, y0 + row_h, f"{hours:.1f} h", "reading time")
        avg_str = f"{avg_spp:.0f} s" if avg_spp else "—"
        self._stat(draw, rx, y0 + row_h, avg_str, "avg per page")

        rsvp_str = f"{rsvp_w:,}" if rsvp_w else "—"
        rsvp_lbl = f"RSVP words  ({rsvp_pct:.0f}% of time)" if rsvp_w else "RSVP words"
        self._stat(draw, lx, y0 + row_h * 2, rsvp_str, rsvp_lbl)
        self._stat(draw, rx, y0 + row_h * 2, f"{words:,}", "total words")

        # Last session line
        sep_y = y0 + row_h * 3 + 4
        draw.line((_MARGIN, sep_y, _W - _MARGIN, sep_y), fill=0, width=1)
        if last:
            try:
                from datetime import datetime
                d = datetime.fromisoformat(last['date']).strftime('%d %b %Y')
            except Exception:
                d = last['date']
            last_line = f"{d}  ·  {last['book']}  ·  {last['pages']}p"
            max_w = _W - _MARGIN * 2
            while last_line and draw.textlength(last_line, font=font_text_10) > max_w:
                last_line = last_line[:-1]
            draw.text((_MARGIN, sep_y + 6), last_line, font=font_text_10, fill=0)
        else:
            draw.text((_MARGIN, sep_y + 6), "No sessions recorded yet.", font=font_text_10, fill=0)

        draw_footer(draw, "", "q = back", w=_W, h=_H, margin=_MARGIN)
        display.draw_screen(img)

    def handle_key(self, key):
        if key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=4)
