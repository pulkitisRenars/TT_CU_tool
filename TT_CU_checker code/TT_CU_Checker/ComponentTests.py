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

# Konstantes, kas vajadzīgas komponenšu pārbaudēm un displeja izvadei.
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

    # Konstruktors, kas izveido attiecošās vērtbības korektai programmatūras izpildei.
    def __init__(self, NewFrame):

        self.main_button = Pin(25, Pin.IN, Pin.PULL_UP)
        self.TT_buzzer = Pin(24,Pin.OUT)
        self.page = 0

        # Ievieto sarakstē displeja saskarnes vārdnīcu.
        self.language_dict = GetLang()

        # Ievieto sarakstē rezultātu vēsturi un izmantojamo valodu.
        self.history_conf = GetConf()

        # Ievieto mainīgajā nolasīto izmantojamo valodu.
        self.current_language = self.GetCurrentLang()

        self.spi = SPI( 0, baudrate=40000000, miso=Pin(TFT_MISO_PIN), mosi=Pin(TFT_MOSI_PIN), sck=Pin(TFT_CLK_PIN) )

        # Objekta konstruēšana ar kuras palīdzību atlasa pievienotās I2C komponentes. 
        self.i2c=machine.I2C( 0, sda=sda, scl=scl, freq=400000 )

        self.used_device = None

        self.i2c_devices=[['104','EEPROM','True'],['80','RTC','True']]

        self.rfid_res = []

        # Objekta konstruktēšana ar kuras palīdzību noskaidro vai ControlUnit mikročips tiek pievienots.
        self.uart_id=UART( 1, baudrate=57600, timeout=1, invert=3 )

        self.M = MSG(print)

        self.display = ILI9341( self.spi, cs=Pin(TFT_CS_PIN), dc=Pin(TFT_DC_PIN), rst=Pin(TFT_RST_PIN), w=SCR_WIDTH, h=SCR_HEIGHT, r=SCR_ROT)
        
        self.eprom=EEPROM( addr=80, pages=256, bpp=64, i2c=self.i2c, at24x=0 )
        
        # Real-Time-Clock objekta konstruktēšana
        self.rtc=machine.RTC()

        self.results_list = []
        self.results_list_to_send= []

        self.NewFrame = NewFrame

        pass

    # Funkcija, kas attīra visus iespējamos saglabātos mikročipu datus uz programmatūras.
    def ResetForTest(self):

        self.rfid_res = []
        self.results_list = []
        self.used_device = None
        self.page = 0

    # Funkcija, kas atlasa izmantojamo valodu no ielādētā ".json" faila.
    def GetCurrentLang(self):
        if self.history_conf["language"] == "conf-eng":
            current_language = "english"
        elif self.history_conf["language"] == "conf-lat":
            current_language = "latvian"
        else:
            current_language = "english"
            
        return current_language

    # Bezgalīga cikla funkcija, kas veic datu plūsmu ar darbstaciju.
    def SendRecieveData(self):

        # Veic datu plūsmas apstiprinājuma uzgaidi.
        poll_obj = select.poll()
        poll_obj.register(sys.stdin, select.POLLIN)

        # Bezgalīgs cikls, programmatūra netiek virzīta vairs uz citu sazarojumu.
        while True:
            while True:

                # Ja datu plūsmas apstiprinājums tiek saņemts.
                poll_results = poll_obj.poll(1)
                if poll_results:
                    
                    # Nolasa apstiprinājuma ziņu no darbstacijas.
                    data = str(sys.stdin.readline().strip())
                    
                    if data == "receive":

                        # Nosūta apstiprinājuma atbildi uz darbstaciju.
                        print("transfer")
                        sys.stdout.write("transfer\r")

                        # Nosūta mikročipu pārbaudes vēsturi uz darbstaciju.
                        for hist in self.history_conf["history"]:
                            print(hist,"\n")
                            utime.sleep(0.01)

                        # Nosūta izmantojamo saskarnes valodu uz darbstaciju.
                        print(self.history_conf["language"],"\n")

                        # Nosūta ziņu, ka datu plūsma ir pabeigta
                        print("END\n")

                        # Izveido jaunu displeja kadru, kas liecina, ka rīks savienots ar darbstaciju.
                        self.NewFrame("pc")
                        
                        self.display.set_pos(10, 60)
                        self.display.print(self.language_dict[self.current_language][0]["pc_connected_label"])
                        
                        break
                    
                    elif data == "delete":

                        # Nosūta apstiprinājuma atbildi uz darbstaciju.
                        sys.stdout.write("deleted\r")

                        # Izveido tukšu datni, bet ar nepieciešamu datnes sākumu.
                        self.history_conf["history"] = ["","", "start"]
                        
                        # ieraksta tukšo datni ".json" failā.
                        with open('/conf.json', 'w') as file:
                            json.dump(self.history_conf, file)
                        
                        # Izveido jaunu displeja kadru, kas liecina, ka rīks savienots ar darbstaciju un pārbaudes rezultātu vēsture tiek izdzēsta.
                        self.NewFrame("pc")
                        
                        self.display.set_pos(10, 60)
                        self.display.print(self.language_dict[self.current_language][0]["deleted_history"])
                        break
                    
                    elif data == "lat":
                        
                        # Nosūta apstiprinājuma atbildi uz darbstaciju.
                        sys.stdout.write("lat_configured\r")
                        
                        # Pārmaina datni, lai tā būtu balstīta uz latviešu valodu.
                        self.history_conf["language"] = "conf-lat"
                        
                        with open('/conf.json', 'w') as file:
                            json.dump(self.history_conf, file)
                            
                        self.current_language = self.GetCurrentLang()
                        
                        # Izveido jaunu displeja kadru, kas liecina, ka rīks savienots ar darbstaciju un saskarnes valodas maiņa tiek mainīta.
                        self.NewFrame("pc")
                        
                        self.display.set_pos(10, 60)
                        self.display.print(self.language_dict[self.current_language][0]["changed_language"])
                        break
                    
                    elif data == "eng":

                        # Nosūta apstiprinājuma atbildi uz darbstaciju.
                        sys.stdout.write("eng_configured\r")

                        # Nosūta apstiprinājuma atbildi uz darbstaciju.
                        self.history_conf["language"] = "conf-eng"
                        
                        with open('conf.json', 'w') as file:
                            json.dump(self.history_conf, file)
                            
                        self.current_language = self.GetCurrentLang()
                        
                        # Izveido jaunu displeja kadru, kas liecina, ka rīks savienots ar darbstaciju un saskarnes valodas maiņa tiek mainīta.
                        self.NewFrame("pc")
                        
                        self.display.set_pos(10, 60)
                        self.display.print(self.language_dict[self.current_language][0]["changed_language"])
                        
                        break
                        
                else:

                    continue
            
            utime.sleep(0.01)    

    # Funkcija, kas veic pirms pārbaudi par pievienotā mikročipa EEPROM komponenti.
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
            
        try:
            self.eprom.wipe()
        except:
            eeprom_check = False
            
        return eeprom_check

    # Funkcija, kas veic pirms pārbaudi par pievienotā ControlUnit mikročipa komunikācijas stāvokli.
    def UartComPreTest(self):
        try:
            self.M.Queue("GET","board_version")
            self.M.Send(True)
            self.M.Receive(True)

            checkU=self.uart_id.read()
            
        except Exception:
            checkU = None
            
        return checkU
        
    # EEPROM komponentes pārbaudes funkcija.
    def EEPROM_check(self):
        
        # Izveido jaunu kadru, kas liecina, ka tiek pārbaudīta komponente.
        self.NewFrame(self.page)

        random_arr = []

        self.display.set_pos(10, 60)
        self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.display.print(self.language_dict[self.current_language][0]["testing_eeprom"])

        # Ieraksta nejaušas secības simbolus uz EEPROM komponentes atmiņas katrā lapā.
        try:

            for i in range(256):
                random_arr.append(RandomString())
                self.eprom.write(i*64, random_arr[i])
            
            self.results_list.append(self.language_dict[self.current_language][0]["eeprom_write_ok"])
            self.results_list_to_send.append("ee-true:")
            
        # Ja rakstīšana uz EEPROM komponentes nestrādā.
        except:
            self.results_list.append(self.language_dict[self.current_language][0]["eeprom_write_er"])
            self.results_list_to_send.append("ee-false:")
            self.i2c_devices[0][2]='False'

        # Nolasa tikko ierakstītās nejaušās secības simbolu vērtības uz EEPROM komponentes.
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

        # Ja lasīšana uz EEPROM komponentes nestrādā.
        except:
            self.results_list.append(self.language_dict[self.current_language][0]["eeprom_read_er"])
            if "ee-false:" not in self.results_list_to_send:

                if "ee-true" in self.results_list_to_send:
                    self.results_list_to_send[0] = "ee-false:"
                else:
                    self.results_list_to_send.append("ee-false:")

            self.i2c_devices[0][2]='False'

        # Izveido tukšu EEPROM komponentes atmiņu.
        self.eprom.wipe()

    # Real-Time-Clock komponentes pārbaudes funkcija.
    def RTC_check(self):

        # Izveido jaunu kadru, kas liecina, ka tiek pārbaudīta komponente.
        self.NewFrame(self.page)

        self.display.set_pos(10, 60)
        self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.display.print(self.language_dict[self.current_language][0]["testing_rtc"])

        # Saglabā šī brīža saglabāto laiku no Real-Time-Clock komponentes.
        oldRtc=self.rtc.datetime()

        # Ieraksta jaunu datumu uz Real-Time-Clock komponentes.
        try:
            self.rtc.datetime((2020, 1, 21, 2, 10, 32, 36, 0))

            self.results_list.append(self.language_dict[self.current_language][0]["rtc_write_ok"])
            self.results_list_to_send.append("rtc-true:")

        # Ja Real-Time-Clock komponentes rakstīšana nestrādā.
        except:
            self.results_list.append(self.language_dict[self.current_language][0]["rtc_write_er"])
            self.results_list_to_send.append("rtc-false:")
            self.i2c_devices[1][2]='False'

        # Nolasa vai tikko ierakstītais datums sakrīt ar gadu un minūtēm.
        try:
            if self.rtc.datetime()[0] == 2020 and self.rtc.datetime()[4] == 10:

                self.results_list.append(self.language_dict[self.current_language][0]["rtc_read_ok"])

                if "rtc-false:" not in self.results_list_to_send and "rtc-true" not in self.results_list_to_send:
                    self.results_list_to_send.append("rtc-true:")

        # Ja Real-Time-Clock komponentes lasīšana nestrādā.
        except:
            self.results_list.append(self.language_dict[self.current_language][0]["rtc_read_er"])

            if "rtc-false:" not in self.results_list_to_send:

                if "rtc-true" in self.results_list_to_send:
                    self.results_list_to_send[1] = "rtc-false:"
                else:
                    self.results_list_to_send.append("rtc-false:")

            self.i2c_devices[1][2]='False'

        # Ievieto atpakaļ oriģinālo laiku uz Real-Time-Clock komponentes
        self.rtc.datetime(oldRtc)

    # Komunikācijas pārbaudes funkcija starp rīku un ControlUnit
    def ATmega_check(self):

        # Izveido jaunu kadru, kas liecina, ka tiek pārbaudīta savstarpējā komunikācija.
        self.NewFrame(self.page)

        self.display.set_pos(10, 60)
        self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
        self.display.print(self.language_dict[self.current_language][0]["testing_cu"])

        ATmega = None
        
        # Ar ControlUnit komunikācijas pārbaudes funkciju noskaidro vai lasīšana un rakstīšana darbojas.
        try:
            ATmega=self.M.HWCheck()
        except:
            ATmega = False
            
        if ATmega ==True:
            self.results_list.append(self.language_dict[self.current_language][0]["cu_write_ok"])
            self.results_list.append(self.language_dict[self.current_language][0]["rtc_read_ok"])

            self.results_list_to_send.append("com-true:")

        # Ja atbilde no funkcijas ir False.
        else:
            self.results_list.append(self.language_dict[self.current_language][0]["rtc_write_er"])
            self.results_list.append(self.language_dict[self.current_language][0]["rtc_read_er"])

            self.results_list_to_send.append("com-false:")
            
    # ControlUnit releju aktivizēšanas funkcija.     
    def ATmega_relay_check(self):

        # Sarakste ar visiem pārbaudāmajiem releju nosaukumiem.
        signalArr=["turnstile1_a","turnstile1_b","turnstile2_a","turnstile2_b","button1","button2"]

        # Iet cauri katram releja nosaukumam.
        for relayName in signalArr:

            # Izvada attiecošo informāciju par releju.
            self.NewFrame(self.page)

            self.display.set_pos(10, 60)
            self.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
            self.display.print('* '+relayName+self.language_dict[self.current_language][0]["cu_testing"])

            self.display.fill_rectangle(5, 90, 180, 45, 008000)
            self.display.set_pos(10, 100)
            self.display.set_font(tt24)
            self.display.print(self.language_dict[self.current_language][0]["cu_relays"])

            self.display.set_font(tt14)

            # Nosūta releja aktivizēšanas komandu uz ControlUnit.
            self.M.Queue("SIGNAL",relayName)
            self.M.Send(True)

            self.page+=1

            utime.sleep(3)

    # Karšu lasītāja pārbaudes funkcija.
    def RFID_check(self):

        # Karšu lasītāja adreses uz ControlUnit.
        RFID_adr=[[2,3,6,8],[9,10,7,11],[14,15,26,13],[28,29,6,27]]

        loop=0

        # Iet cauri katrai ControlUnit karšu lasītāja adresēm.
        for i, add in enumerate(RFID_adr):
            self.page+=1

            # Pievieno adreses uz Wiegand klases, lai karšu lasītājus varētu izmantot.
            wiegand_reader = Wiegand(add[0], add[1])

            # Karšu lasītāja LED gaisma un zumers.
            led=Pin(add[2],Pin.OUT)
            buz=Pin(add[3],Pin.OUT)

            # Izvada attiecošo informāciju par karšu lasītāja pārbaudi.
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

            # Bezgalīgs cikls, kurš gaida signālu no metodes, ka karšu lasītāja dati ir saņemti.
            while True:

                # Ja karšu lasītāja dati ir saņemti.
                if wiegand_reader.available():
                    
                    loop+=1
                    
                    # Signalizē kartes noskenēšanos
                    for x in range(3):
                        led.high()
                        buz.high()

                        utime.sleep(0.3)

                        led.low()
                        buz.low()

                    utime.sleep(0.4)

                    # Uz ekrāna izvada nolasītās kartes informāciju
                    card_code = wiegand_reader.GetCode()
                    self.display.set_pos(10, 160)
                    self.display.print(self.language_dict[self.current_language][0]["w_card_data"] + str(card_code))


                    card_revCode=wiegand_reader.GetRevCode()
                    self.display.set_pos(10, 190)
                    self.display.print(self.language_dict[self.current_language][0]["w_card_data_rev"] + str(card_revCode))                        

                    card_type = wiegand_reader.GetType()
                    self.display.set_pos(10, 220)
                    self.display.print(self.language_dict[self.current_language][0]["w_card_type"] + str(card_type))
                    
                    if loop == 1:

                        # Pievieno sarakstei karšu lasītāja pārbaudes rezultātu.

                        self.rfid_res.append(str(i+1)+'.')

                button_pressed = self.main_button.value() == 0

                # Ja poga nospiesta, tad cikls beidzas un seko uz tālāko karšu lasītāja adresi.
                if button_pressed:
                    loop = 0
                    break

        # Ja nav nolasīta neviena karts no karšu lasītāja, tad ievieto sarakstē atbilstošu tekstu.
        if self.rfid_res==[]:

            self.results_list.append(self.language_dict[self.current_language][0]["w_test_er"])

        # Ja tiek nolasīta karts no karšu lasītāja, tad tos saglabā sarakstē.
        elif self.rfid_res != []:

            self.results_list.append('* '+str(len(self.rfid_res))+self.language_dict[self.current_language][0]["w_test_ok"])

        # Saglabā datnē karšu lasītāja rezultātus.
        for i in range(4):
            if str(i+1)+"." in self.rfid_res:
                self.results_list_to_send.append("w"+str(i+1)+"-true:")
            else:
                self.results_list_to_send.append("w"+str(i+1)+"-false:")

# Funkcija, kas uzģenerē nejaušas secības simbolus.
def RandomString(length=6):
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

# Funkcija, kas nolasa no faila rīka saskarnes valodas vārdnīcu.
def GetLang():
    with open('/language_dict.json', encoding='utf-8') as f:
        data = json.load(f)
    return data

# Funkcija, kas nolasa saglabātos pārbaudes rezultātu datus un izmantojamo valodu.
def GetConf():

    # Ja nav atrasts fails, tad to izveido.
    try:
        open('/conf.json', encoding='utf-8')

    except:
        obj = {"language": "conf-eng", "history": ["","","start"]}

        with open('/conf.json', 'w+') as f:
            json.dump(obj, f)

    with open('/conf.json', encoding='utf-8') as f:
        data = json.load(f)
    return data