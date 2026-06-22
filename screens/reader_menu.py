import time as _time
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_options_24, font_text_10

_W = 480
_H = 280
_MARGIN = 16


class ReaderMenuScreen:
    """
    Small action menu triggered by pressing p while reading.
    Options: Save highlight | RSVP | Cancel
    """

    def __init__(self, ereader, reader_screen):
        self.ereader = ereader
        self.reader = reader_screen  # reference to return to
        self.menu = 0
        size_label = f"Font: {reader_screen.font_size.capitalize()}"
        self.options = ['Save highlight', 'RSVP mode', size_label, 'Sync to Daybook']
        if reader_screen.toc:
            self.options.append('Contents')
        self.options.append('Cancel')
        self.draw()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        # Dimmed background — draw current reader page first, then overlay
        # (We don't have access to it here, so use a clean panel with border)
        item_h = 30
        header_h = 28
        panel_h = header_h + len(self.options) * item_h + 8
        panel_top = max(20, (_H - panel_h) // 2)
        panel_bot = panel_top + panel_h

        draw.rectangle((56, panel_top, _W - 56, panel_bot), outline=0, width=2, fill=0xFF)
        draw.rectangle((56, panel_top, _W - 56, panel_top + header_h), fill=0)
        draw.text((70, panel_top + 8), "Reading options", font=font_text_10, fill=0xFF)

        top = panel_top + header_h + 4
        for i, opt in enumerate(self.options):
            y = top + i * item_h
            if i == self.menu:
                draw.rectangle((64, y, _W - 64, y + item_h - 2), fill=0)
                draw.text((70, y + 4), opt, font=font_options_24, fill=0xFF)
            else:
                draw.text((70, y + 4), opt, font=font_options_24, fill=0)

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
