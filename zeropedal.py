import time
import Adafruit_SSD1306

from g1xfour import Effects

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

g1xfour=Effects()

RST = None     # on the PiOLED this pin isnt used

# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# Initialize display library
disp.begin()

# Clear display
disp.clear()
disp.display()

# Create blank image for drawing
# Make sure to create image with mode '1' for 1-bit color
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Define some constants to allow easy resizing of shapes
padding = 2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = padding

# Load default font
# font = ImageFont.load_default()
font = ImageFont.truetype("vcrosd.ttf",24)

# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('Minecraftia.ttf', 8)

# Draw a black filled box to clear the image
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Write two lines of text.
text=g1xfour.effects[0]["name"].upper()
lx,ly=font.getsize(text)
draw.text((padding+(width-2*padding-lx)/2,top+(height-2*padding-ly)/2),text,font=font,fill=255)

# Display image.
disp.image(image)
disp.display()

