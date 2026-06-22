from PIL import ImageFont
from config.paths import FONTS_DIR
import os

def _load(filename, size):
    try:
        return ImageFont.truetype(os.path.join(FONTS_DIR, filename), size)
    except (IOError, OSError):
        return ImageFont.load_default()

font_title          = _load('Literata-VariableFont.ttf', 36)
font_options_24     = _load('Literata-VariableFont.ttf', 24)
font_medium_18      = _load('Literata-VariableFont.ttf', 18)
font_small_14       = _load('Literata-VariableFont.ttf', 14)
font_large_22       = _load('Literata-VariableFont.ttf', 22)
font_text_10        = _load('Literata-VariableFont.ttf', 10)
font_literata_italic = _load('Literata-Italic.ttf', 28)
