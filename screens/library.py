import os
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_medium_18
from utils.scanner import get_books_list

class LibraryScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.menu = 0
        self.page = 1
        self.pointerpos = [56, 84, 112, 140, 168, 196, 224]
        self.page_size = 7
        self.books = get_books_list()
    
    def draw(self):
        Himage = Image.new('1', (display.epd.height, display.epd.width), 0xFF)
        draw = ImageDraw.Draw(Himage)
        draw.text((60, 10), "Biblioteca", font=font_title, fill=0)
        
        start = (self.page - 1) * self.page_size
        current_books = self.books[start:start + self.page_size]
        
        for i, book in enumerate(current_books):
            draw.text((60, self.pointerpos[i]), book, font=font_medium_18, fill=0)
        
        if current_books:
            draw.rectangle((20, self.pointerpos[self.menu], 40, self.pointerpos[self.menu]+20), fill=0)
        
        display.draw_screen(Himage, use_partial=True)
    
    def handle_key(self, key):
        if key == 'w':  # up
            if self.menu > 0:
                self.menu -= 1
                self.draw()
            elif self.page > 1:
                self.page -= 1
                self.menu = 6
                self.draw()
        elif key == 's':  # down
            if self.menu < len(self.books) - (self.page-1)*self.page_size - 1:
                self.menu += 1
                self.draw()
            elif self.page * self.page_size < len(self.books):
                self.page += 1
                self.menu = 0
                self.draw()
        elif key == 'p': # enter
            print("Entering book")
            index = (self.page-1)*7 + self.menu
            selected_book_path = self.books[index]
            from screens.reader import BookScreenReader
            self.ereader.switch_to(BookScreenReader,book_file=selected_book_path)
        elif key == 'esc' or key == 'q':
            from screens.librarymenu import LibraryMenuScreen
            self.ereader.switch_to(LibraryMenuScreen)
