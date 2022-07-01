import time
import math
import sys
import queue

# Initialize the FIFO task queue
q=queue.Queue()

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

# Helper footswitch class
class Footswitch:
    def __init__(self,pin,id):
        # pin the footswitch is attached to
        self.pin=pin
        # id of the footswitch, must be the same as its display
        self.id=id
        # set the pin and activate its internal pullup resistor
        PINS.setup(pin,PINS.IN,pull_up_down=PINS.PUD_UP)
        
    # Called when switch is pressed (interrupt routine)
    # MUST be as short as possible
    def callback(self,pin):
        if not PINS.input(pin):
            # Add a task to the queue to be resolved on the main loop
            q.put(self.id)

class Controller:
    fontname="./font/VCR_OSD_MONO_1.001.ttf"
    init_done=False
    need_redraw=False
    def __init__(self,pins=[],oleds=[],address=0x70,width=128,height=32):
        #Footpedal switch pins
        self.switch_pins=pins
        
        self.switches=[]
        
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
            for i,p in enumerate(pins):
                self.switches.append(Footswitch(p,i))    
    
    # Select display idx bus on the multiplexer
    def display_select(self,idx):
        self.tca.writeRaw8(1<<idx)
    
    # Deselect all displays
    def display_select_none(self):
        self.tca.writeRaw8(0)
        
    # Draw a text, can be multiline up to 4 lines
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
     
    # Main drawing method. Shows the effect name and bypass line behind (effect on) or in front (effect off)
    def redraw(self,switch):
        try:
            if linux and switch < len(self.oled_bus):
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
    
    # Refresh pedal model with current patch information
    # useful when editing the patch on the pedal while connected
    def refresh_model(self):
        for n in range(self.pedal.patch._n_effects):
            self.redraw(n)
            
if __name__=='__main__':
    
    # Pins connected to the foot switches
    switch_pins=[19,16,26,20,21]
    
    # Buses on the multiplexer used to control the oled displays
    oled_bus=[6,5,4,3,2]

    # Initialization info
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
    print("connected")            
    controller.draw_text(0,"Connected")
    controller.pedal.editor_on()
    controller.draw_text(1,"Loading patch...")
    controller.pedal.patch_download_current()            
    controller.draw_text(0,controller.pedal.patch.name)
    controller.draw_text(1,"Loaded!")
    time.sleep(0.5)
    controller.refresh_model()

    controller.init_done=True
    
    # Attach an interrupt routine to each footswitch
    for s in controller.switches:
        # Detects falling edge
        detect=PINS.FALLING #other possible values PINS.RISING or PINS.BOTH
        # Debounce time
        debounce=100
        # Attach routine
        PINS.add_event_detect(s.pin,detect,callback=s.callback,bouncetime=debounce)
    
    # Main loop
    while True:
        try:
            # Resolve queued tasks
            while not q.empty():
                index=None
                # Pop a task (if any) from the q  
                index=q.get_nowait()
                if not index==None:
                    # Toggle selected effect
                    controller.pedal.toggle_effect(index=index)
                    # Redraw effect state
                    controller.redraw(index)
            # Check pedal for incoming messages
            res,data=controller.pedal.task()
            if res:
                # Got a patch/bank change message
                controller.refresh_model()
            else:
                # Got a patch updated (effects changed) message
                if not data==None:
                    slot=data[0]
                    index=controller.pedal.patch.get_index(slot=slot)
                    controller.pedal.patch.states[index]=data[1]
                    controller.redraw(index)
        except Exception as e:
            print(str(e))
