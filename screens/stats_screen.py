from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_text_10
from config.ui_components import draw_header, draw_footer

_W      = 480
_H      = 280
_MARGIN = 20
_HEADER_H = 54
_FOOTER_H = 18

# Usable height: 280 - 54 - 18 = 208px
# 5 rows × 40px = 200px, 8px to spare
_RH = 40   # row height: 12px label + 22px value + 6px gap


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

        streak   = streak_days()
        pages    = total_pages()
        words    = total_words()
        hours    = total_hours()
        last     = last_session()
        avg_spp  = avg_s_per_page()
        rsvp_w   = total_rsvp_words()
        rsvp_pct = rsvp_time_pct()

        # Two-column layout: left col x=_MARGIN, right col x=_W//2
        col_l = _MARGIN
        col_r = _W // 2
        y0    = _HEADER_H + 6

        def _row(lbl, val, x, y):
            draw.text((x, y),        lbl, font=font_text_10,   fill=0)
            draw.text((x, y + 14),   val, font=font_medium_18, fill=0)

        avg_str  = f"{avg_spp:.0f} s" if avg_spp else "—"
        rsvp_str = f"{rsvp_w:,}" if rsvp_w else "—"
        rsvp_lbl = f"RSVP words ({rsvp_pct:.0f}%)" if rsvp_w else "RSVP words"

        # Row 0
        _row("Day Streak",    f"{streak}",        col_l, y0)
        _row("Total Pages",   f"{pages:,}",        col_r, y0)
        draw.line((_MARGIN, y0 + _RH, _W - _MARGIN, y0 + _RH), fill=0, width=1)

        # Row 1
        _row("Hours Reading", f"{hours:.1f} h",   col_l, y0 + _RH + 4)
        _row("Total Words",   f"{words:,}",        col_r, y0 + _RH + 4)
        draw.line((_MARGIN, y0 + _RH * 2 + 4, _W - _MARGIN, y0 + _RH * 2 + 4), fill=0, width=1)

        # Row 2
        _row("Avg per Page",  avg_str,             col_l, y0 + _RH * 2 + 8)
        _row(rsvp_lbl,        rsvp_str,            col_r, y0 + _RH * 2 + 8)
        draw.line((_MARGIN, y0 + _RH * 3 + 8, _W - _MARGIN, y0 + _RH * 3 + 8), fill=0, width=1)

        # Last session — full width
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
            draw.text((_MARGIN, y0 + _RH * 3 + 12), "Last Session", font=font_text_10, fill=0)
            draw.text((_MARGIN, y0 + _RH * 3 + 24), last_line,      font=font_text_10, fill=0)
        else:
            draw.text((_MARGIN, y0 + _RH * 3 + 12), "No sessions recorded yet.", font=font_text_10, fill=0)

        draw_footer(draw, "", "q = back", w=_W, h=_H, margin=_MARGIN)
        display.draw_screen(img)

        # Sync to Daybook in background
        try:
            from utils.daybook_sync import sync_stats
            sync_stats(streak=streak, pages=pages, words=words, hours=hours,
                       avg_spp=avg_spp, rsvp_words=rsvp_w, rsvp_pct=rsvp_pct)
        except Exception:
            pass

    def handle_key(self, key):
        if key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=2)
