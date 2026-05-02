import smbus2

PISUGAR2_I2C_BUS = 1
PISUGAR2_I2C_ADDR = 0x75
PISUGAR2_BATTERY_REG = 0x2A


def read_battery_percent():
    """Return battery level 0-100, or None if PiSugar2 is unreachable."""
    try:
        bus = smbus2.SMBus(PISUGAR2_I2C_BUS)
        raw = bus.read_byte_data(PISUGAR2_I2C_ADDR, PISUGAR2_BATTERY_REG)
        bus.close()
        return max(0, min(100, raw))
    except Exception:
        return None
