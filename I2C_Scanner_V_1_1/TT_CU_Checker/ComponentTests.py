import machine
import json
import select
from display.ili934xnew import ILI9341, color565
from machine import Pin, SPI, UART
import tools.m5stack as m5stack
from tools.eeprom import EEPROM
import display.glcdfont as glcdfont
from micropython import const
import display.tt14 as tt14
import display.tt24 as tt24
import random
import display.tt32 as tt32
import os
import utime
import sys
from tools.MSG import MSG
from tools.Wiegand import Wiegand


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

        self.language_dict = GetLang()
        self.history_conf = GetConf()
        self.current_language = self.GetCurrentLang()

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
        self.results_list_to_send= []

        self.rtc=machine.RTC()#Real-Time-Clock defining

        self.NewFrame = NewFrame

        pass

    def ResetForTest(self):

        self.rfid_res = []
        self.results_list = []
        self.used_device = None
        self.page = 0

    def GetCurrentLang(self):
        if self.history_conf["language"] == "conf_eng":
            self.current_language = "english"
        elif self.history_conf["language"] == "conf_lat":
            self.current_language = "latvian"
        else:
            self.current_language = "english"   

    def SendRecieveData(self):

        poll_obj = select.poll()
        poll_obj.register(sys.stdin, select.POLLIN)

        while True:
            while True:

                poll_results = poll_obj.poll(1)
                if poll_results:

                    data = str(sys.stdin.readline().strip())
                    
                    if data == "receive":
                        print("transfer")
                        sys.stdout.write("transfer\r")
                        
                        for hist in self.history_conf["history"]:
                            print(hist,"\n")
                            utime.sleep(0.01)
                            
                        print(self.history_conf["language"],"\n")

                        print("END\n")

                        self.NewFrame("pc")
                        break
                    
                    elif data == "delete":
                        
                        sys.stdout.write("deleted\r")
                        self.history_conf["history"] = ["","", "start"]
                        
                        with open('/hist_conf.json', 'w') as file:
                            json.dump(self.history_conf, file)
                        break
                    
                    elif data == "lat":
                        
                        sys.stdout.write("lat_configured\r")
                        
                        self.history_conf["language"] = "conf-lat"
                        
                        with open('/hist_conf.json', 'w') as file:
                            json.dump(self.history_conf, file)
                        break
                    
                    elif data == "eng":
                        
                        self.history_conf["language"] = "conf-eng"
                        
                        with open('hist_conf.json', 'w') as file:
                            json.dump(self.history_conf, file)
                        
                        sys.stdout.write("eng_configured\r")
                        
                        break
                        
                else:

                    continue
            
            utime.sleep(0.01)    

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
            checkU=self.uart_id.read()#Variable used to find out if there is a ControlUnit connected or not
            print(checkU)
        except Exception as error:
            checkU = None
            print(error)
            
        return checkU
        

    def EEPROM_check(self):#EEPROM testing function
        self.NewFrame(self.page)
        random_arr = []
        self.display.set_pos(10, 60)
        self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.display.print(self.language_dict[self.current_language][0]["testing_eeprom"])
        try:

            for i in range(256):
                random_arr.append(RandomString())
                self.eprom.write(i*64, random_arr[i])
            
            self.results_list.append(self.language_dict[self.current_language][0]["eeprom_write_ok"])
            self.results_list_to_send.append("ee-true:")
            

        except:#Finds out if the EEPROM writing works
            self.results_list.append(self.language_dict[self.current_language][0]["eeprom_write_er"])
            self.results_list_to_send.append("ee-false:")
            self.i2c_devices[0][2]='False'

        try:
            
            for i in range(256):
                if random_arr[i] not in self.eprom.read(i*64,6):
                    break
            if i == 255:       
                self.results_list.append(self.language_dict[self.current_language][0]["eeprom_read_ok"])

                if "ee-false:" not in self.results_list_to_send and "ee-true" not in self.results_list_to_send:
                    self.results_list_to_send.append("ee-true:")
                
            else:
                self.results_list.append(self.language_dict[self.current_language][0]["eeprom_read_er"])
                if "ee-false:" not in self.results_list_to_send:

                    if "ee-true" in self.results_list_to_send:
                        self.results_list_to_send[0] = "ee-false:"
                    else:
                        self.results_list_to_send.append("ee-false:")

                self.i2c_devices[0][2]='False'

        except:#Finds out if the EEPROM reading works
            self.results_list.append(self.language_dict[self.current_language][0]["eeprom_read_er"])
            if "ee-false:" not in self.results_list_to_send:

                if "ee-true" in self.results_list_to_send:
                    self.results_list_to_send[0] = "ee-false:"
                else:
                    self.results_list_to_send.append("ee-false:")

            self.i2c_devices[0][2]='False'

        self.eprom.wipe()

    def RTC_check(self):#Real-Time-Clock hardware testing function
        self.NewFrame(self.page)

        self.display.set_pos(10, 60)
        self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.display.print(self.language_dict[self.current_language][0]["testing_rtc"])

        oldRtc=self.rtc.datetime()#Variable used to set RTC time to currect time

        try:
            self.rtc.datetime((2020, 1, 21, 2, 10, 32, 36, 0))#Writes RTC time

            self.results_list.append(self.language_dict[self.current_language][0]["rtc_write_ok"])
            self.results_list_to_send.append("rtc-true:")

        except:#Finds out if the RTC writing works
            self.results_list.append(self.language_dict[self.current_language][0]["rtc_write_er"])
            self.results_list_to_send.append("rtc-false:")
            self.i2c_devices[1][2]='False'

        try:
            if self.rtc.datetime()[0] == 2020 and self.rtc.datetime()[4] == 10:

                self.results_list.append(self.language_dict[self.current_language][0]["rtc_read_ok"])

                if "rtc-false:" not in self.results_list_to_send and "rtc-true" not in self.results_list_to_send:
                    self.results_list_to_send.append("rtc-true:")

        except:#Finds out if RTC hardware even works
            self.results_list.append(self.language_dict[self.current_language][0]["rtc_read_er"])

            if "rtc-false:" not in self.results_list_to_send:

                if "rtc-true" in self.results_list_to_send:
                    self.results_list_to_send[1] = "rtc-false:"
                else:
                    self.results_list_to_send.append("rtc-false:")

            self.i2c_devices[1][2]='False'

        self.rtc.datetime(oldRtc)

    def ATmega_check(self):#ControlUnit testing function
        self.NewFrame(self.page)

        self.display.set_pos(10, 60)
        self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.display.print(self.language_dict[self.current_language][0]["testing_cu"])

        ATmega = None
        
        try:
            ATmega=self.M.HWCheck()
        except:
            ATmega = False
            
        if ATmega ==True:
            self.results_list.append(self.language_dict[self.current_language][0]["cu_write_ok"])
            self.results_list.append(self.language_dict[self.current_language][0]["rtc_read_ok"])

            self.results_list_to_send.append("com-true:")

        else:#If the hardware check function gives out False value
            self.results_list.append(self.language_dict[self.current_language][0]["rtc_write_er"])
            self.results_list.append(self.language_dict[self.current_language][0]["rtc_read_er"])

            self.results_list_to_send.append("com-false:")
            
    def ATmega_relay_check(self):#Relay testing function
        signalArr=["turnstile1_a","turnstile1_b","turnstile2_a","turnstile2_b","button1","button2"]#Array of all test-needed relays
        for relayName in signalArr:#Goes through each test-needed relays
            self.NewFrame(self.page)
            self.display.set_pos(10, 60)
            self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
            self.display.print('* '+relayName+self.language_dict[self.current_language][0]["cu_testing"])
            self.display.fill_rectangle(5, 90, 180, 45, 008000)
            self.display.set_pos(10, 100)
            self.display.set_font(tt24)
            self.display.print(self.language_dict[self.current_language][0]["cu_relays"])
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
            self.display.write(self.language_dict[self.current_language][0]["press_button"])

            self.display.set_pos(10, 60)
            self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
            self.display.print('* '+str(i+1)+self.language_dict[self.current_language][0]["w_test"])

            self.display.fill_rectangle(5, 90, 215, 45, 008000)

            self.display.set_pos(10, 100)
            self.display.set_font(tt24)
            self.display.print(self.language_dict[self.current_language][0]["w_next_test"])

            self.display.set_font(tt14)
            self.display.set_pos(10, 160)
            self.display.print(self.language_dict[self.current_language][0]["w_card_data"])

            self.display.set_pos(10, 190)
            self.display.print(self.language_dict[self.current_language][0]["w_card_data_rev"])

            self.display.set_pos(10, 220)
            self.display.print(self.language_dict[self.current_language][0]["w_card_type"])

            while True:
                if wiegand_reader.available():#Checks if card has been scanned by the RFID card reader
                    
                    loop+=1
                    
                    for x in range(3):
                        led.high()
                        buz.high()

                        utime.sleep(0.3)

                        led.low()
                        buz.low()

                    utime.sleep(0.4)

                    card_code = wiegand_reader.GetCode()# Gets the card code
                    self.display.set_pos(10, 160)
                    self.display.print(self.language_dict[self.current_language][0]["w_card_data"] + str(card_code))


                    card_revCode=wiegand_reader.GetRevCode()
                    self.display.set_pos(10, 190)
                    self.display.print(self.language_dict[self.current_language][0]["w_card_data_rev"] + str(card_revCode))                        

                    card_type = wiegand_reader.GetType()# Gets the RFID bit type
                    self.display.set_pos(10, 220)
                    self.display.print(self.language_dict[self.current_language][0]["w_card_type"] + str(card_type))
                    
                    if loop == 1:

                        self.rfid_res.append(str(i+1)+'.')#Puts the RFID card reader functionality status

                button_pressed = self.main_button.value() == 0  # Check if the button is pressed

                if button_pressed:
                    loop = 0
                    break

        if self.rfid_res==[]:#If there aren't any working card readers it puts in the status array information for results showcase

            self.results_list.append(self.language_dict[self.current_language][0]["w_test_er"])

        elif self.rfid_res != []:#If there are working card readers it puts in the status array information for results showcase

            self.results_list.append('* '+str(len(self.rfid_res))+self.language_dict[self.current_language][0]["w_test_ok"])

            for i in range(4):
                if str(i+1)+"." in self.rfid_res:
                    self.results_list_to_send.append("w"+str(i+1)+"-true:")
                else:
                    self.results_list_to_send.append("w"+str(i+1)+"-false:")



def RandomString(length=6):
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def GetLang():
    with open('/language_dict.json', encoding='utf-8') as f:
        data = json.load(f)
    return data

def GetConf():
    try:
        open('/conf.json', encoding='utf-8')

    except:
        obj = {"language": "conf-eng", "history": ["","","start"]}

        with open('/conf.json', 'w+') as f:
            json.dump(obj, f)

    with open('/conf.json', encoding='utf-8') as f:
        data = json.load(f)
    return data