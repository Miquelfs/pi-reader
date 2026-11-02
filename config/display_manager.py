import threading
import time
from PIL import Image
from .display import epd


def fast_buffer(image):
    """Same bytes as epd.getbuffer() for a 480×280 landscape image, without the
    per-pixel Python loop (~134k iterations, most of a second on a Pi Zero)."""
    return image.convert('1').transpose(Image.ROTATE_90).tobytes()


class DisplayManager:
    def __init__(self):
        self.epd = epd
        self.initialized = False
        # Button callbacks, RSVP playback, the upload screen and auto-sleep all
        # run on different threads; the panel must only see one command stream.
        self.lock = threading.RLock()

    def init_display(self):
        with self.lock:
            if not self.initialized:
                self.epd.init(1)
                self.initialized = True

    def deep_clear(self):
        """Full panel reset — use between screen transitions to remove ghosting."""
        with self.lock:
            self.epd.reset()
            self.epd.init(1)
            self.initialized = True
            self.epd.ReadBusy()
            black = Image.new('1', (self.epd.height, self.epd.width), 0x00)
            self.epd.display_1Gray(fast_buffer(black))
            time.sleep(0.5)
            white = Image.new('1', (self.epd.height, self.epd.width), 0xFF)
            self.epd.display_1Gray(fast_buffer(white))
            time.sleep(0.5)

    def draw_screen(self, image, use_partial=False):
        with self.lock:
            self.init_display()
            self.epd.ReadBusy()
            self.epd.display_1Gray(fast_buffer(image))

    def sleep(self):
        """Put display into low-power sleep mode."""
        with self.lock:
            self.epd.sleep()
            self.initialized = False

    def wake(self):
        """Wake display from sleep and reinitialize."""
        with self.lock:
            self.epd.init(1)
            self.initialized = True
            self.epd.ReadBusy()


display = DisplayManager()
