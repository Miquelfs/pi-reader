import os
from datetime import datetime
from PIL import Image, ImageDraw
from config.fonts import font_title, font_options_24, font_text_10
from config.paths import BASE_DIR

_W = 480
_H = 280
_LOGO_PATH = os.path.join(BASE_DIR, 'assets', 'sleep_logo.png')

# These match extract_logo.py: tx = int(480*0.52)+20 = 269, rule_y=118
_DATE_X = int(_W * 0.52) + 20
_DATE_Y = 118 + 48  # rule_y + 48


def build_sleep_image():
    if os.path.exists(_LOGO_PATH):
        img = Image.open(_LOGO_PATH).convert('RGB')
        draw = ImageDraw.Draw(img)
        date_str = datetime.now().strftime('%d %b %Y')
        # White out placeholder, write today's date
        draw.rectangle((_DATE_X, _DATE_Y - 2, _W - 8, _DATE_Y + 20), fill=(255, 255, 255))
        draw.text((_DATE_X, _DATE_Y), date_str, font=font_text_10, fill=0)
        img = img.convert('L').point(lambda p: 0 if p < 210 else 255, '1')
    else:
        # Fallback until logo is generated
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)
        draw.text((20, 80), "Pi Reader", font=font_title, fill=0)
        draw.text((20, 130), "Miquel Farré", font=font_options_24, fill=0)
        draw.line((20, 160, _W - 20, 160), fill=0, width=1)
        draw.text((20, 172), datetime.now().strftime('%d %b %Y'), font=font_text_10, fill=0)

    return img
