import os
from datetime import datetime
from PIL import Image, ImageDraw
from config.fonts import font_title, font_options_24, font_text_10
from config.paths import BASE_DIR

_W = 480
_H = 280
_LOGO_PATH = os.path.join(BASE_DIR, 'assets', 'sleep_logo.png')


def build_sleep_image():
    """
    Build the 1-bit sleep screen image.
    Uses assets/sleep_logo.png if available, otherwise a plain text fallback.
    """
    if os.path.exists(_LOGO_PATH):
        img = Image.open(_LOGO_PATH).convert('1')
        # Overwrite date in bottom-right corner (it changes every day)
        draw = ImageDraw.Draw(img)
        date_str = datetime.now().strftime('%d %b %Y')
        draw.rectangle((_W - 110, _H - 16, _W, _H), fill=0xFF)
        draw.text((_W - 108, _H - 14), date_str, font=font_text_10, fill=0)
    else:
        # Fallback: plain sleep screen until logo is generated
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)
        draw.text((20, 80), "Pi Reader", font=font_title, fill=0)
        draw.text((20, 130), "Miquel Farré", font=font_options_24, fill=0)
        draw.line((20, 160, _W - 20, 160), fill=0, width=1)
        date_str = datetime.now().strftime('%d %b %Y')
        draw.text((20, 170), date_str, font=font_options_24, fill=0)

    return img
