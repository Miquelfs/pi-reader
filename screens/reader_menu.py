import time as _time
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_options_24, font_text_10
from config.ui_components import draw_header

_W = 480
_H = 280
_MARGIN = 16
_HEADER_H = 54
_ITEM_H = 36


class ReaderMenuScreen:
    """Action menu triggered by pressing p while reading."""

    def __init__(self, ereader, reader_screen):
        self.ereader = ereader
        self.reader = reader_screen
        self.menu = 0
        size_label = f"Font: {reader_screen.font_size.capitalize()}"
        self.options = ['Save highlight']
        if reader_screen.toc:
            self.options.append('Contents')
        self.options += ['RSVP mode', size_label, 'Sync to Daybook', 'Cancel']
        self.draw()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Reading options", w=_W, h=_HEADER_H)

        _bb = font_options_24.getbbox("Ag")
        _text_h = _bb[3] - _bb[1]
        _text_offset = _bb[1]

        top = _HEADER_H + 6
        for i, opt in enumerate(self.options):
            y = top + i * _ITEM_H
            text_y = y + (_ITEM_H - _text_h) // 2 - _text_offset
            if i == self.menu:
                draw.rectangle((0, y, 4, y + _ITEM_H - 2), fill=0)
            draw.text((_MARGIN, text_y), opt, font=font_options_24, fill=0)

        display.draw_screen(img)

    def handle_key(self, key):
        if key == 'w':
            self.menu = max(0, self.menu - 1)
            self.draw()
        elif key == 's':
            self.menu = min(len(self.options) - 1, self.menu + 1)
            self.draw()
        elif key == 'p':
            self._confirm()
        elif key == 'q':
            self._cancel()

    def _confirm(self):
        selected = self.options[self.menu]

        if selected == 'Save highlight':
            from screens.saved_screen import save_highlight
            save_highlight(
                self.reader.book_file,
                self.reader.pages[self.reader.current_page],
                self.reader.current_page,
            )
            self.reader._draw_saved_confirmation()
            self.ereader.current_screen = self.reader

        elif selected == 'RSVP mode':
            from screens.rsvp import RSVPScreen
            from screens.reader import _save_bookmark
            _save_bookmark(self.reader.book_file, self.reader.current_page)
            start_word = self.reader._approx_word_for_page()
            self.ereader.switch_to(
                RSVPScreen,
                words=self.reader._words,
                start_word=start_word,
                book_file=self.reader.book_file,
            )

        elif selected.startswith('Font:'):
            from screens.reader import BookScreenReader, _SIZE_CYCLE, _save_bookmark
            current = self.reader.font_size
            next_size = _SIZE_CYCLE[(_SIZE_CYCLE.index(current) + 1) % len(_SIZE_CYCLE)]
            _save_bookmark(self.reader.book_file, self.reader.current_page, next_size)
            self.ereader.switch_to(
                BookScreenReader,
                book_file=self.reader.book_file,
                start_page=self.reader.current_page,
                font_size=next_size,
            )

        elif selected == 'Sync to Daybook':
            import os
            from utils.daybook_sync import sync_book
            from utils.scanner import _load_meta
            stem = os.path.splitext(self.reader.book_file)[0]
            title, author = _load_meta(stem)
            sync_book(title=title, author=author)
            # Brief feedback overlay
            self._show_toast("Syncing to Daybook…")
            self.ereader.current_screen = self.reader
            self.reader.draw()

        elif selected == 'Contents':
            from screens.toc_screen import TocScreen
            self.ereader.current_screen = TocScreen(self.ereader, self.reader.toc, self.reader)

        elif selected == 'Cancel':
            self._cancel()

    def _show_toast(self, message):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)
        draw.rectangle((80, 110, 400, 150), fill=0)
        draw.text((90, 122), message, font=font_options_24, fill=0xFF)
        display.draw_screen(img)
        _time.sleep(1.0)

    def _cancel(self):
        self.ereader.current_screen = self.reader
        self.reader.draw()
