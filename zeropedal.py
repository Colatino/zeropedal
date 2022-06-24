import time

import Adafruit_SSD1306
from Adafruit_GPIO import I2C

# from smbus import SMBus

import RPi.GPIO as PINS

from g1xfour import Effects

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

switchPins={4:1,14:1,15:1,17:1,18:1}

#bus=SMBus(1)
oleds=[0,1]

g1xfour=Effects()
curreffects=[16777232,16777248,0,0,0]
effectstate=[1,1,1,1,1]

fontname="./font/VCR_OSD_MONO_1.001.ttf"

#TCA9548A
tca=I2C.get_i2c_device(address=0x70)

# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=None)

width=128
height=32
image = Image.new('1', (width, height))

# Get drawing object to draw on image
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image
draw.rectangle((0,0,width,height), outline=0, fill=0)

def displayselect(idx):
    tca.writeRaw8(1<<idx)
    
def initdisplays():
    for o in oleds:
        displayselect(o)

        # Initialize display library
        disp.begin()

        # Clear display
        disp.clear()
        disp.display()

def drawTextTo(idx,text):
    displayselect(idx)
    
    # Draw a black filled box to clear the image
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    
    draw.rectangle((0,height/2-4,width,height/2+4),outline=0,fill=1,width=2)
    
    if not text=="BYPASS":
        fontsize=32
        # Load font
        font = ImageFont.truetype(fontname,fontsize)    
        
        #Try the largest font possible (32 px)
        lx,ly=font.getsize(text)
        while lx > width or ly > height:
            #Reduce font size by 1 and check for text size
            fontsize-=1
            font = ImageFont.truetype(fontname,fontsize)
            lx,ly=font.getsize(text)
        
        pos_x = ( width - lx ) / 2
        pos_y = ( height - ly ) / 2
        draw.rectangle((pos_x,pos_y,pos_x+lx,pos_y+ly),outline=0,fill=0)
        
        draw.text((pos_x,pos_y),text,font=font,fill=255)
        
        if not effectstate[idx]:
            draw.rectangle((0,height/2-4,width,height/2+4),outline=0,fill=1,width=2)
        
    # Display image.
    disp.image(image)
    disp.display()
    
def switch_pressed_cb(pin):
    global curreffect,effectstate
    
    switchpedal=list(switchPins.keys()).index(pin)
    
    if switchPins[pin] and not PINS.input(pin):
        print("Pressed switch",switchpedal+1,"on pin",pin)
        #text=g1xfour.effects[list(g1xfour.effects.keys())[curreffect]]["name"].upper()
        text=g1xfour.effects[curreffects[switchpedal]]["name"].upper()
        effectstate[switchpedal]=not effectstate[switchpedal]
        drawTextTo(switchpedal,text)
    
    switchPins[pin]=PINS.input(pin)

if __name__=='__main__':
    
    initdisplays()
    
    PINS.setmode(PINS.BCM)
    for pin in switchPins:
        PINS.setup(pin,PINS.IN,pull_up_down=PINS.PUD_UP)
        PINS.add_event_detect(pin,PINS.BOTH,callback=switch_pressed_cb,bouncetime=50)
    switch_pressed_cb(4)