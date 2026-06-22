from config.fonts import font_text_10, font_options_24
from utils.battery import read_battery_percent

_BAT_W = 24
_BAT_H = 12
_BAT_TIP = 3

# Cached so every draw() call doesn't hit I2C
_cached_pct = None
_cache_calls = 0
_CACHE_EVERY = 20  # refresh every 20 draw calls (~30-60s at typical usage)


def _get_battery():
    global _cached_pct, _cache_calls
    _cache_calls += 1
    if _cached_pct is None or _cache_calls >= _CACHE_EVERY:
        _cached_pct = read_battery_percent()
        _cache_calls = 0
    return _cached_pct


def draw_battery_icon(draw, x, y, inverted=False):
    """
    Draw battery icon + percentage at (x, y).
    inverted=True for use on black header bars (draws in white).
    Returns the battery % or None if hardware absent.
    """
    pct = _get_battery()
    fg = 0xFF if inverted else 0x00
    bg = 0x00 if inverted else 0xFF

    if pct is None:
        # Draw a simple placeholder so layout stays consistent
        draw.text((x, y), "—%", font=font_text_10, fill=fg)
        return None

    # Outer shell
    draw.rectangle((x, y, x + _BAT_W, y + _BAT_H), outline=fg, fill=bg)
    # Positive nub
    draw.rectangle((x + _BAT_W, y + 3, x + _BAT_W + _BAT_TIP, y + _BAT_H - 3), fill=fg)
    # Fill bar
    fill_max = _BAT_W - 4
    fill_w = max(0, int(fill_max * pct / 100))
    if fill_w > 0:
        draw.rectangle((x + 2, y + 2, x + 2 + fill_w, y + _BAT_H - 2), fill=fg)

    draw.text((x + _BAT_W + _BAT_TIP + 4, y), f"{pct}%", font=font_text_10, fill=fg)
    return pct


def get_battery_percent():
    """Return current cached battery %, or None."""
    return _get_battery()


def draw_header(draw, title, w=480, h=40):
    """
    Draw a full-width black header bar with title (white) and battery (white).
    Returns the bottom y coordinate of the header.
    """
    draw.rectangle((0, 0, w, h), fill=0)
    draw.text((16, (h - 24) // 2), title, font=font_options_24, fill=0xFF)
    draw_battery_icon(draw, x=w - 72, y=(h - 12) // 2, inverted=True)
    return h
