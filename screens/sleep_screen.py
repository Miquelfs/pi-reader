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
        # Load as RGB so we can draw coloured (grey) date text before converting
        img = Image.open(_LOGO_PATH).convert('RGB')
        draw = ImageDraw.Draw(img)
        date_str = datetime.now().strftime('%d %b %Y')
        # Overwrite the placeholder date area with today's date
        # Position matches the text block in extract_logo.py (tx ≈ 265, y=175)
        draw.rectangle((265, 170, _W - 8, 190), fill=(255, 255, 255))
        draw.text((265, 174), date_str, font=font_options_24, fill=0)
        img = img.convert('L').point(lambda p: 0 if p < 200 else 255, '1')
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
