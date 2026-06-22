import time
import threading
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_options_24, font_medium_18, font_text_10
from config.ui_components import draw_header, draw_footer

_W = 480
_H = 280

# WPM options cycled with 'w'/'s' while paused
_WPM_OPTIONS = [150, 200, 250, 300, 350]
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
        self._start_word = start_word
        self.book_file = book_file
        self.on_exit = on_exit  # called with current_word when leaving

        self._wpm_idx = _DEFAULT_WPM
        self._playing = False
        self._thread = None
        self._stop_event = threading.Event()
        self._session_start = time.time()

        self.draw()

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self):
        _HEADER_H = 54
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        # Header: "RSVP" centred title + WPM right-aligned in the bar
        draw_header(draw, "RSVP", w=_W, h=_HEADER_H)
        wpm = _WPM_OPTIONS[self._wpm_idx]
        wpm_str = f"{wpm} WPM"
        wpm_w = int(font_medium_18.getlength(wpm_str))
        draw.text((_W - wpm_w - 16, (_HEADER_H - 18) // 2), wpm_str, font=font_medium_18, fill=0xFF)

        # Central word — large, centred vertically in the reading zone
        word = self.words[self.current_word] if self.words else '—'
        word_w = int(font_title.getlength(word))
        word_x = max(16, (_W - word_w) // 2)
        word_y = _HEADER_H + (_H - _HEADER_H - 80) // 2 - 18
        draw.text((word_x, word_y), word, font=font_title, fill=0)

        # Progress bar
        if self.words:
            progress = self.current_word / len(self.words)
            bar_y = _H - 46
            bar_w = int((_W - 32) * progress)
            draw.rectangle((16, bar_y, _W - 16, bar_y + 8), outline=0)
            if bar_w > 0:
                draw.rectangle((16, bar_y, 16 + bar_w, bar_y + 8), fill=0)
            pct = int(progress * 100)
            draw.text((16, bar_y + 12), f"{pct}%  ·  word {self.current_word + 1} of {len(self.words)}", font=font_text_10, fill=0)

        status = "playing" if self._playing else "paused"
        draw_footer(draw, status, "p=pause  w/s=speed  q=exit", w=_W, h=_H, margin=16)

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
            if self.on_exit:
                self.on_exit(self.current_word)
            from screens.reader import BookScreenReader
            self.ereader.switch_to(BookScreenReader, book_file=self.book_file)
