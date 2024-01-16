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

sda=machine.Pin(0)
scl=machine.Pin(1)


class ComponentTests:
    def __init__(self):

        self.main_button = Pin(25, Pin.IN, Pin.PULL_UP)
        self.TT_buzzer = Pin(24,Pin.OUT)
        self.page = 0

        self.spi = SPI( 0, baudrate=40000000, miso=Pin(TFT_MISO_PIN), mosi=Pin(TFT_MOSI_PIN), sck=Pin(TFT_CLK_PIN) )
        self.i2c=machine.I2C( 0, sda=sda, scl=scl, freq=400000 )

        self.used_device = None

        self.i2c_devices=[['104','EEPROM','False'],['80','RTC','False']]

        self.uart_id=UART( 1, baudrate=57600, timeout=1, invert=3 )#Object used to find out if there is a ControlUnit connected or not

        self.M = MSG(print)

        self.display = ILI9341( self.spi, cs=Pin(TFT_CS_PIN), dc=Pin(TFT_DC_PIN), rst=Pin(TFT_RST_PIN), w=SCR_WIDTH, h=SCR_HEIGHT, r=SCR_ROT)
        
        self.eprom=EEPROM( addr=80, pages=256, bpp=64, i2c=self.i2c, at24x=0 )
        
        self.rtc=machine.RTC()#Real-Time-Clock defining

        self.results_list = []

        self.rtc=machine.RTC()#Real-Time-Clock defining
        pass

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

    def UartComPreTest(self):
        try:
            self.M.Queue("GET","board_version")
            self.M.Send(True)
            self.M.Receive(True)
            checkU=self.uartID.read()#Variable used to find out if there is a ControlUnit connected or not
            print(checkU)
        except:
            checkU = None

    def EEPROM_check(self):#EEPROM testing function
        newFrame(self.page)
        random_arr = []
        self.self.display.set_pos(10, 60)
        self.self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.self.display.print('Testing EEPROM')
        try:

            for i in range(256):
                random_arr.append(RandomString())
                self.eprom.write(i*64, random_arr[i])
            
            self.results_list.append('* EEPROM communication: Write OK')

        except:#Finds out if the EEPROM writing works
            self.results_list.append('* EEPROM communication: Write ERR')
            i2c_devices[1][2]='False'

        try:
            
            for i in range(256):
                if random_arr[i] not in self.eprom.read(i*64,6):
                    break
            if i == 255:       
                self.results_list.append('* EEPROM communication: Read OK')
            else:
                self.results_list.append('* EEPROM communication: Read ERR')

        except:#Finds out if the EEPROM reading works
            self.results_list.append('* EEPROM communication: Read ERR')
            i2c_devices[1][2]='False'

        self.eprom.wipe()

    def RTC_check(self):#Real-Time-Clock hardware testing function
        global statusArr
        newFrame(self.page)

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
            self.results_list.statusArr.append('* RTC communication: Read ERR')
            self.i2c_devices[1][2]='False'

        self.rtc.datetime(oldRtc)

    def ATmega_check(self,y,results):#ControlUnit testing function
        newFrame(3)
        self.display.set_pos(10, 60)
        self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.display.print('Testing ControlUnit')
        atmega_found=False#Variable used for the ControlUnits functionality identification
        ATmega = None
        try:
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
        self.display.set_pos(130, 10)
        self.display.set_font(tt14)
        self.display.write("TEST RELAYS---->")
        while True:
            button_pressed = button.value() == 0  # Check if the button is pressed
            if button_pressed:
                ATmega_relay_check()
                RFID_check()
                break


def RandomString(length=6):
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string