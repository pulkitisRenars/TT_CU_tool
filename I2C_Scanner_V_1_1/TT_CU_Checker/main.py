"""
TT/CU skenera startējamā programmatūra, kas atrodas uz rīka ierīces.
"""

import machine
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
import json
import sys
from tools.MSG import MSG
from tools.Wiegand import Wiegand
from ComponentTests import ComponentTests

# Mikročipu rezultātu pievienošana ".json" failam.
def AddToHistory(data):
    CT.history_conf["history"].append(data)

    # Ar open() funkcijas palīdzību atver ".json" failu un ievieto rezultāta vērtības.
    with open('/conf.json', 'w') as file:
        json.dump(CT.history_conf, file)

#Funkcija, kas izveido jaunu kadru uz rīka displeja
def newFrame(page):
    device=CT.i2c.scan()

    # Izveido tukšu displeja ekrānu ar navigācijas joslu.
    CT.display.erase()
    CT.display.fill_rectangle(0 , 0, 240, 320, 65535)
    CT.display.fill_rectangle(0 , 0, 240, 50, 008000)
    CT.display.fill_rectangle(0 , 50, 240, 5, 000033)

    # Pārbauda vai ir pievienots ControlUnit mikročips.
    if check_uart is not None and device != [] and check_uart != b'\x00':
        CT.display.set_pos(120, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

        CT.display.write("ControlUnit")

    # Pārbauda vai ir pievienots TTunit mikročips.
    elif check_uart==b'\x00' and device != []:
        CT.display.set_pos(165, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

        CT.display.write("TTunit")

    # Pārbauda vai vispārēji ir pievienota ierīce.
    elif device == [] and page != "pc":
        CT.display.set_pos(110, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))
        print(CT.current_language)
        CT.display.write(CT.language_dict[CT.current_language][0]["no_device"])

    # Ja jauna kadra izveide tiek izsaukta pēc darbstacijas pievienošānas.
    if page == "pc":
        CT.display.set_pos(130, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

        CT.display.write(CT.language_dict[CT.current_language][0]["pc_connected"])

    # Izveido "InPass" logo uz displeja navigācijas joslas.
    CT.display.fill_rectangle(10 , 16, 85, 30, 808080)
    CT.display.fill_rectangle(5 , 11, 85, 30, 65535)

    CT.display.set_font(tt24)
    CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
    CT.display.set_pos(10, 15)
    CT.display.write('IN')

    CT.display.set_color(color565(0, 255, 0), color565(255, 255, 255))
    CT.display.set_pos(30, 15)
    CT.display.write('PASS')

    CT.display.set_font(tt14)
    CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

    # Ja funkcijai tiek padota specifiskas pārbaudes numerācijas indekss.
    if page != 0 and page != "res" and page != "pc":
        CT.display.set_pos(10, 300)
        CT.display.write(str(CT.page)+CT.language_dict[CT.current_language][0]["test_numbering"])

    # Ja funkcijai tiek padots rezultāta vērtība.
    elif page == "res":
        CT.display.set_pos(10, 300)
        CT.display.write(CT.language_dict[CT.current_language][0]["test_results"])

# Tiek konstruktēta "ComponentTests" klase un klasei tiek padota jauna kadra izveides funkcija.
CT = ComponentTests(newFrame)

# Veic pirms pārbaudes UART komunikācijas pārbaudes metode to ComponentTests klases.
check_uart = CT.UartComPreTest()

# Veic pirms pārbaudes EEPROM komponentes pārbaudes metode to ComponentTests klases.
check_eeprom = CT.EepromPreTest()

# Funkcija, kas apstrādā rezultātus un veicina to saglabāšanu ".json" failā.
def TestSuccess():
    string_to_send = ""

    # Pievieno rezultātus pie vērtības, lai tos nosūtītu.
    for val in CT.results_list_to_send:
        string_to_send = string_to_send + val 

    # Noņem pēdējo simbolu no vērtības, korektai datu apstrādes procesam.
    string_to_send = string_to_send.rstrip(string_to_send[-1])

    # Ja pievienota ierīce ir ControlUnit.
    if CT.used_device == "ATmega":

        if CT.i2c_devices[0][2]=="True" and CT.i2c_devices[1][2]=="True":

            if CT.language_dict[CT.current_language][0]["cu_write_ok"] in CT.results_list  and CT.rfid_res==['1.','2.','3.','4.']:

                string_to_send = "cu-true:"+string_to_send

                # Izsauc funkciju, kas saglabā rezultātus ".json" failā.
                AddToHistory(string_to_send)

                return True
            
        string_to_send = "cu-false:"+string_to_send

        AddToHistory(string_to_send)

        return False

    # Ja pievienota ierīce ir TTunit
    elif CT.used_device == "I2C":

        if CT.i2c_devices[0][2]=="True" and CT.i2c_devices[1][2]=="True":
            print("in tt true")
            string_to_send = "tt-true:"+string_to_send

            # Izsauc funkciju, kas saglabā rezultātus ".json" failā.
            AddToHistory(string_to_send)

            return True
        
        string_to_send = "tt-false:"+string_to_send

        AddToHistory(string_to_send)

        return False

# Galvenā funkcija, kas uzsāk programmatūras funkcionējošo darbību.
def scan_i2c():

    devices = CT.i2c.scan()
    x=0

    # Ja tiek atrastas I2C ierīces pievienotam mikročipam.
    if devices:
        newFrame(0)

    #Mikročipa informācijas izvade
        CT.display.set_pos(10, 60)
        CT.display.print(CT.language_dict[CT.current_language][0]["i2c_devices_found"])

        col = 60

        for device in devices:

            CT.display.set_pos(135, col)
            CT.display.print(f"{hex(device)};")

            col = col+15

        # Veic pārbaudi vai pievienots ControlUnit.
        if check_uart is not None and check_uart!=b'\x00':
            
            CT.used_device="ATmega"

            col = col+10

            CT.display.set_pos(10, col)
            CT.display.print(CT.language_dict[CT.current_language][0]["cu_device_found"])

        # Veic pārbaudi vai pievienots TTunit.
        elif check_uart==b'\x00':

            CT.used_device="I2C"

            col = col+10

            CT.display.set_pos(10, col)
            CT.display.print(CT.language_dict[CT.current_language][0]["tt_device_found"])

        utime.sleep(2)

        newFrame(0)
        col = 30

        # Izvada informāciju par pievienoto mikročipu.
        for device in devices:
            x=0
            for hexs, name, status in CT.i2c_devices:

                if hexs == str(device):
                    col+=30

                    CT.display.set_pos(10, col)
                    CT.display.print('* '+name+CT.language_dict[CT.current_language][0]["connected_comp"])

                    CT.i2c_devices[x][2]='True'

                x+=1

        # Ja pievienots ControlUnit mikročips.
        if check_uart is not None and check_uart!=b'\x00':

            col+=30
            CT.display.set_pos(10, col)
            CT.display.print(CT.language_dict[CT.current_language][0]["cu_device_found"])

        utime.sleep(1)

        # Veic pārbaudi vai I2C vērtības sarakstē ir "True".
        for device in CT.i2c_devices:

            if 'True' in device:
                i2c_found = True
                break

        # Ja tiek atrasta vismaz viena I2C ierīce.
        if i2c_found:
                        
                        # Veic Real-Time-Clock pārbaudes funkciju.
                        CT.page = 1
                        CT.RTC_check()

                        # Veic EEPROM pārbaudes funkciju.
                        CT.page=2
                        CT.EEPROM_check()

                        # Pārbauda vai ir pievienots ControlUnit mikročips, lai veiktu atbilstošās pārbaudes priekš ControlUnit.
                        if check_uart is not None and check_uart!=b'\x00':

                            # Veic UART komunikācijas pārbaudes funkciju.
                            CT.page=3
                            CT.ATmega_check()
                            
                            CT.display.set_pos(130, 10)
                            CT.display.set_font(tt14)
                            CT.display.write(CT.language_dict[CT.current_language][0]["press_button_r"])

                            # Ja rīka ierīces poga tiek piespiesta.
                            while True:
                                button_pressed = CT.main_button.value() == 0
                                if button_pressed:
                                    
                                    # Veic ControlUnit releju pārbaudes funkciju.
                                    CT.page = 4
                                    CT.ATmega_relay_check()

                                    # Veic karšu lasītāju pārbaudi uz ControlUnit.
                                    CT.page = 9
                                    CT.RFID_check()

                                    break

                        utime.sleep(0.3)

                        # Pārbauda vai ir pievienots ControlUnit mikročips un izvada informāciju par pārbaudes apstiprināšanu.
                        if check_uart is not None and check_uart !=b'\x00':

                            CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                            CT.display.set_pos(170, 10)
                            CT.display.set_font(tt14)
                            CT.display.write(CT.language_dict[CT.current_language][0]["press_button_o"])

                            CT.display.set_pos(10, 265)
                            CT.display.print(CT.language_dict[CT.current_language][0]["alarm_to_confirm"])

                        # Pārbauda vai ir pievienots TTunit mikročips un izvada informāciju par pārbaudes apstiprināšanu.                        
                        elif check_uart==b'\x00' and device != []:

                            CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                            CT.display.set_pos(170, 10)
                            CT.display.set_font(tt14)
                            CT.display.write(CT.language_dict[CT.current_language][0]["press_button_b"])

                            CT.display.set_pos(10, 265)
                            CT.display.print(CT.language_dict[CT.current_language][0]["buzz_to_confirm"])

        # Ja I2c ierīces netiek atlasītas uz rīka ierīces.
        else:
          
          col = 60
          newFrame(0)

            # Tiek izvadīti neatrasto I2C ierīču adreses un nosaukumi.
          for hexs, names, status in CT.i2c_devices:
            if status=="False":

                CT.display.set_pos(0, col)
                CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))
                CT.display.print('* '+names+CT.language_dict[CT.current_language][0]["not_found"])

                col+=30
    # Ja I2c ierīces netiek atlasītas uz rīka ierīces.          
    else:
        newFrame(0)

        # Izvada informāciju, ka nav atrastas I2C ierīces uz rīka ierīces.
        CT.display.set_pos(10, 60)
        CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))
        CT.display.print(CT.language_dict[CT.current_language][0]["i2c_devices_not_found"])

        # Izvada informāciju, ka iespējamā problēma ir EEPROM komponentei.
        if check_eeprom == False:
            CT.display.set_pos(10, 90)
            CT.display.print(CT.language_dict[CT.current_language][0]["problem_eeprom"])

        CT.used_device = None

        # Tiek palaista funkcija, kas apstrādā saņemtos datus no darbstacijas.
        CT.SendRecieveData()

