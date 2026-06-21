import json
import os
from datetime import datetime
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_options_24, font_medium_18, font_text_10
from config.ui_components import draw_battery_icon
from config.paths import BASE_DIR

_W = 480
_H = 280
_MARGIN = 16
_HEADER_H = 52
_FOOTER_H = 20

HIGHLIGHTS_FILE = os.path.join(BASE_DIR, 'content', 'highlights.json')


def load_highlights():
    try:
        with open(HIGHLIGHTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_highlight(book_file, page_lines, page_num):
    """Save a snapshot of the current page as a highlight."""
    highlights = load_highlights()
    text = ' '.join(l.text for l in page_lines if l.kind == 'body')
    if not text.strip():
        return
    highlights.append({
        'book': os.path.splitext(book_file)[0],
        'page': page_num,
        'text': text[:300],
        'date': datetime.now().strftime('%d %b %Y'),
    })
    with open(HIGHLIGHTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(highlights, f, ensure_ascii=False, indent=2)


class SavedScreen:
    """Browse saved highlights."""

    def __init__(self, ereader):
        self.ereader = ereader
        self.highlights = load_highlights()
        self.index = max(0, len(self.highlights) - 1)  # start at newest
        self.draw()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw.rectangle((0, 0, _W, _HEADER_H), fill=0)
        draw.text((_MARGIN, 10), "Guardats", font=font_title, fill=0xFF)
        draw_battery_icon(draw, x=_W - 68, y=16, inverted=True)

        if not self.highlights:
            draw.text((_MARGIN, _HEADER_H + 20), "Cap fragment guardat.", font=font_options_24, fill=0)
            draw.text((_MARGIN, _HEADER_H + 52), "Prem 'p' mentre llegeixes", font=font_medium_18, fill=0)
            draw.text((_MARGIN, _HEADER_H + 76), "per guardar la pàgina actual.", font=font_medium_18, fill=0)
        else:
            h = self.highlights[self.index]
            top = _HEADER_H + 8

            # Book + page metadata
            meta = f"{h['book']}  —  pàg. {h['page'] + 1}  —  {h['date']}"
            draw.text((_MARGIN, top), meta, font=font_text_10, fill=0)
            draw.line((_MARGIN, top + 14, _W - _MARGIN, top + 14), fill=0, width=1)

            # Highlight text — wrap to display width
            import textwrap
            text_area_h = _H - _HEADER_H - _FOOTER_H - 30
            lines = textwrap.wrap(h['text'], width=52)
            y = top + 20
            for line in lines:
                if y + 20 > _H - _FOOTER_H:
                    draw.text((_MARGIN, y), '…', font=font_medium_18, fill=0)
                    break
                draw.text((_MARGIN, y), line, font=font_medium_18, fill=0)
                y += 22

            # Counter
            draw.line((0, _H - _FOOTER_H, _W, _H - _FOOTER_H), fill=0, width=1)
            counter = f"{self.index + 1} / {len(self.highlights)}"
            draw.text((_MARGIN, _H - 16), counter, font=font_text_10, fill=0)
            draw.text((_W - 160, _H - 16), "w/s=navegar  q=enrere", font=font_text_10, fill=0)

        display.draw_screen(img)

    def handle_key(self, key):
        if not self.highlights:
            if key == 'q':
                from screens.menu import MenuScreen
                self.ereader.switch_to(MenuScreen)
            return

        if key == 'w':
            self.index = max(0, self.index - 1)
            self.draw()
        elif key == 's':
            self.index = min(len(self.highlights) - 1, self.index + 1)
            self.draw()
        elif key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen)
