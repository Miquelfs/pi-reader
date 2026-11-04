from config.fonts import font_heading, font_text_10, font_label

_FOOTER_H = 18
_HEADER_H = 54


def get_battery_percent():
    """Battery unavailable: Waveshare HAT blocks I2C bus. Returns None."""
    return None


def draw_header(draw, title, w=480, h=_HEADER_H):
    """Title on white with a hairline underneath. Keeps the old 54 px height so layouts hold."""
    bbox = font_heading.getbbox(title)
    text_h = bbox[3] - bbox[1]
    text_y = (h - 8 - text_h) // 2 - bbox[1]
    draw.text((16, text_y), title, font=font_heading, fill=0)
    draw.line((16, h - 8, w - 16, h - 8), fill=0, width=1)
    return h


def draw_label(draw, xy, text):
    """Small uppercase label with a little letter-spacing."""
    x, y = xy
    for ch in text.upper():
        draw.text((x, y), ch, font=font_label, fill=0)
        x += font_label.getlength(ch) + 0.8
    return x


def draw_footer(draw, left_text, right_text='', w=480, h=280, margin=16):
    """1px separator line + left/right labels in the bottom 18px."""
    y_line = h - _FOOTER_H
    draw.line((0, y_line, w, y_line), fill=0, width=1)
    draw.text((margin, h - 15), left_text, font=font_text_10, fill=0)
    if right_text:
        right_w = int(font_text_10.getlength(right_text))
        draw.text((w - margin - right_w, h - 15), right_text, font=font_text_10, fill=0)
    return y_line
