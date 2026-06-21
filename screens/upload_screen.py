import threading
import socket
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_title, font_options_24, font_text_10

_W = 480
_H = 280

_server_thread = None
_server_running = False


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
    """
    Shows the device IP and starts the Flask upload server.
    User opens http://<ip>:5000 on their phone/Mac to upload books.
    Pressing q stops the server and returns to the menu.
    """

    def __init__(self, ereader):
        self.ereader = ereader
        self._start_server()
        self.draw()

    def _start_server(self):
        global _server_thread, _server_running
        if _server_thread and _server_thread.is_alive():
            return
        _server_running = True
        _server_thread = threading.Thread(target=_run_server, daemon=True)
        _server_thread.start()

    def draw(self):
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw.rectangle((0, 0, _W, 52), fill=0)
        draw.text((16, 10), "Puja un llibre", font=font_title, fill=0xFF)

        ip = _get_ip()
        url = f"http://{ip}:5000"

        draw.text((16, 70), "Connecta al mateix WiFi i", font=font_options_24, fill=0)
        draw.text((16, 100), "obre al teu navegador:", font=font_options_24, fill=0)

        # URL prominently
        draw.rectangle((12, 130, _W - 12, 168), outline=0, width=2)
        url_w = font_options_24.getlength(url)
        draw.text(((_W - url_w) // 2, 136), url, font=font_options_24, fill=0)

        draw.text((16, 180), "El servidor està actiu.", font=font_text_10, fill=0)
        draw.text((16, 196), "Els llibres pujats apareixeran a la biblioteca.", font=font_text_10, fill=0)

        draw.line((0, _H - 20, _W, _H - 20), fill=0, width=1)
        draw.text((16, _H - 16), "q = tancar i tornar al menú", font=font_text_10, fill=0)

        display.draw_screen(img)

    def handle_key(self, key):
        if key == 'q':
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen)
