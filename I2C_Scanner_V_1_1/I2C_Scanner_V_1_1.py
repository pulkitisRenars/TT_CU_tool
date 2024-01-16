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
from ComponentTests import ComponentTests


def newFrame():#Function for a new frame on the LCD display
    device=CT.i2c.scan()

    CT.display.erase()
    CT.display.fill_rectangle(0 , 0, 240, 320, 65535)
    CT.display.fill_rectangle(0 , 0, 240, 50, 008000)
    CT.display.fill_rectangle(0 , 50, 240, 5, 000033)

    if check_uart is not None and device != [] and check_uart != b'\x00':#Checks if there is a ControlUnit connected
        CT.display.set_pos(120, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

        CT.display.write("ControlUnit")

    elif check_uart==b'\x00' and device != []:#Otherwise it shows that there is a TTunit connected
        CT.display.set_pos(165, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

        CT.display.write("TTunit")

    elif device == []:#If there aren't any devices connected to RPi
        CT.display.set_pos(130, 285)
        CT.display.set_font(tt24)
        CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))

        CT.display.write("No device")

    CT.display.fill_rectangle(10 , 16, 85, 30, 111111)
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

    if CT.page != 0 and CT.page != "res":#If there are any test numbers set it sets to needed test number
        CT.display.set_pos(10, 300)
        CT.display.write(str(CT.page)+". test")

    elif CT.page == "res":#If there is given a result signal it will set it as Results on frame
        CT.display.set_pos(10, 300)
        CT.display.write("Results")

CT = ComponentTests(newFrame)

check_uart = CT.UartComPreTest()
check_eeprom = CT.EepromPreTest()
    
def scan_i2c():#The main scanner function
    devices = CT.i2c.scan()
    x=0
    y=60

    if devices:#If there are I2C hardware used
        newFrame(0)
        CT.display.set_pos(10, 60)
        CT.display.print('* I2C devices found:')

        print("Found I2C devices")

        col = 60

        for device in devices:

            CT.display.set_pos(135, col)
            CT.display.print(f"{hex(device)};")

            col = col+15

        if check_uart is not None and check_uart!=b'\x00':#Checks if there is a ControlUnit connected

            CT.used_device="ATmega"#Names the Unit according to the test

            col = col+10

            CT.display.set_pos(10, col)
            CT.display.print('* ControlUnit device found')

            print("Found ControlUnit device")

        elif check_uart==b'\x00':
            CT.used_device="I2C"#Names the Unit according to the test

            col = col+10

            CT.display.set_pos(10, col)
            CT.display.print('* TTunit device found')

            print("Found TTunit device")

        utime.sleep(2)

        newFrame(0)
        col = 30

        for device in devices:#Makes the I2C hardware status true for further results identification
            x=0
            for hexs, name, status in CT.i2c_devices:

                if hexs == str(device):
                    col+=30

                    CT.display.set_pos(10, col)
                    CT.display.print('* '+name+' connected')

                    CT.i2c_devices[x][2]='True'

                x+=1

        if check_uart is not None and check_uart!=b'\x00':#Checks if there is a ControlUnit connected

            col+=30
            CT.display.set_pos(10, col)
            CT.display.print('* ControlUnit connected')

        print(str(x)+" I2C devices were found")

        utime.sleep(1)

        for device in CT.i2c_devices:
            if 'True' in device:#Checks if the device has a "True" value
                i2c_found = True

                break
        if i2c_found:#If there is at least one "True"  
                          
                        CT.page = 1
                        CT.RTC_check()#Runs the RTC_check function, y is used for the storing of the display location

                        CT.page=2
                        CT.EEPROM_check()#Runs the EEPROM_check function, y is used for the storing of the display location

                        if check_uart is not None and check_uart!=b'\x00':#Checks if there is a ControlUnit connected

                            CT.page=3
                            CT.ATmega_check()#Runs the ATmega_check function, y is used for the storing of the display location

                            while True:
                                button_pressed = CT.button.value() == 0  # Check if the button is pressed
                                if button_pressed:

                                    CT.page = 4
                                    CT.ATmega_relay_check()

                                    CT.page = 9
                                    CT.RFID_check()

                                    break


                        utime.sleep(0.3)
                        if check_uart is not None and check_uart!=b'\x00':

                            CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                            CT.display.set_pos(170, 10)
                            CT.display.set_font(tt14)
                            CT.display.write("ON---------->")

                            CT.display.set_pos(10, 265)
                            CT.display.print('Alarm to confirm scan results')

                        elif check_uart==b'\x00' and device != []:

                            CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                            CT.display.set_pos(170, 10)
                            CT.display.set_font(tt14)
                            CT.display.write("Buzz------>")

                            CT.display.set_pos(10, 265)
                            CT.display.print('Buzz to confirm scan results')

                    
        else:#If there isn't any "True" found
          
          col = 60
          newFrame(0)

          for hexs, names, status in CT.i2c_devices:
            if status=="False":#Checks the I2C hardware for "False" values

                CT.display.set_pos(0, col)
                CT.display.set_color(color565(0, 0, 255), color565(255, 255, 255))
                CT.display.print('* '+names+' not found.')

                print("The scanner didn't find "+names+" device")

                col+=30
           
    else:#If there aren't any I2C hardware found
        newFrame(0)

        print(devices)

        CT.display.set_pos(10, 60)
        CT.display.set_color(color565(0, 0, 255), color565(255, 255, 255))
        CT.display.print('* I2C devices not found.')

        print("There weren't any I2C devices found")

        if check_eeprom == False:
            CT.display.set_pos(10, 90)
            CT.display.print('* Likely a problem with EEPROM.')

        CT.used_device = None
        
