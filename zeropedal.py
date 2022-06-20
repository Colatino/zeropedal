import time

import Adafruit_SSD1306
from smbus import SMBus

from g1xfour import Effects

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

g1xfour=Effects()
fontname="./FONT/VCR_OSD_MONO_1.001.ttf"

# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=None)

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

for e in g1xfour.effects.keys():
    
    # Draw a black filled box to clear the image
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    
    fontsize=32
    # Load font
    font = ImageFont.truetype(fontname,fontsize)

    # Get effect name
    text=g1xfour.effects[e]["name"].upper()
    lx,ly=font.getsize(text)
    
    #Try the largest font possible (32 px)
    while lx > width or ly > height:
        fontsize-=2
        font = ImageFont.truetype(fontname,fontsize)
        lx,ly=font.getsize(text)
    
    pos_x = ( width - lx ) / 2
    pos_y = ( height - ly ) / 2
    draw.text((pos_x,pos_y),text,font=font,fill=255)

    # Display image.
    disp.image(image)
    disp.display()
    
    time.sleep(0.1)

