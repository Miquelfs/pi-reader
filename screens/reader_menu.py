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
        self.options = ['Guardar fragment', 'Mode RSVP', 'Cancel·lar']
        self.draw()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        # Dimmed background — draw current reader page first, then overlay
        # (We don't have access to it here, so use a clean panel with border)
        draw.rectangle((60, 60, _W - 60, _H - 60), outline=0, width=2, fill=0xFF)
        draw.rectangle((60, 60, _W - 60, 96), fill=0)
        draw.text((76, 68), "Opcions de lectura", font=font_text_10, fill=0xFF)

        item_h = 38
        top = 100
        for i, opt in enumerate(self.options):
            y = top + i * item_h
            if i == self.menu:
                draw.rectangle((68, y - 2, _W - 68, y + item_h - 6), fill=0)
                draw.text((76, y), opt, font=font_options_24, fill=0xFF)
            else:
                draw.text((76, y), opt, font=font_options_24, fill=0)

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
        if self.menu == 0:
            # Save highlight
            from screens.saved_screen import save_highlight
            save_highlight(
                self.reader.book_file,
                self.reader.pages[self.reader.current_page],
                self.reader.current_page,
            )
            self.reader._draw_saved_confirmation()
            # Return to reader (confirmation redraws it)
            self.ereader.current_screen = self.reader

        elif self.menu == 1:
            # Launch RSVP
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

        elif self.menu == 2:
            self._cancel()

    def _cancel(self):
        self.ereader.current_screen = self.reader
        self.reader.draw()
