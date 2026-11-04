import time
import threading
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_rsvp, font_rsvp_small, font_rsvp_tiny, font_text_10

_W = 480
_H = 280
_FOCUS_X = 200     # a little left of centre: most of a word sits after its focus letter
_EDGE = 12

# Each word is a full panel refresh, so the top speeds are only reachable if
# the refresh is quick enough — the loop just runs as fast as the panel allows.
_WPM_OPTIONS = [60, 100, 150, 200, 250]
_DEFAULT_WPM = 2  # index into _WPM_OPTIONS → 150 WPM


def _wpm_to_delay(wpm):
    return 60.0 / wpm


def focus_index(word):
    """Optimal recognition point: the letter the eye should land on (Spritz-style)."""
    n = len(word)
    return 0 if n <= 1 else 1 if n <= 5 else 2 if n <= 9 else 3 if n <= 13 else 4


class RSVPScreen:
    """
    Rapid Serial Visual Presentation reader.
    Receives the full word list and starting position from BookScreenReader.
    Controls: p=pause/resume, s=faster, w=slower, q=back to book
    """

    def __init__(self, ereader, words, start_word=0, book_file='', font_size=None):
        self.ereader = ereader
        self.words = words
        self.current_word = start_word
        self._start_word = start_word
        self.book_file = book_file
        self.font_size = font_size

        self._wpm_idx = _DEFAULT_WPM
        self._playing = False
        self._thread = None
        self._stop_event = threading.Event()
        self._session_start = time.time()


    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self):
        """Only the word. One letter (the recognition point) stays at the same x on every
        word, marked by two ticks, so the eye never moves. Paused shows the speed."""
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        word = self.words[self.current_word] if self.words else ''
        if word:
            i = focus_index(word)
            # largest size that fits; a long word may have to shift, then the ticks follow it
            for font in (font_rsvp, font_rsvp_small, font_rsvp_tiny):
                if font.getlength(word) <= _W - 2 * _EDGE:
                    break
            before = font.getlength(word[:i]) + font.getlength(word[i]) / 2
            x = _FOCUS_X - before
            x = max(_EDGE, min(x, _W - _EDGE - font.getlength(word)))
            fx = x + before
            ascent, descent = font.getmetrics()
            y = (_H - ascent - descent) // 2
            draw.text((x, y), word, font=font, fill=0)
            draw.line((fx, y - 16, fx, y - 4), fill=0, width=2)   # above any accent
            bottom = y + ascent + descent
            draw.line((fx, bottom + 4, fx, bottom + 16), fill=0, width=2)

        if self.words:
            draw.rectangle((0, _H - 3, int(_W * self.current_word / len(self.words)), _H - 2), fill=0)
        if not self._playing:
            hint = f"paused · {_WPM_OPTIONS[self._wpm_idx]} wpm"
            draw.text(((_W - font_text_10.getlength(hint)) / 2, _H - 26), hint, font=font_text_10, fill=0)

        display.draw_screen(img)

    # ── Playback ──────────────────────────────────────────────────────────────

    @property
    def busy(self):
        """Keeps auto-sleep away while playing — no key presses happen then."""
        return self._playing

    def _play_loop(self):
        while not self._stop_event.is_set():
            if self.current_word >= len(self.words) - 1:
                self._playing = False
                self.draw()
                break
            t0 = time.time()
            self.current_word += 1
            self.draw()
            delay = _wpm_to_delay(_WPM_OPTIONS[self._wpm_idx])
            self._stop_event.wait(timeout=max(0, delay - (time.time() - t0)))

    def _start(self):
        self._stop_event.clear()
        self._playing = True
        self._thread = threading.Thread(target=self._play_loop, daemon=True)
        self._thread.start()

    def _pause(self):
        self._playing = False
        self._stop_event.set()
        # Let an in-flight frame finish so it can't land on top of the next screen
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=5)

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
            rsvp_words = max(0, self.current_word - self._start_word)
            rsvp_dur   = time.time() - self._session_start
            if rsvp_words > 0:
                import os
                from utils.stats import record_session
                record_session(
                    book=os.path.splitext(self.book_file)[0],
                    pages=0,
                    words=0,
                    duration_s=0,
                    rsvp_words=rsvp_words,
                    rsvp_duration_s=rsvp_dur,
                )
            from screens.reader import BookScreenReader
            self.ereader.switch_to(BookScreenReader, book_file=self.book_file,
                                   start_word=self.current_word, font_size=self.font_size)
