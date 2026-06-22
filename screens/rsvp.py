import time
import threading
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_options_24, font_text_10

_W = 480
_H = 280

# WPM options cycled with 'w'/'s' while paused
_WPM_OPTIONS = [150, 200, 250]
_DEFAULT_WPM = 1  # index into _WPM_OPTIONS → 200 WPM


def _wpm_to_delay(wpm):
    return 60.0 / wpm


class RSVPScreen:
    """
    Rapid Serial Visual Presentation reader.
    Receives the full word list and starting position from BookScreenReader.
    Controls: p=pause/resume, s=faster, w=slower, q=back to book
    """

    def __init__(self, ereader, words, start_word=0, book_file='', on_exit=None):
        self.ereader = ereader
        self.words = words
        self.current_word = start_word
        self.book_file = book_file
        self.on_exit = on_exit  # called with current_word when leaving

        self._wpm_idx = _DEFAULT_WPM
        self._playing = False
        self._thread = None
        self._stop_event = threading.Event()

        self.draw()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        # Header
        draw.rectangle((0, 0, _W, 52), fill=0)
        draw.text((16, 10), "RSVP", font=font_title, fill=0xFF)
        wpm = _WPM_OPTIONS[self._wpm_idx]
        draw.text((_W - 90, 10), f"{wpm} WPM", font=font_options_24, fill=0xFF)


        # Central word — large, centred
        word = self.words[self.current_word] if self.words else '—'
        # Use font_title (36pt) for the word itself
        word_w = font_title.getlength(word)
        x = max(16, (_W - word_w) // 2)
        draw.text((x, 110), word, font=font_title, fill=0)

        # Fixation guide: vertical bar at the optimal recognition point (~30% from left)
        fix_x = _W // 3
        draw.line((fix_x, 100, fix_x, 155), fill=0, width=1)

        # Progress bar
        if self.words:
            progress = self.current_word / len(self.words)
            bar_w = int((_W - 32) * progress)
            draw.rectangle((16, 200, 16 + bar_w, 208), fill=0)
            draw.rectangle((16, 200, _W - 16, 208), outline=0)
            pct = int(progress * 100)
            draw.text((16, 214), f"{pct}%  —  {self.current_word + 1} / {len(self.words)} words", font=font_text_10, fill=0)

        # Footer controls
        draw.line((0, _H - 20, _W, _H - 20), fill=0, width=1)
        status = "▶ a reproduir" if self._playing else "⏸ pausat"
        draw.text((16, _H - 16), status, font=font_text_10, fill=0)
        draw.text((_W - 200, _H - 16), "p=pausa  w/s=vel  q=sortir", font=font_text_10, fill=0)

        display.draw_screen(img)

    # ── Playback ──────────────────────────────────────────────────────────────

    def _play_loop(self):
        while not self._stop_event.is_set():
            if self.current_word >= len(self.words) - 1:
                self._playing = False
                self.draw()
                break
            self.current_word += 1
            self.draw()
            delay = _wpm_to_delay(_WPM_OPTIONS[self._wpm_idx])
            self._stop_event.wait(timeout=delay)

    def _start(self):
        self._stop_event.clear()
        self._playing = True
        self._thread = threading.Thread(target=self._play_loop, daemon=True)
        self._thread.start()

    def _pause(self):
        self._playing = False
        self._stop_event.set()

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_key(self, key):
        if key == 'p':
            if self._playing:
                self._pause()
                self.draw()
            else:
                self._start()

        elif key == 's':
            # Faster
            self._wpm_idx = min(len(_WPM_OPTIONS) - 1, self._wpm_idx + 1)
            self.draw()

        elif key == 'w':
            # Slower
            self._wpm_idx = max(0, self._wpm_idx - 1)
            self.draw()

        elif key == 'q':
            self._pause()
            if self.on_exit:
                self.on_exit(self.current_word)
            from screens.reader import BookScreenReader
            self.ereader.switch_to(BookScreenReader, book_file=self.book_file)
