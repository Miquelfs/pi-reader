from PIL import ImageFont
from config.paths import FONTS_DIR
import os

_LITERATA = 'Literata-VariableFont.ttf'
_SANS = 'AtkinsonHyperlegible-Regular.ttf'
_SANS_BOLD = 'AtkinsonHyperlegible-Bold.ttf'


def _load(filename, size, weight=None):
    try:
        font = ImageFont.truetype(os.path.join(FONTS_DIR, filename), size)
    except (IOError, OSError):
        return ImageFont.load_default()
    if weight:
        try:
            font.set_variation_by_name(weight)
        except (OSError, ValueError):
            pass   # FreeType without variation support: stays Regular
    return font


font_title          = _load(_LITERATA, 36)
font_options_24     = _load(_LITERATA, 24)
font_medium_18      = _load(_LITERATA, 18)
font_small_14       = _load(_LITERATA, 14)
font_large_22       = _load(_LITERATA, 22)
font_literata_italic = _load('Literata-Italic.ttf', 28)

# Headings and big single words
font_heading        = _load(_LITERATA, 26, 'SemiBold')
font_display        = _load(_LITERATA, 30, 'SemiBold')
font_rsvp           = _load(_LITERATA, 60, 'SemiBold')
font_rsvp_small     = _load(_LITERATA, 44, 'SemiBold')
font_rsvp_tiny      = _load(_LITERATA, 32, 'SemiBold')

# Labels, footers and small print: Literata breaks up at 10 px on a 1-bit panel
font_text_10        = _load(_SANS, 12)
font_label          = _load(_SANS_BOLD, 11)
font_body_16        = _load(_LITERATA, 16)
