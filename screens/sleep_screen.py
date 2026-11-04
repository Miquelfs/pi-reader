import os
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw
from config.fonts import (font_title, font_options_24, font_medium_18, font_text_10,
                          font_display, font_body_16)
from config.ui_components import draw_label
from config.paths import BASE_DIR

_W = 480
_H = 280
_MARGIN = 20
_LOGO_PATH = os.path.join(BASE_DIR, 'assets', 'sleep_logo.png')

# Right panel starts where the Obelix image ends (~52% of width)
_SPLIT_X = int(_W * 0.52)
_RIGHT_X  = _SPLIT_X + 16
_RIGHT_W  = _W - _SPLIT_X - 16

_OFF_TEXT = "Off · safe to slide the switch"


def _streak():
    try:
        from utils.stats import streak_days, read_today
        return streak_days(), read_today()
    except Exception:
        return 0, False


def build_sleep_image(off=False):
    """Tomorrow's duty or trip day when Daybook has one (it stays on the panel unpowered),
    otherwise the Obelix screen. off=True adds the line that says it's safe to switch off."""
    try:
        from utils.daybook_today import load, tomorrow_view
        tomorrow = tomorrow_view(load())
    except Exception:
        tomorrow = None
    img = _tomorrow_image(tomorrow) if tomorrow else _obelix_image()
    if off:
        draw = ImageDraw.Draw(img)
        w = int(font_text_10.getlength(_OFF_TEXT))
        draw.rectangle((_W - w - 2 * _MARGIN, _H - 24, _W, _H), fill=0xFF)
        draw.text((_W - w - _MARGIN, _H - 20), _OFF_TEXT, font=font_text_10, fill=0)
    return img


def _tomorrow_image(t):
    img = Image.new('1', (_W, _H), 0xFF)
    draw = ImageDraw.Draw(img)
    draw_label(draw, (_MARGIN, 18), 'Tomorrow')
    draw.text((_MARGIN, 34), t['label'], font=font_display, fill=0)
    draw.line((_MARGIN, 78, _W - _MARGIN, 78), fill=0)

    y = 92
    if t['duty']:
        draw_label(draw, (_MARGIN, y), 'Duty')
        draw.text((_MARGIN, y + 16), t['duty'], font=font_options_24, fill=0)
        y += 56
    if t['trip']:
        draw_label(draw, (_MARGIN, y), 'Trip')
        draw.text((_MARGIN, y + 16), t['trip']['trip'], font=font_medium_18, fill=0)
        y += 42
        for line in textwrap.wrap(t['trip'].get('note') or '', width=52)[:2]:
            draw.text((_MARGIN, y), line, font=font_body_16, fill=0)
            y += 22
        y += 6
    if t['weather'] and y < _H - 60:
        draw_label(draw, (_MARGIN, y), 'Weather')
        draw.text((_MARGIN, y + 16), t['weather'], font=font_body_16, fill=0)

    streak, _ = _streak()
    if streak:
        draw.text((_MARGIN, _H - 20), f"{streak}-day reading streak", font=font_text_10, fill=0)
    return img


def _obelix_image():
    now = datetime.now()

    if os.path.exists(_LOGO_PATH):
        img = Image.open(_LOGO_PATH).convert('1')
    else:
        img = Image.new('1', (_W, _H), 0xFF)
        draw = ImageDraw.Draw(img)
        draw.text((20, 80), "Pi Reader", font=font_title, fill=0)

    draw = ImageDraw.Draw(img)

    # White out the entire right panel so we draw fresh every call
    draw.rectangle((_SPLIT_X, 0, _W, _H), fill=0xFF)

    name = "Pi Reader"
    name_w = int(font_options_24.getlength(name))
    draw.text((_SPLIT_X + (_RIGHT_W - name_w) // 2, 40), name, font=font_options_24, fill=0)

    date_str = now.strftime('%a, %d %b %Y')
    date_w = int(font_text_10.getlength(date_str))
    draw.text((_SPLIT_X + (_RIGHT_W - date_w) // 2, 74), date_str, font=font_text_10, fill=0)

    draw.line((_RIGHT_X, 92, _W - 12, 92), fill=0, width=1)

    streak, did_read = _streak()
    y_streak = 104
    if streak > 0:
        streak_label = f"{streak} day{'s' if streak != 1 else ''}"
        sl_w = int(font_medium_18.getlength(streak_label))
        draw.text((_SPLIT_X + (_RIGHT_W - sl_w) // 2, y_streak), streak_label, font=font_medium_18, fill=0)
        sub = "streak" if did_read else "streak — read today?"
        sub_w = int(font_text_10.getlength(sub))
        draw.text((_SPLIT_X + (_RIGHT_W - sub_w) // 2, y_streak + 24), sub, font=font_text_10, fill=0)
    else:
        prompt = "Read today?"
        pw = int(font_medium_18.getlength(prompt))
        draw.text((_SPLIT_X + (_RIGHT_W - pw) // 2, y_streak), prompt, font=font_medium_18, fill=0)

    return img
