from config.fonts import font_text_10
from utils.battery import read_battery_percent

# Battery icon dimensions
_BAT_W = 24   # outer shell width
_BAT_H = 12   # outer shell height
_BAT_TIP = 3  # nub on the right


def draw_battery_icon(draw, x, y):
    """
    Draw a battery icon + percentage text at (x, y) using top-left origin.
    Reads live from PiSugar2; draws nothing if hardware is absent.
    Total bounding box is roughly (_BAT_W + _BAT_TIP + 28) x _BAT_H.
    """
    pct = read_battery_percent()
    if pct is None:
        return

    # Outer shell
    draw.rectangle((x, y, x + _BAT_W, y + _BAT_H), outline=0, fill=255)
    # Positive nub
    nub_top = y + 3
    nub_bot = y + _BAT_H - 3
    draw.rectangle((x + _BAT_W, nub_top, x + _BAT_W + _BAT_TIP, nub_bot), fill=0)
    # Fill bar — 2px padding inside the shell on all sides
    fill_max = _BAT_W - 4
    fill_w = max(0, int(fill_max * pct / 100))
    if fill_w > 0:
        draw.rectangle((x + 2, y + 2, x + 2 + fill_w, y + _BAT_H - 2), fill=0)

    # Percentage label to the right of the icon
    label = f"{pct}%"
    draw.text((x + _BAT_W + _BAT_TIP + 4, y), label, font=font_text_10, fill=0)
