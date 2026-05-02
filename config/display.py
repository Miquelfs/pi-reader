from waveshare import epd3in7
from PIL import Image,ImageDraw,ImageFont


epd = epd3in7.EPD()
epd.init(0)
epd.Clear(0xFF, 0)
epd.width = 280
epd.height = 480
