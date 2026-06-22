from config.fonts import font_options_24


def get_battery_percent():
    """Battery unavailable: Waveshare HAT blocks I2C bus. Returns None."""
    return None


def draw_header(draw, title, w=480, h=40):
    """Full-width black header bar with white title."""
    draw.rectangle((0, 0, w, h), fill=0)
    draw.text((16, (h - 24) // 2), title, font=font_options_24, fill=0xFF)
    return h
