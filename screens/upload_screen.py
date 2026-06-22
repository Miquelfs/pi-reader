import threading
import socket
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_options_24, font_text_10
from config.ui_components import draw_battery_icon

_W = 480
_H = 280
_MARGIN = 28
_HEADER_H = 44

_server_thread = None


def _get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '?.?.?.?'


def _run_server():
    from app.file_transfer import app
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


class UploadScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self._start_server()
        self.draw()

    def _start_server(self):
        global _server_thread
        if _server_thread and _server_thread.is_alive():
            return
        _server_thread = threading.Thread(target=_run_server, daemon=True)
        _server_thread.start()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        # Header
        title = "Puja un llibre"
        tw = int(font_title.getlength(title))
        draw.rectangle((_MARGIN - 6, 6, _MARGIN + tw + 6, _HEADER_H - 6), fill=0)
        draw.text((_MARGIN, 8), title, font=font_title, fill=0xFF)
        draw_battery_icon(draw, x=_W - 72, y=14)
        draw.line((0, _HEADER_H, _W, _HEADER_H), fill=0, width=1)

        ip = _get_ip()

        draw.text((_MARGIN, _HEADER_H + 18), "Obre al teu navegador:", font=font_options_24, fill=0)

        # URL box
        url = f"http://{ip}:5000"
        url_w = int(font_options_24.getlength(url))
        box_x = (_W - url_w) // 2
        draw.rectangle((box_x - 12, _HEADER_H + 52, box_x + url_w + 12, _HEADER_H + 86), outline=0, width=2)
        draw.text((box_x, _HEADER_H + 58), url, font=font_options_24, fill=0)

        draw.text((_MARGIN, _HEADER_H + 100), "Guardats disponibles a:", font=font_text_10, fill=0)
        highlights_url = f"http://{ip}:5000/highlights"
        draw.text((_MARGIN, _HEADER_H + 114), highlights_url, font=font_text_10, fill=0)

        # Footer
        draw.line((0, _H - 18, _W, _H - 18), fill=0, width=1)
        draw.text((_MARGIN, _H - 14), "q = tancar i tornar", font=font_text_10, fill=0)

        display.draw_screen(img)

    def handle_key(self, key):
        if key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=2)
