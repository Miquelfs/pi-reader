from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_text_10
from config.ui_components import draw_header, draw_footer

_W = 480
_H = 280
_MARGIN = 20
_HEADER_H = 54
_FOOTER_H = 18

# Fixed row geometry: value at row_y, label at row_y + 20, next row starts at row_y + 36
_ROW_H  = 36   # value line (18pt ≈ 22px rendered) + label (10pt ≈ 12px) + 2px gap
_VAL_H  = 20   # space reserved for the value text
_LBL_Y  = 20   # offset from row top to label baseline


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

        # Six stats in a 2-column × 3-row grid
        col_l = _MARGIN
        col_r = _W // 2 + _MARGIN
        y0    = _HEADER_H + 8

        stats = [
            (col_l, y0 + _ROW_H * 0, f"{streak}",        f"day streak"),
            (col_r, y0 + _ROW_H * 0, f"{pages:,}",       "pages read"),
            (col_l, y0 + _ROW_H * 1, f"{hours:.1f} h",   "reading time"),
            (col_r, y0 + _ROW_H * 1, f"{avg_spp:.0f} s" if avg_spp else "—", "avg per page"),
            (col_l, y0 + _ROW_H * 2, f"{rsvp_w:,}" if rsvp_w else "—",
                                      f"RSVP ({rsvp_pct:.0f}%)" if rsvp_w else "RSVP words"),
            (col_r, y0 + _ROW_H * 2, f"{words:,}",       "total words"),
        ]

        for x, y, val, lbl in stats:
            draw.text((x, y),           val, font=font_medium_18, fill=0)
            draw.text((x, y + _LBL_Y), lbl, font=font_text_10,   fill=0)

        # Separator + last session
        sep_y = y0 + _ROW_H * 3 + 2
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
            draw.text((_MARGIN, sep_y + 5), last_line, font=font_text_10, fill=0)
        else:
            draw.text((_MARGIN, sep_y + 5), "No sessions recorded yet.", font=font_text_10, fill=0)

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
