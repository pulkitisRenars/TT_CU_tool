import machine
from I2C_Scanner_V_1_1.display.ili934xnew import ILI9341, color565
from machine import Pin, SPI, UART
import I2C_Scanner_V_1_1.tools.m5stack as m5stack
from I2C_Scanner_V_1_1.tools.eeprom import EEPROM
import I2C_Scanner_V_1_1.display.glcdfont as glcdfont
from micropython import const
import I2C_Scanner_V_1_1.display.tt14 as tt14
import I2C_Scanner_V_1_1.display.tt24 as tt24
import random
import I2C_Scanner_V_1_1.display.tt32 as tt32
import os
import utime
import sys
from I2C_Scanner_V_1_1.tools.MSG import MSG
from I2C_Scanner_V_1_1.tools.Wiegand import Wiegand


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

sda=machine.Pin(0)
scl=machine.Pin(1)


class ComponentTests:
    def __init__(self, NewFrame):

        self.main_button = Pin(25, Pin.IN, Pin.PULL_UP)
        self.TT_buzzer = Pin(24,Pin.OUT)
        self.page = 0

        self.spi = SPI( 0, baudrate=40000000, miso=Pin(TFT_MISO_PIN), mosi=Pin(TFT_MOSI_PIN), sck=Pin(TFT_CLK_PIN) )
        self.i2c=machine.I2C( 0, sda=sda, scl=scl, freq=400000 )

        self.used_device = None

        self.i2c_devices=[['104','EEPROM','False'],['80','RTC','False']]

        self.rfid_res = []

        self.uart_id=UART( 1, baudrate=57600, timeout=1, invert=3 )#Object used to find out if there is a ControlUnit connected or not

        self.M = MSG(print)

        self.display = ILI9341( self.spi, cs=Pin(TFT_CS_PIN), dc=Pin(TFT_DC_PIN), rst=Pin(TFT_RST_PIN), w=SCR_WIDTH, h=SCR_HEIGHT, r=SCR_ROT)
        
        self.eprom=EEPROM( addr=80, pages=256, bpp=64, i2c=self.i2c, at24x=0 )
        
        self.rtc=machine.RTC()#Real-Time-Clock defining

        self.results_list = []

        self.rtc=machine.RTC()#Real-Time-Clock defining

        self.NewFrame = NewFrame

        pass


    def ResetForTest(self):

        self.rfid_res = []
        self.results_list = []
        self.used_device = None
        self.page = 0

    def EepromPreTest(self):
        try:
            for i in range(10):
                self.eprom.write(0, "test")
                epromVal=self.eprom.read(0,4)
        except:
            eeprom_check = False
            print(eeprom_check)
        else:
            eeprom_check = True
            print(eeprom_check)
        self.eprom.wipe()
        return eeprom_check

    def UartComPreTest(self):
        try:
            self.M.Queue("GET","board_version")
            self.M.Send(True)
            self.M.Receive(True)
            checkU=self.uartID.read()#Variable used to find out if there is a ControlUnit connected or not
            print(checkU)
            return checkU
        except:
            checkU = None
            return checkU
        

    def EEPROM_check(self):#EEPROM testing function
        self.NewFrame(self.page)
        random_arr = []
        self.display.set_pos(10, 60)
        self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.display.print('Testing EEPROM')
        try:

            for i in range(256):
                random_arr.append(RandomString())
                self.eprom.write(i*64, random_arr[i])
            
            self.results_list.append('* EEPROM communication: Write OK')
            

        except:#Finds out if the EEPROM writing works
            self.results_list.append('* EEPROM communication: Write ERR')
            self.i2c_devices[0][2]='False'

        try:
            
            for i in range(256):
                if random_arr[i] not in self.eprom.read(i*64,6):
                    break
            if i == 255:       
                self.results_list.append('* EEPROM communication: Read OK')
                
            else:
                self.results_list.append('* EEPROM communication: Read ERR')
                self.i2c_devices[0][2]='False'

        except:#Finds out if the EEPROM reading works
            self.results_list.append('* EEPROM communication: Read ERR')
            self.i2c_devices[0][2]='False'

        self.eprom.wipe()

    def RTC_check(self):#Real-Time-Clock hardware testing function
        self.NewFrame(self.page)

        self.display.set_pos(10, 60)
        self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.display.print('Testing RTC')

        oldRtc=self.rtc.datetime()#Variable used to set RTC time to currect time

        try:
            self.rtc.datetime((2020, 1, 21, 2, 10, 32, 36, 0))#Writes RTC time

            self.results_list.append('* RTC communication: Write OK')

        except:#Finds out if the RTC writing works
            self.results_list.append('* RTC communication: Write ERR')
            self.i2c_devices[1][2]='False'

        try:
            if self.rtc.datetime()[0] == 2020 and self.rtc.datetime()[4] == 10:

                self.results_list.append('* RTC communication: Read OK')

        except:#Finds out if RTC hardware even works
            self.results_list.append('* RTC communication: Read ERR')
            self.i2c_devices[1][2]='False'

        self.rtc.datetime(oldRtc)

    def ATmega_check(self):#ControlUnit testing function
        self.NewFrame(self.page)

        self.display.set_pos(10, 60)
        self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.display.print('Testing ControlUnit')

        ATmega = None
        
        try:
            ATmega=self.M.HWCheck()
        except:
            ATmega = False
        y+=30
        if ATmega ==True:
            self.results_list.append('* ConUnit communication: Write OK')
            self.results_list.append('* ConUnit communication: Read OK')

        else:#If the hardware check function gives out False value
            self.results_list.append('* ConUnit communication: Write ERR')
            self.results_list.append('* ConUnit communication: Read ERR')
            
    def ATmega_relay_check(self):#Relay testing function
        signalArr=["turnstile1_a","turnstile1_b","turnstile2_a","turnstile2_b","button1","button2"]#Array of all test-needed relays
        for relayName in signalArr:#Goes through each test-needed relays
            self.NewFrame(self.page)
            self.display.set_pos(10, 60)
            self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
            self.display.print('* '+relayName+' testing')
            self.display.fill_rectangle(5, 90, 180, 45, 008000)
            self.display.set_pos(10, 100)
            self.display.set_font(tt24)
            self.display.print("Listen for relay!")
            self.display.set_font(tt14)
            self.M.Queue("SIGNAL",relayName)#Signals ControlUnit to turn on relay
            self.M.Send(True)
            self.page+=1
            utime.sleep(3)

    def RFID_check(self): # RFID card reader testing function

        RFID_adr=[[2,3,6,8],[9,10,7,11],[14,15,26,13],[28,29,6,27]]#RFID card reader addresses

        loop=0

        for i, add in enumerate(RFID_adr):#Goes through each pin address to test
            self.page+=1
            wiegand_reader = Wiegand(add[0], add[1])#Sets the pin addresses to work with the wiegand protocol

            led=Pin(add[2],Pin.OUT)
            buz=Pin(add[3],Pin.OUT)

            self.NewFrame(self.page)

            self.display.set_pos(170, 10)
            self.display.set_font(tt14)
            self.display.write("PRESS---->")

            self.display.set_pos(10, 60)
            self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
            self.display.print('* '+str(i+1)+'. Wiegand device address testing')

            self.display.fill_rectangle(5, 90, 215, 45, 008000)

            self.display.set_pos(10, 100)
            self.display.set_font(tt24)
            self.display.print("For next test press")

            self.display.set_font(tt14)
            self.display.set_pos(10, 160)
            self.display.print("Wiegand Card Data:")

            self.display.set_pos(10, 190)
            self.display.print("Wiegand Card Data(rev):")

            self.display.set_pos(10, 220)
            self.display.print("Wiegand Type(bits):")

            while True:
                if wiegand_reader.available() and loop==0:#Checks if card has been scanned by the RFID card reader
                    for x in range(2):
                        led.high()
                        buz.high()

                        utime.sleep(0.4)

                        led.low()
                        buz.low()

                        utime.sleep(0.4)

                    if loop==0:
                        loop=1

                        card_code = wiegand_reader.GetCode()# Gets the card code
                        self.display.set_pos(10, 160)
                        self.display.print("RFID Card Data:" + str(card_code))


                        card_revCode=wiegand_reader.GetRevCode()
                        self.display.set_pos(10, 190)
                        self.display.print("Wiegand Card Data(rev):" + str(card_revCode))                        

                        card_type = wiegand_reader.GetType()# Gets the RFID bit type
                        self.display.set_pos(10, 220)
                        self.display.print("Wiegand Type(bits):" + str(card_type))

                        self.rfid_res.append(str(i+1)+'.')#Puts the RFID card reader functionality status

                button_pressed = self.button.value() == 0  # Check if the button is pressed

                if button_pressed:
                    loop=0

                    break

        if self.rfid_res==[]:#If there aren't any working card readers it puts in the status array information for results showcase

            self.results_list.append('* 0 Wiegand readers work: ERR')

        elif self.rfid_res != []:#If there are working card readers it puts in the status array information for results showcase

            self.results_list.append('* '+len(self.rfid_res)+' Wiegand readers work')



def RandomString(length=6):
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string