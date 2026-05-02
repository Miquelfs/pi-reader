from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_options_24


class MenuScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.menu = 0
        self.options = ['Biblioteca', 'Guardats', 'Mode de Lectura', 'Configuració']
        self.pointerpos = [56, 100, 144, 188]
    
    def draw(self):
        Himage = Image.new('1', (display.epd.height, display.epd.width), 0xFF)
        draw = ImageDraw.Draw(Himage)
        draw.text((60, 10), "Menu", font=font_title, fill=0)
        for i, opt in enumerate(self.options):
            draw.text((60, self.pointerpos[i]), f'- {opt}', font=font_options_24, fill=0)
        draw.rectangle((20, self.pointerpos[self.menu], 40, self.pointerpos[self.menu]+20), fill=0)
        display.draw_screen(Himage, use_partial=True)
    
    def handle_key(self, key):
        if key == 'w':  # up
            self.menu = max(0, self.menu - 1)
            self.draw()
        elif key == 's':  # down
            self.menu = min(3, self.menu + 1)
            self.draw()
        elif key == 'p':
            if self.menu == 0:  # Library and Comics Screen
                from screens.librarymenu import LibraryMenuScreen
                self.ereader.switch_to(LibraryMenuScreen)
