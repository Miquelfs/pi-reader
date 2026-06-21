import time
from PIL import Image
from .display import epd


class DisplayManager:
    def __init__(self):
        self.epd = epd
        self.initialized = False

    def init_display(self):
        if not self.initialized:
            self.epd.init(1)
            self.initialized = True

    def deep_clear(self):
        """Full panel reset — use between screen transitions to remove ghosting."""
        self.epd.reset()
        self.epd.init(1)
        self.epd.ReadBusy()
        black = Image.new('1', (self.epd.height, self.epd.width), 0x00)
        self.epd.display_1Gray(self.epd.getbuffer(black))
        time.sleep(0.5)
        white = Image.new('1', (self.epd.height, self.epd.width), 0xFF)
        self.epd.display_1Gray(self.epd.getbuffer(white))
        time.sleep(0.5)

    def draw_screen(self, image, use_partial=False):
        self.init_display()
        self.epd.ReadBusy()
        self.epd.display_1Gray(self.epd.getbuffer(image))

    def sleep(self):
        """Put display into low-power sleep mode."""
        self.epd.sleep()
        self.initialized = False

    def wake(self):
        """Wake display from sleep and reinitialize."""
        self.epd.init(1)
        self.initialized = True
        self.epd.ReadBusy()


display = DisplayManager()
