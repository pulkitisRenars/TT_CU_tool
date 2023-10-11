#I2C_Scanner_V_1_1.py
#I2C and ControlUnit scanner tool meant for testing TTunits and ControlUnits. The tool tests I2C devices(Real-Time-Clock, EEPROM, Buzzer),
#also the ControlUnit(connected relays, Alarm state), Wiegand RFID card reader(all 4 pin addresses, card data, reader functionality)

import machine
from ili934xnew import ILI9341, color565
from machine import Pin, SPI, UART
import m5stack
from eeprom import EEPROM
import glcdfont
from micropython import const
import tt14
import tt24
import random
import tt32
import os
import utime
import sys
from MSG import MSG
from Wiegand import Wiegand

SCR_WIDTH = const(480)
SCR_HEIGHT = const(320)
SCR_ROT = const(3)
CENTER_Y = int(SCR_WIDTH / 2)
CENTER_X = int(SCR_HEIGHT / 2)

TFT_CLK_PIN = const(18)
TFT_MOSI_PIN = const(19)
TFT_MISO_PIN = const(16)

TFT_CS_PIN = const(17)
TFT_RST_PIN = const(20)
TFT_DC_PIN = const(21)

Ttx=Pin(4)
Trx=Pin(5)

button = Pin(25, Pin.IN, Pin.PULL_UP)
buzzer = Pin(24,Pin.OUT)
results=False
RFID_res=[]
btn_count=0

spi = SPI(#object used to configure the display of the LCD display
    0,
    baudrate=40000000,
    miso=Pin(TFT_MISO_PIN),
    mosi=Pin(TFT_MOSI_PIN),
    sck=Pin(TFT_CLK_PIN)
)

sda=machine.Pin(0)
scl=machine.Pin(1)
i2c=machine.I2C(0,sda=sda,scl=scl,freq=400000)
global atmega_found
atmega_found=False
true_found=False
global mDevice#Global variable that says which Unit is used
uartID=UART(1,baudrate=57600,timeout=1, invert=3)#Object used to find out if there is a ControlUnit connected or not

M=MSG(print)
M.Queue("GET","board_version")
M.Send(True)
M.Receive(True)
checkU=uartID.read()#Variable used to find out if there is a ControlUnit connected or not
print(checkU)

display = ILI9341(#Object used to overall display the LCD display
    spi,
    cs=Pin(TFT_CS_PIN),
    dc=Pin(TFT_DC_PIN),
    rst=Pin(TFT_RST_PIN),
    w=SCR_WIDTH,
    h=SCR_HEIGHT,
    r=SCR_ROT
)


eprom=EEPROM(#Object used to work with units EEPROM storage
    addr=80,
    pages=128,
    bpp=32,
    i2c=i2c,
    at24x=0
    )

#2D array that has the I2C addresses, hardware name and its status in the scanner(if there are more hardware connected, than add its info in the array)
i2c_devices=[['104','EEPROM','False'],['80','RTC','False']]
statusArr=[]

def EEPROM_check(y,i2c_devices,results):#EEPROM testing function
    global statusArr
    newFrame(2)
    display.set_pos(10, 60)
    display.set_color(color565(0, 0, 0), color565(255, 255, 255))
    display.print('Testing EEPROM')
    try:
        eprom.write(0, "test")#Writes EEPROM value
    except:#Finds out if the EEPROM writing works
        statusArr.append('* EEPROM communication: Write ERR')
        i2c_devices[1][2]='False'
    else:
        eprom.write(0, "test")#Writes EEPROM value
    try:
            epromVal=eprom.read(0,4)#Reads EEPROM value
    except:#Finds out if the EEPROM reading works
        statusArr.append('* EEPROM communication: Read ERR')
        i2c_devices[1][2]='False'
    else:
            epromVal=eprom.read(0,4)#Reads EEPROM value
    try:
        if "test" in epromVal:#Checks if in the EEPROM memory exists a value
          y+=30  
    except:#The try except is used because of a possible error, if the reading and writing doesn't work
        statusArr.append('* EEPROM Read-Write ERROR')
        i2c_devices[1][2]='False'
    else:
        if "test" in epromVal:#Checks if in the EEPROM memory exists a value
            statusArr.append('* EEPROM communication: Write OK')
            statusArr.append('* EEPROM communication: Read OK')
            if results==True:#Used for result identification further on in the code
                results=False
            else:
                results=True
        else:#If there is a EEPROM read-write error
            statusArr.append('* EEPROM Read-Write ERROR')
            i2c_devices[0][2]='False'
        eprom.wipe()
        
