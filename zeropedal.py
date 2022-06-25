import time

from minizt2 import zoomzt2

import Adafruit_SSD1306
from Adafruit_GPIO import I2C

import RPi.GPIO as PINS

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


class Controller:
    fontname="./font/VCR_OSD_MONO_1.001.ttf"

    def __init__(self,pins=[],oleds=[],address=0x70,width=128,height=32):
        
        #Footpedal switch pins
        self.switch_pins=pins
        
        self._switch_state=[]
        for p in pins:
            self._switch_state.append(1)

        #Oled screens multiplexer buses
        self.oled_bus=oleds
        #TCA9548A I2C multiplexer
        self.tca=I2C.get_i2c_device(address)
        self.pedal=zoomzt2()

        # 128 x 32 OLED display with I2C
        self.width=width
        self.height=height
        self.disp=Adafruit_SSD1306.SSD1306_128_32(rst=None)
        
        # Init Drawing object
        self.image=Image.new('1',(width,height))
        self.draw=ImageDraw.Draw(self.image)
        self.draw.rectangle((0,0,width,height), outline=0, fill=0)
        # Draw the bypass line
        self.draw.rectangle((0,height/2-4,width,height/2+4),outline=0,fill=1,width=2)
        
        for b in oleds:
            #Select display bus
            self.tca.writeRaw8(1<<b)

            # Initialize display library
            self.disp.begin()

            # Clear display
            self.disp.clear()
            self.disp.image(self.image)
            self.disp.display()

        PINS.setmode(PINS.BCM)
        for p in pins:
            PINS.setup(p,PINS.IN,pull_up_down=PINS.PUD_UP)
            PINS.add_event_detect(p,PINS.BOTH,callback=self.switch_pressed_cb,bouncetime=50)

    def display_select(self,idx):
        self.tca.writeRaw8(1<<idx)

    def redraw(self,switch):
        self.display_select(self.oled_bus[switch])
        
        # Draw a black filled box to clear the image
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
        
        # Draw the bypass line
        self.draw.rectangle((0,self.height/2-4,self.width,self.height/2+4),outline=0,fill=1,width=2)
        
        # Get effect name linked to the pressed switch
        text=self.pedal.patch.get_name(index=switch)

        if not text=="BYPASS":
            fontsize=self.height
            # Load font
            font = ImageFont.truetype(self.fontname,fontsize)    
            
            #Try the largest font possible (32 px)
            lx,ly=font.getsize(text)
            while lx > self.width or ly > self.height:
                #Reduce font size by 1 and check for text size
                fontsize-=1
                font = ImageFont.truetype(self.fontname,fontsize)
                lx,ly=font.getsize(text)
            
            pos_x = ( self.width - lx ) / 2
            pos_y = ( self.height - ly ) / 2

            # Black container
            self.draw.rectangle((pos_x,pos_y,pos_x+lx,pos_y+ly),outline=0,fill=0)
            
            # Effect name
            self.draw.text((pos_x,pos_y),text,font=font,fill=255)

            # Draw bypass line after the name if disabled            
            if not self.pedal.patch.states[switch]:
                self.draw.rectangle((0,self.height/2-4,self.width,self.height/2+4),outline=0,fill=1,width=2)
            
        # Display image.
        self.disp.image(self.image)
        self.disp.display()
    
    def switch_pressed_cb(self,pin):
        global curreffect,effectstate
        
        index=self.switch_pins.index(pin)
        cur_state=PINS.input(pin)
        # Check if last state was HIGH and current state is LOW (switch pressed)
        if self._switch_state[index] and not cur_state:
            #print("Pressed switch",index+1,"on pin",pin)

            # Toggle effect state
            if self.pedal.patch.get_state(index=index):
                self.pedal.effect_off(self.pedal.patch.get_slot(index=index))
                self.pedal.patch.set_state(0,index=index)
            else:
                self.pedal.effect_on(self.pedal.patch.get_slot(index=index))
                self.pedal.patch.set_state(1,index=index)

            # Draw state to display
            self.redraw(index)
        
        self._switch_state[index]=cur_state
    
if __name__=='__main__':

    # Pins connected to the foot switches
    switch_pins=[4,14]#,15,17,18]
    # Buses used for the oled displays
    oled_bus=[0,1]#,2,3,4]

    controller=Controller(switch_pins,oled_bus)


    # Main loop
    #while True:
    #    pass