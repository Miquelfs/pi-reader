#!/usr/bin/env python3
"""
Draws a frame on the outermost pixels of the panel plus centre lines, so the
image area can be measured against the board edges for the case window.
Stop the service first: sudo systemctl stop pi-reader
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw
from config.display_manager import display

img = Image.new('1', (480, 280), 0xFF)
draw = ImageDraw.Draw(img)
draw.rectangle((0, 0, 479, 279), outline=0, width=2)
draw.line((240, 0, 240, 279), fill=0)
draw.line((0, 140, 479, 140), fill=0)
display.init_display()
display.draw_screen(img)
display.sleep()
print("Frame drawn. Measure from the board's LEFT and BOTTOM edges to the outside of the frame.")