def RFID_check(): # RFID card reader testing function
    global results, RFID_res
    RFID_adr=[[2,3,6,8],[9,10,7,11],[14,15,26,13],[28,29,6,27]]#RFID card reader addresses
    RFID_res=[]
    pg=9
    i=0
    for add in RFID_adr:#Goes through each pin address to test
        pg+=1
        i+=1
        led=Pin(add[2],Pin.OUT)
        buz=Pin(add[3],Pin.OUT)
        wiegand_reader = Wiegand(add[0], add[1])#Sets the pin addresses to work with the wiegand protocol
        newFrame(pg)
        display.set_pos(170, 10)
        display.set_font(tt14)
        display.write("PRESS---->")
        display.set_pos(10, 60)
        display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        display.print('* '+str(i)+'. Wiegand device address testing')
        display.fill_rectangle(5, 90, 215, 45, 008000)
        display.set_pos(10, 100)
        display.set_font(tt24)
        display.print("For next test press")
        display.set_font(tt14)
        display.set_pos(10, 160)
        display.print("Wiegand Card Data:")
        display.set_pos(10, 190)
        display.print("Wiegand Card Data(rev):")
        display.set_pos(10, 220)
        display.print("Wiegand Type(bits):")

        while True:
            if wiegand_reader.available():#Checks if card has been scanned by the RFID card reader
                for x in range(2):
                    led.high()
                    buz.high()
                    utime.sleep(0.4)
                    led.low()
                    buz.low()
                    utime.sleep(0.4)
                card_code = wiegand_reader.GetCode()# Gets the card code
                card_revCode=wiegand_reader.GetRevCode()
                card_type = wiegand_reader.GetType()# Gets the RFID bit type
                display.set_pos(10, 160)
                display.print("RFID Card Data:" + str(card_code))
                display.set_pos(10, 190)
                display.print("Wiegand Card Data(rev):" + str(card_revCode))
                display.set_pos(10, 220)
                display.print("Wiegand Type(bits):" + str(card_type))
                if str(i)+'.' in RFID_res:
                    print("not append")
                else:
                    RFID_res.append(str(i)+'.')#Puts the RFID card reader functionality statuss
                if results == True:  # Used for result identification further on in the code
                        results = False
                else:
                        results = True
            button_pressed = button.value() == 0  # Check if the button is pressed

            if button_pressed:
                break
    if RFID_res==[]:#If there aren't any working card readers it puts in the status array information for results showcase
        statusArr.append('* 0 Wiegand readers work: ERR')
    elif RFID_res != []:#If there are working card readers it puts in the status array information for results showcase
        ind=str(RFID_res)
        statusArr.append('* '+ind+' Wiegand readers work')

def ATmega_relay_check():#Relay testing function
    signalArr=["turnstile1_a","turnstile1_b","turnstile2_a","turnstile2_b","button1","button2"]#Array of all test-needed relays
    pg=4
    for relayName in signalArr:#Goes through each test-needed relays
        newFrame(pg)
        display.set_pos(10, 60)
        display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        display.print('* '+relayName+' testing')
        display.fill_rectangle(5, 90, 180, 45, 008000)
        display.set_pos(10, 100)
        display.set_font(tt24)
        display.print("Listen for relay!")
        display.set_font(tt14)
        M.Queue("SIGNAL",relayName)#Signals ControlUnit to turn on relay
        M.Send(True)
        pg=pg+1
        utime.sleep(3)
        
