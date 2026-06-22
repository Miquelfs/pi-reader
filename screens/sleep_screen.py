import os
from datetime import datetime
from PIL import Image, ImageDraw
from config.fonts import font_title, font_options_24, font_medium_18, font_text_10
from config.paths import BASE_DIR

_W = 480
_H = 280
_LOGO_PATH = os.path.join(BASE_DIR, 'assets', 'sleep_logo.png')

# Right panel starts where the Obelix image ends (~52% of width)
_SPLIT_X = int(_W * 0.52)
_RIGHT_X  = _SPLIT_X + 16
_RIGHT_W  = _W - _SPLIT_X - 16


def build_sleep_image():
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

    # ── Name ──────────────────────────────────────────────────────────────────
    name = "Pi Reader"
    name_w = int(font_options_24.getlength(name))
    name_x = _SPLIT_X + (_RIGHT_W - name_w) // 2
    draw.text((name_x, 40), name, font=font_options_24, fill=0)

    # ── Date ──────────────────────────────────────────────────────────────────
    date_str = now.strftime('%a, %d %b %Y')
    date_w = int(font_text_10.getlength(date_str))
    date_x = _SPLIT_X + (_RIGHT_W - date_w) // 2
    draw.text((date_x, 74), date_str, font=font_text_10, fill=0)

    # Thin separator
    draw.line((_RIGHT_X, 92, _W - 12, 92), fill=0, width=1)

    # ── Streak ────────────────────────────────────────────────────────────────
    try:
        from utils.stats import streak_days, read_today
        streak = streak_days()
        did_read = read_today()
    except Exception:
        streak = 0
        did_read = False

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
