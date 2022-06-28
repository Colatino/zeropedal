import mido
from g1xfour import effects
import time
import logging

class Effects:
    effects={}
    
    def __init__(self):
        for e in effects:
            tempeffect={}
            tempeffect={"name":e[0],
                        "id":e[1],
                        "filename":e[2],
                        "nslots":e[3],
                        "nparam":e[4],
                        "params":[]}
            for p in e[5]:
                tempparam={}
                tempparam={"pedal":p[0],
                           "maxval":p[1],
                           "defval":p[2],
                           "curval":p[3],
                           "name":p[4]}
                tempeffect["params"].append(tempparam)
                
            self.effects[e[1]]=tempeffect
    
    def find(self,id):
        return self.effects[id]
    
    def get_size(self,id):
        return self.find(id)['nslots']
    
    def get_name(self,id):
        return self.find(id)['name'].upper()
    
class Patch:
    _cur_slot=0
    _n_effects=0
    name=""
    names=[]
    ids=[]
    slots=[]
    states=[]
        
    def add_effect(self,id,state,effects):
        self.ids.append(id)
        self.states.append(state)
        self.names.append(effects.get_name(id))        
        self.slots.append(self._cur_slot)
        self._cur_slot+=effects.get_size(id)
        self._n_effects+=1
        
    def get_index(self,slot=None,id=None):
        if not slot==None:
            return self.slots.index(slot)
        
        if not id==None:
            return self.ids.index(id)
    
    def get_slot(self,index=None,id=None):
        if not index==None:
            return self.slots[index]
        
        if not id==None:
            return self.slots[self.ids,index(id)]

    def get_name(self,slot=None,id=None,index=None):
        if not slot==None:
            return self.names[self.slots.index(slot)]
        
        if not id==None:
            return self.names[self.ids.index(id)]
        
        if not index==None:
            return self.names[index]
                 
    def clear(self):
        self.names=[]
        self.ids=[]
        self.slots=[]
        self.states=[]
        self._cur_slot=0
        self._n_effects=0
    
    def get_state(self,slot=None,index=None,id=None):
        if not slot==None:
            return self.states[self.slots.index(slot)]
        
        if not index==None:
            return self.states[index]
        
        if not id==None:
            return self.states[self.ids.index(slot)]

    def set_state(self,state,slot=None,index=None,id=None):
        if not slot==None:
            self.states[self.slots.index(slot)]=state
        
        if not index==None:
            self.states[index]=state

        if not id==None:
            self.states[self.ids.index(id)]=state

class zoomzt2(object):
    midiname="ZOOM G"
    inport = None
    outport = None
    editor = False
    
    effects=Effects()
    patch=Patch()

    def is_connected(self):
        if self.inport == None or self.outport == None:
            return False
        else:
            return True

    def connect(self):
        for port in mido.get_input_names():
            if port[:len(self.midiname)]==self.midiname:
                logging.info("opening ports on device "+port)
                self.inport = mido.open_input(port)
                self.outport = mido.open_output(port)
                break

        if self.inport == None or self.outport == None:
            return False
        logging.info("Connected")
        return True

    def disconnect(self):
        logging.info("disconnecting")
        if self.editor:
            self.editor_off()
        
        self.inport.close()
        self.inport = None
        self.outport.close()
        self.outport = None

    def editor_on(self):
        logging.info("editor mode on")
        # Enable Editor Mode
        msg = mido.Message("sysex", data = [0x52, 0x00, 0x6e, 0x50])
        self.outport.send(msg); msg = self.inport.receive()
        self.editor = True

    def editor_off(self):
        logging.info("editor mode off")
        # Disable Editor Mode
        msg = mido.Message("sysex", data = [0x52, 0x00, 0x6e, 0x51])
        self.outport.send(msg); msg = self.inport.receive()
        self.editor = False
    
    def effect_on(self,slot):
        logging.info("effect on slot "+str(slot)+" on")
        msg=mido.Message('sysex',data=[0x52 ,0x00 ,0x6E ,0x64 ,0x03 ,0x00 ,slot ,0x00 ,0x00 ,0x02 ,0x00 ,0x00 ,0x00])
        self.outport.send(msg); msg = self.inport.receive()

    def effect_off(self,slot):
        logging.info("effect on slot "+str(slot)+" off")
        msg=mido.Message('sysex',data=[0x52 ,0x00 ,0x6E ,0x64 ,0x03 ,0x00 ,slot ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00])
        self.outport.send(msg); msg = self.inport.receive()
        
    def unpack(self, packet):
        # Unpack data 7bit to 8bit, MSBs in first byte
        data = bytearray(b"")
        loop = -1
        hibits = 0

        for byte in packet:
            if loop !=-1:
                if (hibits & (2**loop)):
                    data.append(128 + byte)
                else:
                    data.append(byte)
                loop = loop - 1
            else:
                hibits = byte
                loop = 6
        return(data)
    
    def parse_patch(self,data):
        try:
            self.patch.clear()
            self.patch.name=data[26:36].rstrip().decode("utf-8")

            edtb=data.split(b'EDTB')[1].split(b'PPRM')[0]
            neff=int(edtb[0]/24)
            logging.info("got patch "+self.patch.name+" now parsing")
            
            for i in range(neff):    
                bits=''        
                union=edtb[7+i*24]<<24 | edtb[6+i*24]<<16 | edtb[5+i*24]<<8 | edtb[4+i*24]
                id=(union>>1) & 0xfffffff
                self.patch.add_effect(id,union & 1,self.effects)
            logging.info("parse completed, patch has "+str(self.patch._n_effects)+" effects")
            return True
        except Exception as e:
            logging.info("Error while parsing patch")
            logging.exception(e)
              
    def patch_download_current(self):
        logging.info("downloading current patch")
        try:
            msg = mido.Message("sysex", data = [0x52, 0x00, 0x6e, 0x29])
        
            self.clear_buffer()
            
            self.outport.send(msg); msg = self.inport.receive()

            # decode received data
            while True:
                if msg:
                    if msg.type=="sysex":
                        packet = msg.data
                        data = self.unpack(packet[4:])
                        if b"PTCF" in data:
                            return self.parse_patch(data)
                
                msg = self.inport.receive()
            logging.info("download successful")
        except Exception as e:
            logging.info("error downloading current patch")
            logging.exception(e)
        
    def clear_buffer(self):
        for m in self.inport.iter_pending():
            print(m)
    
    def task(self):
        try:
            for m in self.inport.iter_pending():
                if m.type=="program_change":
                    self.patch_download_current()
                    logging.info("Changed to patch "+self.patch.name)
                elif m.type=="sysex":
                    if m.data[:5]==(82,0,110,100,3):
                        logging.indo("toggle effect on slot "+str(slot)+" to "+("On" if m.data[8] else "Off"))
                        self.patch_download_current()      
        except Exception as e:
            logging.info("error while performing task")
            logging.exception(e)
            
if __name__ == '__main__':     
    zoom=zoomzt2()
    
    # Wait for device to connect
    while not zoom.is_connected():
        if zoom.connect():
            print ("Device connected")
            
    zoom.editor_on()
    zoom.patch_download_current()
    
    while True:
        zoom.task()
                    
    zoom.disconnect()