def ATmega_check(y,results):#ControlUnit testing function
    global statusArr
    global atmega_found
    newFrame(3)
    display.set_pos(10, 60)
    display.set_color(color565(0, 0, 0), color565(255, 255, 255))
    display.print('Testing ControlUnit')
    atmega_found=False#Variable used for the ControlUnits functionality identification
    ATmega=M.HWCheck()
    y+=30
    if ATmega ==True:
        atmega_found=True#Sets the ConrolUnits status as True
        statusArr.append('* ConUnit communication: Write OK')
        statusArr.append('* ConUnit communication: Read OK')
        if results==True:#Used for result identification further on in the code
                results=False
        else:
                results=True
    else:#If the hardware check function gives out False value
        statusArr.append('* ConUnit communication: Write ERR')
        statusArr.append('* ConUnit communication: Read ERR')
    display.set_pos(130, 10)
    display.set_font(tt14)
    display.write("TEST RELAYS---->")
    while True:
        button_pressed = button.value() == 0  # Check if the button is pressed
        if button_pressed:
            ATmega_relay_check()
            RFID_check()
            break
        
rtc=machine.RTC()#Real-Time-Clock defining
print(rtc.datetime())

def RTC_check(y,i2c_devices,results):#Real-Time-Clock hardware testing function
    global statusArr
    newFrame(1)
    display.set_pos(10, 60)
    display.set_color(color565(0, 0, 0), color565(255, 255, 255))
    display.print('Testing RTC')
    oldRtc=rtc.datetime()#Variable used to set RTC time to currect time
    try:
        rtc.datetime((2020, 1, 21, 2, 10, 32, 36, 0))#Writes RTC time
    except:#Finds out if the RTC writing works
        statusArr.append('* RTC communication: Write ERR')
        i2c_devices[1][2]='False'
    else:
         rtc.datetime((2020, 1, 21, 2, 10, 32, 36, 0))#Writes the RTC time
    try:
        print(rtc.datetime())#Reads the RTC time
    except:#Finds out if RTC hardware even works
        statusArr.append('* RTC communication: Read ERR')
        i2c_devices[1][2]='False'
    try:
         if rtc.datetime()[0] == 2020 and rtc.datetime()[4] == 10:#Checks if the RTC reads and writes perfectly
             display.set_pos(10, y)
    except:#If RTC doesn't work then it writes an error in RTC communication
        statusArr.append('* RTC communication ERR')
        i2c_devices[1][2]='False'
    else:
        if rtc.datetime()[0] == 2020 and rtc.datetime()[4] == 10:#Checks if the RTC reads and writes perfectly
            statusArr.append('* RTC communication: Write OK')
            statusArr.append('* RTC communication: Read OK')
            if results==True:#Used for result identification further on in the code
                results=False
            else:
                results=True
        else:#If RTC doesn't work then it writes an error in RTC communication
            statusArr.append('* RTC communication ERR')
            i2c_devices[1][2]='False'
    rtc.datetime(oldRtc)

def newFrame(pg):#Function for a new frame on the LCD display
    device=i2c.scan()
    display.erase()
    display.fill_rectangle(0 , 0, 240, 320, 65535)
    display.fill_rectangle(0 , 0, 240, 50, 008000)
    display.fill_rectangle(0 , 50, 240, 5, 000033)
    if checkU is not None and device != [] and checkU != b'\x00':#Checks if there is a ControlUnit connected
        display.set_pos(120, 285)
        display.set_font(tt24)
        display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        display.write("ControlUnit")
    elif checkU==b'\x00' and device != []:#Otherwise it shows that there is a TTunit connected
        display.set_pos(165, 285)
        display.set_font(tt24)
        display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        display.write("TTunit")
    elif device == []:#If there aren't any devices connected to RPi
        display.set_pos(130, 285)
        display.set_font(tt24)
        display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        display.write("No device")
    display.fill_rectangle(10 , 16, 85, 30, 111111)
    display.fill_rectangle(5 , 11, 85, 30, 65535)
    display.set_font(tt24)
    display.set_color(color565(0, 0, 0), color565(255, 255, 255))
    display.set_pos(10, 15)
    display.write('IN')
    display.set_color(color565(0, 255, 0), color565(255, 255, 255))
    display.set_pos(30, 15)
    display.write('PASS')
    display.set_font(tt14)
    display.set_color(color565(0, 0, 0), color565(255, 255, 255))
    if pg != 0 and pg != "res":#If there are any test numbers set it sets to needed test number
        display.set_pos(10, 300)
        display.write(str(pg)+". test")
    elif pg == "res":#If there is given a result signal it will set it as Results on frame
        display.set_pos(10, 300)
        display.write("Results")
    display.set_color(color565(0, 0, 0), color565(255, 255, 255))
    
