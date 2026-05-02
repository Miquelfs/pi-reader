# config/display_manager.py
import time
from PIL import Image
from .display import epd

class DisplayManager:
    def __init__(self):
        self.epd = epd
        self.current_screen = None
        self.initialized = False
        
    def init_display(self):
        if not self.initialized:
            self.epd.init(1)
            self.initialized = True
    
    def deep_clear(self):
        """Full panel reset: black flash → white → ready for new content"""
        self.epd.reset()
        self.epd.init(1)
        self.epd.ReadBusy()
        
        # Black screen (full refresh)
        black = Image.new('1', (self.epd.height, self.epd.width), 0x00)
        self.epd.display_1Gray(self.epd.getbuffer(black))
        time.sleep(0.5)
        
        # White screen (full refresh)
        white = Image.new('1', (self.epd.height, self.epd.width), 0xFF)
        self.epd.display_1Gray(self.epd.getbuffer(white))
        time.sleep(0.5)
    
    def draw_screen(self, image, use_partial=False):
        self.init_display()
        self.epd.ReadBusy()
        self.epd.display_1Gray(self.epd.getbuffer(image))

# Global instance
display = DisplayManager()