def scannerRestart(btn_count):#Function that lets the user restart scanner functions
   global mDevice, RFID_res
   if mDevice!=None:
    while True:#Meant for pressing a button
     if button.value() == 0:
      for i in range(2):
        btn_count += 1
        if btn_count ==1:#If the button is pressed one time goes through a buzzer test
            newFrame(0)
            if check_uart is not None and check_uart!=b'\x00':#If a ControlUnit is connected
                CT.display.set_pos(10, 60)
                CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                CT.display.print("Alarming")
                print("Buzzing!")
                M.Queue("SET","alarm_on_state",value=1)
                M.Send(True)
                utime.sleep(3)
                M.Queue("SET","alarm_on_state",value=0)
                M.Send(True)
            elif check_uart==b'\x00':#If a TTunit is connected
                CT.display.set_pos(10, 60)
                CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                CT.display.print("Buzzing")
                CT.display.set_pos(170, 10)
                CT.display.set_font(tt14)
                print("Buzzing!")
                for x in range(5):
                    buzzer.on()
                    utime.sleep(0.1)
                    buzzer.off()
                    utime.sleep(0.1)
        elif btn_count==2:#If button is pressed two times shows results and lets the user restart the main scanner function
            newFrame("res")
            CT.display.set_pos(160, 10)
            CT.display.set_font(tt14)
            CT.display.write("RESTART---->")
            if (i2c_devices[0][2]=="True" and i2c_devices[1][2]=="True" and atmega_found==True and mDevice=="ATmega" and RFID_res==['1.','2.','3.','4.']) or (i2c_devices[0][2]=="True" and i2c_devices[1][2]=="True" and mDevice=="I2C"):
                #Checks the status of all of the hardware, if every hardware is found and tested successfully
                k=60
                i=0
                for stat in statusArr:
                    i=i+1
                    CT.display.set_pos(5, k)
                    CT.display.set_font(tt14)
                    if "ERR" in stat or "ERROR" in stat:
                        CT.display.set_color(color565(0, 0, 255), color565(255, 255, 255))
                        print("err")
                    CT.display.write(stat)
                    if (i < 7 and mDevice=="ATmega") or mDevice=="I2C":
                        CT.display.fill_rectangle(20 , k+15, 200, 2, 000033)
                    k=k+25
                    CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                CT.display.fill_rectangle(0 , 240, 240, 5, 008000)
                CT.display.set_pos(30, 250)
                CT.display.set_font(tt24)
                CT.display.set_color(color565(0, 255, 0), color565(255, 255, 255))
                CT.display.write("Test successful!")
                print("The I2C scanner test was successful!")
            else:#If the hardware status isn't successful
                k=60
                i=0
                for stat in statusArr:
                    i=i+1
                    CT.display.set_pos(5, k)
                    CT.display.set_font(tt14)
                    if RFID_res != ['1.','2.','3.','4.'] and "readers" in stat:
                        CT.display.set_color(color565(0, 0, 255), color565(255, 255, 255))
                    if ("ERR" in stat or "ERROR" in stat):
                        CT.display.set_color(color565(0, 0, 255), color565(255, 255, 255))
                    CT.display.write(stat)
                    if (i < 7 and mDevice=="ATmega") or mDevice=="I2C":
                        CT.display.fill_rectangle(20 , k+15, 200, 2, 000033)
                    k=k+25
                    CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
                CT.display.set_pos(30, 250)
                CT.display.fill_rectangle(0 , 240, 240, 5, 000030)
                CT.display.set_font(tt24)
                CT.display.set_color(color565(0, 0, 255), color565(255, 255, 255))
                CT.display.write("Test unsuccessful!")
                print("The I2C scanner test was unsuccessful!")
            return btn_count
   elif mDevice==None:#If there isn't any device connected
       btn_count=0
       return btn_count
    
newFrame(0)#The first starting frame
print("Starting program")
CT.display.set_pos(10, 60)
CT.display.set_color(color565(0, 0, 0), color565(255, 255, 255))
CT.display.print("* To Start press button")
CT.display.set_pos(170, 10)
CT.display.set_font(tt14)
CT.display.write("PRESS---->")
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
