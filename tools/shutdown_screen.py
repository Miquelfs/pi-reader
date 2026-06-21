#!/usr/bin/env python3
"""
Draws the sleep/shutdown screen on the e-ink display.
Called by systemd on shutdown/reboot before the system halts.
"""
import sys
import os
sys.path.insert(0, '/home/miquel/pi-reader')

from config.display_manager import display
from screens.sleep_screen import build_sleep_image

display.init_display()
display.draw_screen(build_sleep_image())
display.sleep()
