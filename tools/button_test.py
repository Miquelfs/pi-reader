#!/usr/bin/env python3
"""
Button wiring check. Watches every free GPIO and prints which one goes low
when a button is pressed, so a wire on the wrong header pin still shows up.
Run with: python3 tools/button_test.py   (Ctrl+C to stop)
"""
from signal import pause
from gpiozero import Button

EXPECTED = {5: 'UP', 6: 'DOWN', 13: 'SELECT', 26: 'BACK'}
# BCM → physical pin, skipping the display (8, 10, 11, 17, 18, 24, 25),
# SPI (7, 9), I2C (2, 3) and UART (14, 15)
FREE = {4: 7, 5: 29, 6: 31, 12: 32, 13: 33, 16: 36, 19: 35,
        20: 38, 21: 40, 22: 15, 23: 16, 26: 37, 27: 13}


def label(bcm):
    name = EXPECTED.get(bcm, 'not a button pin')
    return f"BCM {bcm:2d} (physical pin {FREE[bcm]:2d}) — {name}"


buttons = []
for bcm in FREE:
    try:
        b = Button(bcm, pull_up=True, bounce_time=0.05)
    except Exception as e:
        print(f"skip {label(bcm)}: {e}")
        continue
    if b.is_pressed:
        print(f"LOW AT REST  {label(bcm)} — shorted to ground (button rotated, or wire on a GND pin)")
    b.when_pressed = lambda bcm=bcm: print(f"pressed      {label(bcm)}", flush=True)
    buttons.append(b)

print(f"Watching {len(buttons)} pins. Press each button; Ctrl+C to stop.")
pause()
