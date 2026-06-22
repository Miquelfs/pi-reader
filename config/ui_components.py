from config.fonts import font_options_24, font_title, font_text_10

_FOOTER_H = 18
_HEADER_H = 48


def get_battery_percent():
    """Battery unavailable: Waveshare HAT blocks I2C bus. Returns None."""
    return None


def draw_header(draw, title, w=480, h=_HEADER_H):
    """Full-width black header bar with white title."""
    draw.rectangle((0, 0, w, h), fill=0)
    draw.text((16, (h - 36) // 2), title, font=font_title, fill=0xFF)
    return h


def draw_footer(draw, left_text, right_text='', w=480, h=280, margin=16):
    """1px separator line + left/right labels in the bottom 18px."""
    y_line = h - _FOOTER_H
    draw.line((0, y_line, w, y_line), fill=0, width=1)
    draw.text((margin, h - 14), left_text, font=font_text_10, fill=0)
    if right_text:
        right_w = int(font_text_10.getlength(right_text))
        draw.text((w - margin - right_w, h - 14), right_text, font=font_text_10, fill=0)
    return y_line
