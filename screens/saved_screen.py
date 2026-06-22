import json
import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18, font_text_10
from config.ui_components import draw_header, draw_footer
from config.paths import BASE_DIR

_W = 480
_H = 280
_MARGIN = 28
_HEADER_H = 44
_FOOTER_H = 18

HIGHLIGHTS_FILE = os.path.join(BASE_DIR, 'content', 'highlights.json')


def load_highlights():
    try:
        with open(HIGHLIGHTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_highlight(book_file, page_lines, page_num):
    highlights = load_highlights()
    text = ' '.join(l.text for l in page_lines if l.kind == 'body')
    if not text.strip():
        return
    stem = os.path.splitext(book_file)[0]
    date_str = datetime.now().strftime('%d %b %Y')
    highlights.append({
        'book': stem,
        'page': page_num,
        'text': text[:300],
        'date': date_str,
    })
    with open(HIGHLIGHTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(highlights, f, ensure_ascii=False, indent=2)
    # Push to Daybook in background — fire and forget
    try:
        from utils.daybook_sync import push_highlight
        from datetime import date as _date
        push_highlight(stem, page_num, text[:300], _date.today().isoformat())
    except Exception:
        pass


class SavedScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.highlights = load_highlights()
        self.index = max(0, len(self.highlights) - 1)
        self.draw()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Highlights", w=_W, h=_HEADER_H)

        if not self.highlights:
            draw.text((_MARGIN, _HEADER_H + 40), "No highlights saved yet.", font=font_medium_18, fill=0)
            draw.text((_MARGIN, _HEADER_H + 66), "Press p while reading to save a page.", font=font_text_10, fill=0)
        else:
            h = self.highlights[self.index]
            top = _HEADER_H + 8

            meta = f"{h['book']}  ·  p.{h['page'] + 1}  ·  {h['date']}"
            draw.text((_MARGIN, top), meta, font=font_text_10, fill=0)
            draw.line((_MARGIN, top + 14, _W - _MARGIN, top + 14), fill=0, width=1)

            lines = textwrap.wrap(h['text'], width=52)
            y = top + 20
            for line in lines:
                if y + 20 > _H - _FOOTER_H - 4:
                    draw.text((_MARGIN, y), '…', font=font_medium_18, fill=0)
                    break
                draw.text((_MARGIN, y), line, font=font_medium_18, fill=0)
                y += 22

        if self.highlights:
            counter = f"{self.index + 1} / {len(self.highlights)}"
            draw_footer(draw, counter, "w/s = navigate   q = back", w=_W, h=_H, margin=_MARGIN)
        else:
            draw_footer(draw, "", "q = back", w=_W, h=_H, margin=_MARGIN)

        display.draw_screen(img)

    def handle_key(self, key):
        if not self.highlights:
            if key == 'q':
                from screens.menu import MenuScreen
                self.ereader.switch_to(MenuScreen, start_index=1)
            return
        if key == 'w':
            self.index = max(0, self.index - 1)
            self.draw()
        elif key == 's':
            self.index = min(len(self.highlights) - 1, self.index + 1)
            self.draw()
        elif key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=1)
