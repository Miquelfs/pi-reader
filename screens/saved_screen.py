import json
import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_medium_18, font_text_10
from config.ui_components import draw_battery_icon
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
    highlights.append({
        'book': os.path.splitext(book_file)[0],
        'page': page_num,
        'text': text[:300],
        'date': datetime.now().strftime('%d %b %Y'),
    })
    with open(HIGHLIGHTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(highlights, f, ensure_ascii=False, indent=2)


class SavedScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.highlights = load_highlights()
        self.index = max(0, len(self.highlights) - 1)
        self.draw()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        # Header
        title = "Guardats"
        tw = int(font_title.getlength(title))
        draw.rectangle((_MARGIN - 6, 6, _MARGIN + tw + 6, _HEADER_H - 6), fill=0)
        draw.text((_MARGIN, 8), title, font=font_title, fill=0xFF)
        draw_battery_icon(draw, x=_W - 72, y=14)
        draw.line((0, _HEADER_H, _W, _HEADER_H), fill=0, width=1)

        if not self.highlights:
            draw.text((_MARGIN, _HEADER_H + 24), "Cap fragment guardat.", font=font_medium_18, fill=0)
            draw.text((_MARGIN, _HEADER_H + 50), "Prem 'p' mentre llegeixes", font=font_medium_18, fill=0)
            draw.text((_MARGIN, _HEADER_H + 74), "per guardar la pàgina actual.", font=font_medium_18, fill=0)
        else:
            h = self.highlights[self.index]
            top = _HEADER_H + 8

            meta = f"{h['book']}  ·  pàg. {h['page'] + 1}  ·  {h['date']}"
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

        # Footer
        draw.line((0, _H - _FOOTER_H, _W, _H - _FOOTER_H), fill=0, width=1)
        if self.highlights:
            counter = f"{self.index + 1} / {len(self.highlights)}"
            draw.text((_MARGIN, _H - 14), counter, font=font_text_10, fill=0)
            draw.text((_W // 2 - 50, _H - 14), "w/s=navegar   q=enrere", font=font_text_10, fill=0)
        else:
            draw.text((_MARGIN, _H - 14), "q=enrere", font=font_text_10, fill=0)

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