# Funkcija, kas apstiprina un izvada rezultātus uz displeja.
def TestResults():

    if CT.used_device != None:

        while True:
            if CT.main_button.value() == 0:

                newFrame(0)

                # Pārbauda vai pievienots ControlUnit.
                if check_uart is not None and check_uart!=b'\x00':

                    CT.display.set_pos(10, 60)
                    CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                    CT.display.print(CT.language_dict[CT.current_language][0]["alarming"])

                    print("Buzzing!")

                    # Aktivizē signalazācijas stāvokli uz ControlUnit.
                    CT.M.Queue("SET","alarm_on_state",value=1)
                    CT.M.Send(True)

                    utime.sleep(3)

                    # Deaktivizē signalazācijas stāvokli uz ControlUnit.
                    CT.M.Queue("SET","alarm_on_state",value=0)
                    CT.M.Send(True)
                    
                    break

                # Pārbauda vai pievienots TTunit.
                elif check_uart==b'\x00':

                    CT.display.set_pos(10, 60)
                    CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                    CT.display.print(CT.language_dict[CT.current_language][0]["buzzing"])

                    CT.display.set_pos(170, 10)
                    CT.display.set_font(tt14)

                    print("Buzzing!")


                    # Ieslēdz un izslēdz TTunit zumera komponenti.
                    for x in range(5):
                        CT.TT_buzzer.on()
                        utime.sleep(0.1)

                        CT.TT_buzzer.off()
                        utime.sleep(0.1)
                        
                    break

        while True:     

                # Izveido rezultāta kadru.
                newFrame("res")

                CT.display.set_pos(160, 10)
                CT.display.set_font(tt14)
                CT.display.write(CT.language_dict[CT.current_language][0]["restart_button"])

                # Ar funkcijas palīzdību nosaka vai pārbaude ir veiksmīga.
                if TestSuccess():

                    col = 60

                    # Izriet katram komponenšu pārbaudes rezultātam.
                    for i, stat in enumerate(CT.results_list):
                        i+=1

                        CT.display.set_pos(5, col)
                        CT.display.set_font(tt14)

                        if "ERR" in stat or "ERROR" in stat:
                            CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))

                            print("err")

                        CT.display.write(stat)

                        if (i < 7 and CT.used_device=="ATmega") or CT.used_device=="I2C":

                            CT.display.fill_rectangle(20 , col+15, 200, 2, 000033)

                        col+=25

                        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

                    CT.display.fill_rectangle(0 , 240, 240, 5, 008000)

                    # Izvada uz displeja pārbaudes galējo rezultātu.
                    CT.display.set_pos(30, 250)
                    CT.display.set_font(tt24)
                    CT.display.set_color(color565(0, 255, 0), color565(255, 255, 255))
                    CT.display.write(CT.language_dict[CT.current_language][0]["test_successful"])
                    
                    break

                # Ja pārbaude ir neveiksmīga.
                else:

                    col=60

                    # Izriet katram komponenšu pārbaudes rezultātam.
                    for i, stat in enumerate(CT.results_list):
                        i=i+1

                        CT.display.set_pos(5, col)
                        CT.display.set_font(tt14)

                        if CT.rfid_res != ['1.','2.','3.','4.'] and "readers" in stat:

                            CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))

                        elif ("ERR" in stat or "ERROR" in stat):

                            CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))

                        CT.display.write(stat)

                        if (i < 7 and CT.used_device=="ATmega") or CT.used_device=="I2C":

                            CT.display.fill_rectangle(20 , col+15, 200, 2, 000033)

                        col+=25

                        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

                    CT.display.fill_rectangle(0 , 240, 240, 5, 000030)

                    # Izvada uz displeja pārbaudes galējo rezultātu.
                    CT.display.set_pos(30, 250)
                    CT.display.set_font(tt24)
                    CT.display.set_color(color565(255, 0, 0), color565(255, 255, 255))
                    CT.display.write(CT.language_dict[CT.current_language][0]["test_unsuccessful"])
                    
                    break

# Programmatūras startēšanas kadrs.
newFrame(0)

# Informācijas izvade uz rīka displeja.
CT.display.set_pos(10, 60)
CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
CT.display.print(CT.language_dict[CT.current_language][0]["main_start"])

CT.display.set_pos(170, 10)
CT.display.set_font(tt14)
CT.display.write(CT.language_dict[CT.current_language][0]["press_button"])

# Ja poga tiek piespiesta, tad mikročipu pārbaude sākas.
while True:
    if CT.main_button.value() == 0:
        
        # Funkcija izsaukšana, kas attīra visus iespējamos saglabātos datus uz programmatūras
        CT.ResetForTest()

        # Galvenās pārbaudes funkcijas izsaukšana
        scan_i2c()

        TestResults()
