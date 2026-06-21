import time
from config.display_manager import display
from config.ui_components import get_battery_percent
from screens.menu import MenuScreen

# ── GPIO pin assignments (BCM numbering) ─────────────────────────────────────
# Fill in once buttons are physically wired. Suggested free pins:
PIN_UP     = 17
PIN_DOWN   = 22
PIN_SELECT = 23
PIN_BACK   = 27
# ─────────────────────────────────────────────────────────────────────────────

# Auto-sleep: shut down display after this many seconds of inactivity
SLEEP_AFTER_S = 300  # 5 minutes; set to None to disable

# Battery warning threshold (%)
LOW_BATTERY_WARN = 15


class EReader:
    def __init__(self):
        self.current_screen = None
        self.running = True
        self._last_activity = time.time()
        self._sleeping = False
        self._gpio_available = False
        self._setup_gpio()

    def _setup_gpio(self):
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

    def _check_sleep(self):
        if SLEEP_AFTER_S is None:
            return
        if not self._sleeping and time.time() - self._last_activity > SLEEP_AFTER_S:
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

    def _check_battery(self):
        pct = get_battery_percent()
        if pct is not None and pct <= LOW_BATTERY_WARN:
            print(f"LOW BATTERY: {pct}%")
            # TODO: overlay a low-battery warning on current screen

    def run(self):
        display.init_display()

        # Boot directly into last-read book if one exists
        from screens.reader import get_last_opened
        from utils.scanner import get_books_list
        last_book, last_page = get_last_opened()
        if last_book and last_book in get_books_list():
            from screens.reader import BookScreenReader
            self.switch_to(BookScreenReader, book_file=last_book, start_page=last_page)
        else:
            self.switch_to(MenuScreen)

        if self._gpio_available:
            # GPIO callbacks handle input — just run the maintenance loop
            while self.running:
                self._check_sleep()
                self._check_battery()
                time.sleep(5)
        else:
            # Keyboard fallback for development over SSH
            while self.running:
                self._check_sleep()
                self._check_battery()
                key = input("w=up  s=down  p=select  q=back  z=quit: ").strip()
                if key == 'z':
                    self.running = False
                else:
                    self._handle_key(key)


if __name__ == "__main__":
    ereader = EReader()
    ereader.run()
