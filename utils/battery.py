import smbus2

PISUGAR2_I2C_BUS = 1

# PiSugar2 can appear at different addresses depending on hardware revision:
# 0x75 = PiSugar2 (IP5209 chip)
# 0x57 = PiSugar2 Pro (IP5312 chip)
# We probe both and use whichever responds.
_CANDIDATE_ADDRS = [0x75, 0x57]
_PISUGAR2_ADDR   = None  # resolved at first read

# IP5209 registers (addr 0x75)
_REG_VOL_LOW_5209  = 0xa2
_REG_VOL_HIGH_5209 = 0xa3

# IP5312 registers (addr 0x57)
_REG_VOL_LOW_5312  = 0x22
_REG_VOL_HIGH_5312 = 0x23

# Voltage-to-percentage curve for a standard 3.7V LiPo
# (voltage_mV, percent) breakpoints — linear interpolation between them
_CURVE = [
    (4180, 100),
    (4100,  95),
    (4000,  88),
    (3900,  77),
    (3800,  63),
    (3700,  45),
    (3600,  25),
    (3500,  10),
    (3400,   4),
    (3000,   0),
]


def _voltage_to_percent(mv):
    if mv >= _CURVE[0][0]:
        return 100
    if mv <= _CURVE[-1][0]:
        return 0
    for i in range(len(_CURVE) - 1):
        v_high, p_high = _CURVE[i]
        v_low,  p_low  = _CURVE[i + 1]
        if v_low <= mv <= v_high:
            ratio = (mv - v_low) / (v_high - v_low)
            return int(p_low + ratio * (p_high - p_low))
    return 0


def _probe_address(bus):
    """Try known PiSugar2 addresses and return (addr, chip) or (None, None)."""
    for addr in _CANDIDATE_ADDRS:
        try:
            bus.read_byte_data(addr, 0x00)
            chip = 'IP5209' if addr == 0x75 else 'IP5312'
            return addr, chip
        except Exception:
            continue
    return None, None


def read_battery_percent():
    """Return battery level 0-100, or None if PiSugar2 is unreachable."""
    global _PISUGAR2_ADDR
    try:
        bus = smbus2.SMBus(PISUGAR2_I2C_BUS)

        if _PISUGAR2_ADDR is None:
            _PISUGAR2_ADDR, chip = _probe_address(bus)
            if _PISUGAR2_ADDR is None:
                bus.close()
                return None

        if _PISUGAR2_ADDR == 0x75:
            low  = bus.read_byte_data(_PISUGAR2_ADDR, _REG_VOL_LOW_5209)
            high = bus.read_byte_data(_PISUGAR2_ADDR, _REG_VOL_HIGH_5209)
            raw_adc = (high << 8) | low
            voltage_mv = int(raw_adc * 0.26855 + 2600)
        else:  # 0x57 IP5312
            low  = bus.read_byte_data(_PISUGAR2_ADDR, _REG_VOL_LOW_5312)
            high = bus.read_byte_data(_PISUGAR2_ADDR, _REG_VOL_HIGH_5312)
            raw_adc = (high << 8) | low
            voltage_mv = int(raw_adc * 1.25)  # IP5312: direct mV reading

        bus.close()
        return _voltage_to_percent(voltage_mv)
    except Exception:
        _PISUGAR2_ADDR = None  # reset so we re-probe next time
        return None