def scan_i2c():#The main scanner function
    global mDevice, RFID_res, statusArr
    devices = i2c.scan()
    x=0
    rtc_found = False
    y=60

    if devices:#If there are I2C hardware used
        newFrame(0)
        display.set_pos(10, 60)
        display.print('* I2C devices found:')
        print("Found I2C devices")
        display.set_pos(135, 60)
        lvl=30
        display.print(str(hex(devices[0])+", "+str(hex(devices[1]))))
        if checkU is not None and checkU!=b'\x00':#Checks if there is a ControlUnit connected
            display.set_pos(10, 90)
            display.print('* ControlUnit device found')
            print("Found ControlUnit device")
        utime.sleep(2)
        newFrame(0)
        for device in devices:#Makes the I2C hardware status true for further results identification
            x=0
            for hexs, name, status in i2c_devices:
             if hexs == str(device):
                lvl=lvl+30
                display.set_pos(10, lvl)
                display.print('* '+name+' connected')
                i2c_devices[x][2]='True'
             x+=1
        if checkU is not None and checkU!=b'\x00':#Checks if there is a ControlUnit connected
            mDevice="ATmega"#Names the Unit according to the test
            lvl=lvl+30
            display.set_pos(10, lvl)
            display.print('* ControlUnit connected')
        elif checkU==b'\x00':
            mDevice="I2C"#Names the Unit according to the test
        print(str(x)+" I2C devices were found")
        utime.sleep(1)
        for device in i2c_devices:
            if 'True' in device:#Checks if the device has a "True" value
                true_found = True
                break
        if true_found:#If there is at least one "True"    
                        y=60
                        RTC_check(60,i2c_devices,results)#Runs the RTC_check function, y is used for the storing of the display location
                        EEPROM_check(y,i2c_devices,results)#Runs the EEPROM_check function, y is used for the storing of the display location
                        if checkU is not None and checkU!=b'\x00':#Checks if there is a ControlUnit connected
                            ATmega_check(y,results)#Runs the ATmega_check function, y is used for the storing of the display location
                        utime.sleep(0.3)
                        if checkU is not None and checkU!=b'\x00':
                            display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                            display.set_pos(170, 10)
                            display.set_font(tt14)
                            display.write("ON---------->")
                            display.set_pos(10, 265)
                            display.print('Alarm to confirm scan results')
                        elif checkU==b'\x00' and device != []:
                            display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                            display.set_pos(170, 10)
                            display.set_font(tt14)
                            display.write("Buzz------>")
                            display.set_pos(10, 265)
                            display.print('Buzz to confirm scan results')
                    
        else:#If there isn't any "True" found
          t=60
          newFrame(0)
          for hexs, names, status in i2c_devices:
            if status=="False":#Checks the I2C hardware for "False" values
                display.set_pos(0, t)
                display.set_color(color565(0, 0, 255), color565(255, 255, 255))
                display.print('* '+names+' not found.')
                print("The scanner didn't find "+names+" device")
                t+=30
           
    else:#If there aren't any I2C hardware found
        newFrame(0)
        display.set_pos(10, 60)
        display.set_color(color565(0, 0, 255), color565(255, 255, 255))
        display.print('* I2C devices not found.')
        print("There weren't any I2C devices found")
        mDevice=None
        btn_count=0
        
