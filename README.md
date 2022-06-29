# ZEROPEDAL
Raspberry Pi Zero midi pedal controller for Zoom pedals. 

The purpose of this project is to build an auxiliary pedal controller to be used with Zoom multi-effects processors like the G1XFour (tested with this model) and toggle individual effects on/off.

This is a software and hardware project.

The code is written in Python (tested on 3.7 and 3.9) and is largely based and inspired on [zoom-zt2](https://github.com/mungewell/zoom-zt2) and [ZoomPedalFun](https://github.com/shooking/ZoomPedalFun)

## BILL OF MATERIALS
- 1 x Raspberry Pi Zero (mine is a zero w with a busted wifi chip)
- 5 x SSD1306 0.91" oled displays
- 1 x TC9548A
- 5 x Foot switches
- 1 x female USB type A breakout board
- 1 x female micro USB breakout board
- 10 x 2.2kOhm resistor
- Some jumper wires
- Some box or case (mine will be 3d printed and stl/3mf files will be uploaded) to contain everything (TODO)

## DEPENDENCIES
This project makes use of the following:
A deprecated [Adafruit Python SSD1306 library](https://github.com/adafruit/Adafruit_Python_SSD1306) and its dependencies
[MIDO](https://mido.readthedocs.io/en/latest/) and its dependencies
[VCR OSD MONO font](https://www.dafont.com/vcr-osd-mono.font)  by [Riciery Leal](https://www.dafont.com/mrmanet.d5509)

### TODO list
[] Design and print case
[] Detect when pedal is unplugged
[] Improve README
