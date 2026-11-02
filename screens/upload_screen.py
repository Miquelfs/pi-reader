import threading
import socket
from PIL import Image, ImageDraw
from config.display_manager import display
from config.fonts import font_options_24, font_medium_18, font_text_10
from config.ui_components import draw_header, draw_footer

_W = 480
_H = 280
_MARGIN = 28
_HEADER_H = 54

_server = None


def _get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '?.?.?.?'


def _start_server():
    global _server
    if _server:
        return
    from werkzeug.serving import make_server
    from app.file_transfer import app
    _server = make_server('0.0.0.0', 5000, app, threaded=True)
    threading.Thread(target=_server.serve_forever, daemon=True).start()


def _stop_server():
    global _server
    if _server:
        _server.shutdown()
        _server = None


class UploadScreen:
    def __init__(self, ereader):
        self.ereader = ereader
        self._dot_cycle = 0
        self._stop = threading.Event()
        _start_server()
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def _poll_loop(self):
        # Only redraw when the conversion status changes — every frame is a
        # full e-ink refresh, and drawing while asleep would wake the panel.
        from app.text_converter import conversion_state
        last = (conversion_state['status'], conversion_state['filename'])
        while not self._stop.wait(timeout=3):
            now = (conversion_state['status'], conversion_state['filename'])
            if now == last:
                continue
            last = now
            with self.ereader._lock:
                if self.ereader.current_screen is not self or self.ereader._sleeping:
                    continue
                self._dot_cycle = (self._dot_cycle + 1) % 3
                try:
                    self.draw()
                except Exception as e:
                    print(f"Upload screen redraw failed: {e}")

    def draw(self):
        from app.text_converter import conversion_state
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)

        draw_header(draw, "Upload", w=_W, h=_HEADER_H)

        ip = _get_ip()
        status = conversion_state['status']

        if status == 'converting':
            dots = '.' * (self._dot_cycle + 1)
            title = conversion_state['last_title'] or conversion_state['filename']
            draw.text((_MARGIN, _HEADER_H + 24), f"Converting{dots}", font=font_options_24, fill=0)
            draw.text((_MARGIN, _HEADER_H + 60), title, font=font_medium_18, fill=0)
            draw.text((_MARGIN, _HEADER_H + 88), "This takes about a minute on the Pi.", font=font_text_10, fill=0)
        elif status == 'done':
            title = conversion_state['last_title']
            draw.text((_MARGIN, _HEADER_H + 24), "Done!", font=font_options_24, fill=0)
            draw.text((_MARGIN, _HEADER_H + 60), f'"{title}" is ready to read.', font=font_medium_18, fill=0)
        elif status == 'error':
            draw.text((_MARGIN, _HEADER_H + 24), "Conversion failed.", font=font_options_24, fill=0)
            draw.text((_MARGIN, _HEADER_H + 56), "Check the file format and try again.", font=font_text_10, fill=0)
        else:
            # Idle — show normal upload UI
            draw.text((_MARGIN, _HEADER_H + 18), "Open in your browser:", font=font_options_24, fill=0)
            url = f"http://{ip}:5000"
            url_w = int(font_options_24.getlength(url))
            box_x = (_W - url_w) // 2
            draw.rectangle((box_x - 12, _HEADER_H + 52, box_x + url_w + 12, _HEADER_H + 86), outline=0, width=2)
            draw.text((box_x, _HEADER_H + 58), url, font=font_options_24, fill=0)
            draw.text((_MARGIN, _HEADER_H + 100), "Download highlights:", font=font_text_10, fill=0)
            highlights_url = f"http://{ip}:5000/highlights"
            draw.text((_MARGIN, _HEADER_H + 114), highlights_url, font=font_text_10, fill=0)

        draw_footer(draw, "", "q = back", w=_W, h=_H, margin=_MARGIN)
        display.draw_screen(img)

    def handle_key(self, key):
        if key == 'q':
            self._stop.set()
            _stop_server()
            from screens.menu import MenuScreen
            self.ereader.switch_to(MenuScreen, start_index=3)
