import os
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_medium_18
from config.ui_components import draw_battery_icon
from utils.scanner import LIBRARY_PATH
import textwrap

LINES_PER_PAGE = 10
SCROLL_STEP = LINES_PER_PAGE
WRAP_WIDTH = 58  # characters per line at font_medium_18 on 480px canvas


class BookScreenReader:
    def __init__(self, ereader, book_file):
        self.ereader = ereader
        self.book_file = book_file
        self.current_line = 0

        with open(os.path.join(LIBRARY_PATH, book_file), "r") as f:
            content = f.read()

        # textwrap.wrap splits on word boundaries only
        self.lines = textwrap.wrap(content, width=WRAP_WIDTH)
        self.max_line = max(0, len(self.lines) - LINES_PER_PAGE)

    def draw(self):
        Himage = Image.new('1', (display.epd.height, display.epd.width), 0xFF)
        draw = ImageDraw.Draw(Himage)

        y = 10
        for line in self.lines[self.current_line: self.current_line + LINES_PER_PAGE]:
            draw.text((10, y), line, font=font_medium_18, fill=0)
            y += 25

        draw_battery_icon(draw, x=425, y=8)
        display.draw_screen(Himage, use_partial=True)

    def handle_key(self, key):
        if key == 's':  # page down
            self.current_line = min(self.current_line + SCROLL_STEP, self.max_line)
            self.draw()
        elif key == 'w':  # page up
            self.current_line = max(self.current_line - SCROLL_STEP, 0)
            self.draw()
        elif key == 'q':  # back to library
            from screens.library import LibraryScreen
            self.ereader.switch_to(LibraryScreen)
