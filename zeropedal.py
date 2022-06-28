import time
import math
import sys

linux=False
if sys.platform =='linux':
    linux=True
    import Adafruit_SSD1306
    from Adafruit_GPIO import I2C
    import RPi.GPIO as PINS

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from minizt2 import zoomzt2

class Controller:
    fontname="./font/VCR_OSD_MONO_1.001.ttf"
    init_done=False
    need_redraw=False
    def __init__(self,pins=[],oleds=[],address=0x70,width=128,height=32):
        #Footpedal switch pins
        self.switch_pins=pins
    
        self._switch_state=[]
        for p in pins:
            self._switch_state.append(1)
            
        self.pedal=zoomzt2()
        
        if linux:        
            #Oled screens multiplexer buses
            self.oled_bus=oleds
            
            #TCA9548A I2C multiplexer
            self.tca=I2C.get_i2c_device(address)            

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
                self.display_select_none()

            text="Waiting"
            self.font = ImageFont.truetype(self.fontname,28)  
            lx,ly=self.font.getsize(text)
            pos_x = ( self.width - lx ) / 2
            pos_y = ( self.height - ly ) / 2

            PINS.setmode(PINS.BCM)
            for p in pins:
                PINS.setup(p,PINS.IN,pull_up_down=PINS.PUD_UP)
                PINS.add_event_detect(p,PINS.BOTH,callback=self.switch_pressed_cb,bouncetime=50)
            
    def display_select(self,idx):
        self.tca.writeRaw8(1<<idx)
    
    def display_select_none(self):
        self.tca.writeRaw8(0)
        
    def draw_text(self,idx,text):
        try:
            if idx < len(self.oled_bus) and linux:
                self.display_select(idx)
                self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
                
                fontsize=self.height
                # Reload font
                self.font = ImageFont.truetype(self.fontname,fontsize)
                while True:
                    #Try the largest font possible (32 px)
                    lx,ly=self.font.getsize(text)
                    if fontsize>=16 and lx <= self.width:
                        pos_x = ( self.width - lx ) / 2
                        pos_y = ( self.height - ly ) / 2
                        
                        # Effect name
                        self.draw.text((pos_x,pos_y),text,font=self.font,fill=255)
                        break
                    elif fontsize < 16:
                        nlines = math.ceil(lx/self.width)
                        maxlines = int(32/ly)
                        if nlines < maxlines:
                            lines= math.ceil(lx / self.width)
                            cursor=0
                            for l in range(lines):
                                end=len(text)
                                pos_y = ( l * ly )
                                lsize,_=self.font.getsize(text[cursor:end])
                                while lsize > self.width:
                                    end-=1
                                    lsize,_=self.font.getsize(text[cursor:end])
                                self.draw.text((0,pos_y),text[cursor:end],font=self.font,fill=255)
                                pos_y+=ly
                                cursor=end
                                end=len(text)
                            break
                            
                    
                    #Reduce font size by 1 and check for text size
                    fontsize-=1
                    self.font = ImageFont.truetype(self.fontname,fontsize)
                    if fontsize < 8:
                        done=True
                # Display image.
                self.disp.image(self.image)
                self.disp.display()
                self.display_select_none()
            else:
                print(text)
        except:
            pass
            
    def redraw(self,switch):
        try:
            if linux and switch < len(self.oled_bus):
                print(switch)
                # Draw a black filled box to clear the image
                self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)
                # Draw the bypass line
                self.draw.rectangle((0,self.height/2-4,self.width,self.height/2+4),outline=0,fill=1,width=2)
                # Get effect name linked to the pressed switch
                text=self.pedal.patch.get_name(index=switch)
                
                if not text=="BYPASS":
                    fontsize=self.height
                    # Load font
                    self.font = ImageFont.truetype(self.fontname,fontsize)                
                    #Try the largest font possible (32 px)
                    lx,ly=self.font.getsize(text)
                    while lx > self.width or ly > self.height:
                        #Reduce font size by 1 and check for text size
                        fontsize-=1
                        self.font = ImageFont.truetype(self.fontname,fontsize)
                        lx,ly = self.font.getsize(text)
                    pos_x = ( self.width - lx ) / 2
                    pos_y = ( self.height - ly ) / 2
                    
                    # Black container
                    self.draw.rectangle((pos_x,pos_y,pos_x+lx,pos_y+ly),outline=0,fill=0)
                    # Effect name
                    self.draw.text((pos_x,pos_y),text,font=self.font,fill=255)
                    # Draw bypass line after the name if disabled
                    if not self.pedal.patch.states[switch]:
                        self.draw.rectangle((0,self.height/2-4,self.width,self.height/2+4),outline=0,fill=1,width=2)   
                # Display image
                self.display_select(self.oled_bus[switch])
                self.disp.clear()
                self.disp.image(self.image)
                self.disp.display()
                self.display_select_none()
                return True
            else:
                text=self.pedal.patch.get_name(index=switch)
                print (text)
                return False
                
        except:
            return False
    
    def refresh_model(self):
        for n in range(self.pedal.patch._n_effects):
            self.redraw(n)

    def switch_pressed_cb(self,pin):
        try:
            if self.init_done:
                index=self.switch_pins.index(pin)
                cur_state=PINS.input(pin)
                # Check if last state was HIGH and current state is LOW (switch pressed)
                if self._switch_state[index] and not cur_state:
                    #print("Pressed switch",index+1,"on pin",pin)

                    # Toggle effect state
                    if self.pedal.patch.get_state(index=index):
                        if self.pedal.effect_off(self.pedal.patch.get_slot(index=index)):
                            self.pedal.patch.set_state(0,index=index)
                            
                            # Draw state to display
                            self.redraw(index)
                    else:
                        if self.pedal.effect_on(self.pedal.patch.get_slot(index=index)):
                            self.pedal.patch.set_state(1,index=index)
                            
                            # Draw state to display
                            self.redraw(index)
                
                self._switch_state[index]=cur_state
                #self.refresh_model()
            else:
                pass
                
        except:
            pass
            
if __name__=='__main__':
    
    # Pins connected to the foot switches
    switch_pins=[19,16,26,20,21]
    
    # Buses on the multiplexer used to control the oled displays
    oled_bus=[6,5,4,3,2]

    controller=Controller(switch_pins,oled_bus)
    
    loaded=time.perf_counter()
    controller.draw_text(0,"zeropedal v 0.1")
    time.sleep(.5)
    controller.draw_text(0,"Init took "+str(round(loaded,2))+" s")
    time.sleep(.5)
    
    controller.draw_text(0,"Waiting")
    
    # Wait for device to connect
    while not controller.pedal.connected:
        if controller.pedal.connect():
            break
            
    controller.draw_text(0,"Connected")
    controller.pedal.editor_on()
    controller.draw_text(1,"Loading patch...")
    controller.pedal.patch_download_current()            
    controller.draw_text(0,controller.pedal.patch.name)
    controller.draw_text(1,"Loaded!")
    time.sleep(0.5)
    controller.refresh_model()

    controller.init_done=True
    
    # Main loop
    while True:
        if controller.pedal.task():
            controller.refresh_model()
