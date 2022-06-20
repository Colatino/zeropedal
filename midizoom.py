import mido,time
import json

def connect():
    global zin,zout
    zin=mido.open_input('ZOOM G Series 0')
    zout=mido.open_output('ZOOM G Series 1')

def disconnect():
    global zin,zout
    zin.close()
    zout.close()

def editorOn():
    global zin,zout
    zout.send(mido.Message('sysex',data=[0x52,0x00,0x6e,0x50]))
    _=zin.receive()

def editorOff():
    global zin,zout
    zout.send(mido.Message('sysex',data=[0x52,0x00,0x6e,0x51]))
    _=zin.receive()

def effectOn(slot):
    global zin,zout
    effect_on=mido.Message('sysex',data=[0x52 ,0x00 ,0x6E ,0x64 ,0x03 ,0x00 ,slot ,0x00 ,0x00 ,0x02 ,0x00 ,0x00 ,0x00])
    connect()
    editorOn()
    #Flush
    zout.send(mido.Message('sysex',data=[0x52,0x00,0x6e,0x60,0x05,0x00]))
    zout.send(effect_on)
    m=zin.receive()
    editorOff()
    disconnect()

def effectOff(slot):
    global zin,zout
    effect_off=mido.Message('sysex',data=[0x52 ,0x00 ,0x6E ,0x64 ,0x03 ,0x00 ,slot ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00])
    connect()
    editorOn()
    #Flush
    zout.send(mido.Message('sysex',data=[0x52,0x00,0x6e,0x60,0x05,0x00]))
    zout.send(effect_off)
    m=zin.receive()
    editorOff()
    disconnect()
    
def getCurPatch():
    global zin,zout
    connect()
    editorOn()
    #Flush
    zout.send(mido.Message('sysex',data=[0x52,0x00,0x6e,0x60,0x05,0x00]))
    for m in zin.iter_pending():
        pass
    #Get current patch
    zout.send(mido.Message('sysex',data=[0x52,0x00,0x6e,0x29]))
    m=zin.receive()  
    editorOff()
    disconnect()
    parsePatch(unpack(m.data[4:]))    
    
def unpack(packet):
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
                # do we need to acount for short sets (at end of block block)?
                loop = 6

        return(data)
    
def parsePatch(data):
    global effects,t0,dd
    dd=data
    edtb=data.split(b'EDTB')[1].split(b'PPRM')[0]
    effects={'id':[],'st':[]}
    eff_st=[]
    neff=int(edtb[0]/24)
    t0=time.perf_counter_ns()
    for i in range(neff):    
        bits=''        
        uniao=edtb[7+i*24]<<24 | edtb[6+i*24]<<16 | edtb[5+i*24]<<8 | edtb[4+i*24]
        id=(uniao>>1) & 0xfffffff
        effects['id'].append(id)
        effects['st'].append(uniao & 1)    

summary={}
f=open('final_summary.json','r')
summary=json.loads(f.read())
f.close()

t0=time.perf_counter_ns()
getCurPatch()
pedal_state=[]
slot=0
slots=0
for i in range(len(effects['id'])):    
    e=effects    
    slot+=slots
    pedal_state.append({'id':e['id'][i],
                        'onoff':e['st'][i],
                        'slot':slot})
    slots=summary[str(e['id'][i])]['nslots']
t1=time.perf_counter_ns()
print(pedal_state,(t1-t0)/1000000)