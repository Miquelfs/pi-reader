import socket
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_medium_18, font_text_10
from config.ui_components import draw_battery_icon, get_battery_percent
from config.paths import LIBRARY_PATH
from utils.scanner import get_books_list

_W = 480
_H = 280
_MARGIN = 28
_HEADER_H = 44


def _get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return 'sense xarxa'


class ConfigScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self.draw()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        # Header
        title = "Configuració"
        tw = int(font_title.getlength(title))
        draw.rectangle((_MARGIN - 6, 6, _MARGIN + tw + 6, _HEADER_H - 6), fill=0)
        draw.text((_MARGIN, 8), title, font=font_title, fill=0xFF)
        draw_battery_icon(draw, x=_W - 72, y=14)
        draw.line((0, _HEADER_H, _W, _HEADER_H), fill=0, width=1)

        # System info
        ip = _get_ip()
        book_count = len(get_books_list())
        pct = get_battery_percent()
        battery_str = f"{pct}%" if pct is not None else "no disponible"

        rows = [
            ("IP",       ip),
            ("Bateria",  battery_str),
            ("Llibres",  str(book_count)),
            ("Upload",   f"http://{ip}:5000"),
            ("Guardats", f"http://{ip}:5000/highlights"),
        ]

        y = _HEADER_H + 14
        for label, value in rows:
            draw.text((_MARGIN, y), f"{label}:", font=font_text_10, fill=0)
            draw.text((_MARGIN + 80, y), value, font=font_medium_18, fill=0)
            y += 28

        # Footer
        draw.line((0, _H - 18, _W, _H - 18), fill=0, width=1)
        draw.text((_MARGIN, _H - 14), "q = enrere", font=font_text_10, fill=0)

        display.draw_screen(img)

    def handle_key(self, key):
        if key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=3)
