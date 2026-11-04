import os
import json
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_display, font_body_16, font_medium_18, font_text_10
from config.ui_components import draw_label, draw_footer
from config.paths import LIBRARY_PATH, BOOKMARKS_FILE

_W = 480
_H = 280
_MARGIN = 16
_SPLIT_X = 292
_TASK_H = 24
_MAX_TASKS = 5


def _truncate(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + '…', font=font) > max_w:
        text = text[:-1]
    return text + '…'


def _current_book():
    """(title, fraction read) of the last opened book, or (None, 0)."""
    try:
        with open(BOOKMARKS_FILE, 'r') as f:
            bookmarks = json.load(f)
        book = bookmarks.get('_last_opened')
        if not book:
            return None, 0
        from utils.scanner import _load_meta
        stem = os.path.splitext(book)[0]
        title, _ = _load_meta(stem)
        with open(os.path.join(LIBRARY_PATH, stem + '.meta.json'), 'r', encoding='utf-8') as f:
            total = json.load(f).get('word_count') or 0
        word = (bookmarks.get(book) or {}).get('word', 0) if isinstance(bookmarks.get(book), dict) else 0
        return title, (word / total if total else 0)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None, 0


class TodayScreen:
    """Read-only day overview from Daybook. Draws from the cache at once, then refreshes in the background."""

    def __init__(self, ereader):
        self.ereader = ereader
        from utils.daybook_today import refresh_in_background
        refresh_in_background(on_done=self._redraw_if_visible)

    def _redraw_if_visible(self):
        with self.ereader._lock:
            if self.ereader.current_screen is self and not self.ereader._sleeping:
                self.draw()

    def draw(self):
        from utils.daybook_today import load, today_view
        from utils.stats import streak_days
        v = today_view(load())
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw.text((_MARGIN, 8), f"{v['weekday']} {v['day']}", font=font_display, fill=0)
        sub = ' · '.join(p for p in (v['month'], v['weather']) if p)
        draw_label(draw, (_MARGIN + 1, 50), sub)
        draw.line((_MARGIN, 70, _W - _MARGIN, 70), fill=0)

        # Left: tasks
        draw_label(draw, (_MARGIN, 80), 'Today')
        y = 98
        items = [(k, t) for k, t in v['tasks']] + [('birthday', f"Birthday: {n}") for n in v['birthdays']]
        if not items:
            msg = "Nothing due today." if not v['stale'] and v['updated'] else "No Daybook data yet."
            draw.text((_MARGIN, y), msg, font=font_body_16, fill=0)
        for kind, title in items[:_MAX_TASKS]:
            draw.rectangle((_MARGIN, y + 5, _MARGIN + 10, y + 15), outline=0)
            label = title + ('  (late)' if kind == 'overdue' else '')
            draw.text((_MARGIN + 18, y), _truncate(draw, label, font_body_16, _SPLIT_X - _MARGIN - 30), font=font_body_16, fill=0)
            y += _TASK_H
        if len(items) > _MAX_TASKS:
            draw.text((_MARGIN + 18, y), f"+ {len(items) - _MAX_TASKS} more", font=font_text_10, fill=0)

        # Right: duty or trip, reading, streak
        draw.line((_SPLIT_X, 80, _SPLIT_X, 226), fill=0)
        rx, rw = _SPLIT_X + 14, _W - _SPLIT_X - 14 - _MARGIN
        ry = 80
        if v['duty'] or v['trip']:
            draw_label(draw, (rx, ry), 'Trip' if v['trip'] and not v['duty'] else 'Duty')
            line = v['duty'] or v['trip']['trip']
            draw.text((rx, ry + 16), _truncate(draw, line, font_body_16, rw), font=font_body_16, fill=0)
            ry += 46
        title, frac = _current_book()
        if title:
            draw_label(draw, (rx, ry), 'Reading')
            draw.text((rx, ry + 16), _truncate(draw, title, font_body_16, rw), font=font_body_16, fill=0)
            draw.rectangle((rx, ry + 40, rx + rw, ry + 45), outline=0)
            draw.rectangle((rx, ry + 40, rx + int(rw * min(frac, 1)), ry + 45), fill=0)
            ry += 58
        streak = streak_days()
        draw_label(draw, (rx, ry), 'Streak')
        draw.text((rx, ry + 14), f"{streak} day{'s' if streak != 1 else ''}", font=font_medium_18, fill=0)

        # Bottom: a memory, then the footer
        if v['on_this_day']:
            draw.line((_MARGIN, 232, _W - _MARGIN, 232), fill=0)
            x = draw_label(draw, (_MARGIN, 240), 'On this day') + 8
            draw.text((x, 238), _truncate(draw, v['on_this_day'], font_text_10, _W - _MARGIN - x), font=font_text_10, fill=0)
        status = f"updated {v['updated']}" if v['updated'] else ("offline · old data" if v['stale'] else "offline")
        draw_footer(draw, status, "q = back", w=_W, h=_H, margin=_MARGIN)
        display.draw_screen(img)

    def handle_key(self, key):
        if key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start='Today')
