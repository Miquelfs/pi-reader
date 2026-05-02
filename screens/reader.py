import os
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_medium_18
import textwrap

class BookScreenReader:
    def __init__(self, ereader, book_file, lines):
        self.ereader = ereader
        self.book_file = book_file
        self.path = "/home/miquel/pi-reader/content/library/"
        self.current_line = 0

        with open(self.path + self.book_file,"r") as f:
            content = f.read()
        self.lines = textwrap.wrap(content, width=30)

    def draw(self):
        Himage = Image.new('1', (display.epd.height, display.epd.width), 0xFF)
        draw = ImageDraw.Draw(Himage)
        
        y = 10
        for line in self.lines[self.current_line : self.current_line + 10]:
            draw.text((10, y), line, font=font_medium_18, fill=0)
            y += 25
            
        display.draw_screen(Himage, use_partial=True)

    def handle_key(self, key):
        if key == 's': # Scroll down
            self.current_line += 5
            self.draw()
        elif key =="w":
            self.current_line -=5
            self.draw()
        elif key == 'q': # Back to library
            from screens.library import LibraryScreen
            self.ereader.switch_to(LibraryScreen)
