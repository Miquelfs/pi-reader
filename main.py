import time
from config.display_manager import display
from screens.menu import MenuScreen

# ── GPIO pin assignments (BCM numbering) ─────────────────────────────────────
# Set GPIO_ENABLED = True only after buttons are physically wired.
# Floating (unwired) pins trigger spurious callbacks and cause constant redraws.
GPIO_ENABLED = False
PIN_UP     = 17
PIN_DOWN   = 22
PIN_SELECT = 23
PIN_BACK   = 27
# ─────────────────────────────────────────────────────────────────────────────

# Auto-sleep default (overridden by content/config.json at runtime)
SLEEP_AFTER_S = 300


class EReader:
    def __init__(self):
        self.current_screen = None
        self.running = True
        self._last_activity = time.time()
        self._sleeping = False
        self._gpio_available = False
        self._setup_gpio()

    def _setup_gpio(self):
        if not GPIO_ENABLED:
            print("GPIO disabled (GPIO_ENABLED=False) — using keyboard input.")
            return
        try:
            from gpiozero import Button
            btn_up     = Button(PIN_UP,     pull_up=True, bounce_time=0.05)
            btn_down   = Button(PIN_DOWN,   pull_up=True, bounce_time=0.05)
            btn_select = Button(PIN_SELECT, pull_up=True, bounce_time=0.05)
            btn_back   = Button(PIN_BACK,   pull_up=True, bounce_time=0.05)

            btn_up.when_pressed     = lambda: self._handle_key('w')
            btn_down.when_pressed   = lambda: self._handle_key('s')
            btn_select.when_pressed = lambda: self._handle_key('p')
            btn_back.when_pressed   = lambda: self._handle_key('q')

            # Keep references so gpiozero doesn't garbage-collect them
            self._buttons = [btn_up, btn_down, btn_select, btn_back]
            self._gpio_available = True
            print("GPIO buttons active.")
        except Exception as e:
            print(f"GPIO not available ({e}) — using keyboard input.")

    def _handle_key(self, key):
        self._last_activity = time.time()
        if self._sleeping:
            self._wake()
            return
        if self.current_screen:
            self.current_screen.handle_key(key)

    def switch_to(self, screen_class, **kwargs):
        display.deep_clear()
        self.current_screen = screen_class(self, **kwargs)
        self.current_screen.draw()
        self._last_activity = time.time()
        self._sleeping = False

    def _sleep_timeout(self):
        try:
            from utils.config_manager import get
            return get('sleep_timeout_min', 5) * 60
        except Exception:
            return SLEEP_AFTER_S

    def _check_sleep(self):
        if not self._sleeping and time.time() - self._last_activity > self._sleep_timeout():
            self._sleep()

    def _sleep(self):
        self._sleeping = True
        from screens.sleep_screen import build_sleep_image
        display.draw_screen(build_sleep_image())
        display.sleep()
        print("Display sleeping.")

    def _wake(self):
        self._sleeping = False
        display.wake()
        if self.current_screen:
            display.deep_clear()
            self.current_screen.draw()

    def run(self):
        display.init_display()

        # Boot into last-read book only when running as a systemd service.
        # Interactive SSH sessions (no JOURNAL_STREAM) always start at the menu.
        import os
        if 'JOURNAL_STREAM' in os.environ:
            from screens.reader import get_last_opened
            from utils.scanner import get_books_list
            last_book, last_page = get_last_opened()
            if last_book and last_book in [b.filename for b in get_books_list()]:
                from screens.reader import BookScreenReader
                self.switch_to(BookScreenReader, book_file=last_book, start_page=last_page)
            else:
                self.switch_to(MenuScreen)
        else:
            self.switch_to(MenuScreen)

        if self._gpio_available:
            while self.running:
                self._check_sleep()
                time.sleep(5)
        else:
            try:
                while self.running:
                    self._check_sleep()
                    key = input("w=up  s=down  p=select  q=back  z=quit: ").strip()
                    if key == 'z':
                        self.running = False
                    else:
                        self._handle_key(key)
            except EOFError:
                while self.running:
                    self._check_sleep()
                    time.sleep(5)


if __name__ == "__main__":
    ereader = EReader()
    ereader.run()