def scannerRestart(btn_count):#Function that lets the user restart scanner functions
   global mDevice, RFID_res
   if mDevice!=None:
    while True:#Meant for pressing a button
     if button.value() == 0:
      for i in range(2):
        btn_count += 1
        if btn_count ==1:#If the button is pressed one time goes through a buzzer test
            newFrame(0)
            if checkU is not None and checkU!=b'\x00':#If a ControlUnit is connected
                display.set_pos(10, 60)
                display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                display.print("Alarming")
                print("Buzzing!")
                M.Queue("SET","alarm_on_state",value=1)
                M.Send(True)
                utime.sleep(3)
                M.Queue("SET","alarm_on_state",value=0)
                M.Send(True)
            elif checkU==b'\x00':#If a TTunit is connected
                display.set_pos(10, 60)
                display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                display.print("Buzzing")
                display.set_pos(170, 10)
                display.set_font(tt14)
                print("Buzzing!")
                for x in range(5):
                    buzzer.on()
                    utime.sleep(0.1)
                    buzzer.off()
                    utime.sleep(0.1)
        elif btn_count==2:#If button is pressed two times shows results and lets the user restart the main scanner function
            newFrame("res")
            display.set_pos(160, 10)
            display.set_font(tt14)
            display.write("RESTART---->")
            if (i2c_devices[0][2]=="True" and i2c_devices[1][2]=="True" and atmega_found==True and mDevice=="ATmega" and RFID_res==['1.','2.','3.','4.']) or (i2c_devices[0][2]=="True" and i2c_devices[1][2]=="True" and mDevice=="I2C"):
                #Checks the status of all of the hardware, if every hardware is found and tested successfully
                k=60
                i=0
                for stat in statusArr:
                    i=i+1
                    display.set_pos(5, k)
                    display.set_font(tt14)
                    if "ERR" in stat or "ERROR" in stat:
                        display.set_color(color565(0, 0, 255), color565(255, 255, 255))
                        print("err")
                    display.write(stat)
                    if (i < 7 and mDevice=="ATmega") or mDevice=="I2C":
                        display.fill_rectangle(20 , k+15, 200, 2, 000033)
                    k=k+25
                    display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                display.fill_rectangle(0 , 240, 240, 5, 008000)
                display.set_pos(30, 250)
                display.set_font(tt24)
                display.set_color(color565(0, 255, 0), color565(255, 255, 255))
                display.write("Test successful!")
                print("The I2C scanner test was successful!")
            else:#If the hardware status isn't successful
                k=60
                i=0
                for stat in statusArr:
                    i=i+1
                    display.set_pos(5, k)
                    display.set_font(tt14)
                    if RFID_res != ['1.','2.','3.','4.'] and "readers" in stat:
                        display.set_color(color565(0, 0, 255), color565(255, 255, 255))
                    if ("ERR" in stat or "ERROR" in stat):
                        display.set_color(color565(0, 0, 255), color565(255, 255, 255))
                    display.write(stat)
                    if (i < 7 and mDevice=="ATmega") or mDevice=="I2C":
                        display.fill_rectangle(20 , k+15, 200, 2, 000033)
                    k=k+25
                    display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                display.set_pos(30, 250)
                display.fill_rectangle(0 , 240, 240, 5, 000030)
                display.set_font(tt24)
                display.set_color(color565(0, 0, 255), color565(255, 255, 255))
                display.write("Test unsuccessful!")
                print("The I2C scanner test was unsuccessful!")
            return btn_count
   elif mDevice==None:#If there isn't any device connected
       btn_count=0
       return btn_count
    
newFrame(0)#The first starting frame
print("Starting program")
display.set_pos(10, 60)
display.set_color(color565(0, 0, 0), color565(255, 255, 255))
display.print("* To Start press button")
display.set_pos(170, 10)
display.set_font(tt14)
display.write("PRESS---->")
while True:#If button is pressed restarts the main scanner function
    if button.value() == 0:
        if btn_count ==0:#If the start/restart button hasn't been pressed or has been reset
            print("1st")
            scan_i2c()
            btn_count=scannerRestart(btn_count)
        elif btn_count==2:#If the start/restart button has been pressed just once it confirms the test and restarts
            print("2nd")
            btn_count=0
            statusArr=[]
            RFID_res=[]
