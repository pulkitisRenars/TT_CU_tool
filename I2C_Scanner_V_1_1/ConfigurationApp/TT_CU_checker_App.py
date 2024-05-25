# -*- coding: utf-8 -*-
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image  
import json

from serial import Serial, PARITY_EVEN, STOPBITS_ONE
import time

def center(win):
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()

def SendToDevice(device_port,type):

    type = type+"\r"

    try:
        s = Serial(port=device_port, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=1)
        s.flush()

        s.write(type.encode())

        mes = s.read_until().strip()

        if mes == b'':
            return False
        else:
            return mes
            
    except Exception:
        return False

def ParseHistoryData(data):

    history_array = {
            "ttunit": {},
            "controlunit": {}
            }
    
    tt_count = 0
    cu_count = 0

    for data_item in data:
            
            if data_item[0:2] == "tt":
                tt_count+=1

            elif data_item[0:2] == "cu":
                cu_count+=1

    for i in range(tt_count):
        history_array["ttunit"][i] = {}

    for i in range(cu_count):
        history_array["controlunit"][i] = {}
    
    for i, data_item in enumerate(data):

        split_data = data_item.split(":")

        if data_item[0:2] == "tt":

            for item in split_data:
                key, value = item.split('-')

                for i in range(tt_count):

                    if len(history_array["ttunit"][i]) < 3:

                        if key not in history_array["ttunit"][i]:

                            history_array["ttunit"][i][key] = value
                            break

        elif data_item[0:2] == "cu":

            for item in split_data:

                key, value = item.split('-')

                for i in range(cu_count):

                    if len(history_array["controlunit"][i]) < 8:
                        history_array["controlunit"][i][key] = value
                        break

    return history_array

class ConfigTTCUChecker:
    global center

    def __init__(self):

        self.language = {}
        self.GetConf()
    
        self.root =  Tk()
        self.root.option_add('*Font', 'Arial 12')
        self.root.option_add('*TkDefaultFont', 'Arial 12')
        self.root.option_add('*Dialog.msg.font', 'Arial 12')

        self.root.resizable(0, 0)
        self.root.minsize(1280, 720) # Pievieno minimālās un maksimālās vērtības logam
        self.root.maxsize(1920, 1080)
        self.root.geometry('1280x720')
        self.root.configure(bg="#fff")
        
        self.device_port_value = ""
        self.device_connected = False
        self.tt_cu_history = {}

        self.language_option_val = StringVar(self.root)

        center(self.root)# Funkcijas palaišana, lai iecentrētu programmatūru ekrāna vidū

        self.current_language = "english"

    def GetConf(self):
                # Load the JSON data from file
        with open('I2C_Scanner_V_1_1\ConfigurationApp\conf.json', encoding='utf-8') as f:
            self.language = json.load(f)

    def ChangeLanguageHandler(self):

        if self.current_language == "english":
            self.current_language = "latvian"

        elif self.current_language == "latvian":
            self.current_language = "english"

        self.navbar.destroy()
        self.content_box.destroy()
        self.CreateWindow()

    def DeleteHistoryHandler(self):
        if self.device_connected:
            if SendToDevice(self.device_port_value, "delete") == b'deleted':
                messagebox.showwarning(self.language[self.current_language][0]["deleted_history_title"], self.language[self.current_language][0]["deleted_history_message"])
                self.CheckDevice()

    def ConfigureHandler(self):
        if self.device_connected:
            if self.language_option_val.get() == "Latvian" or self.language_option_val.get() == "Latviešu":
                res = SendToDevice(self.device_port_value, "lat")

            elif self.language_option_val.get() == "English" or self.language_option_val.get() == "Angļu":
                res = SendToDevice(self.device_port_value, "eng")

            if res == b'lat_configured' or res == b'eng_configured':
                messagebox.showwarning("Warning!", self.language[self.current_language][0]["changed_language_message"]+self.language_option_val.get())
                self.CheckDevice()

    def CheckDevice(self):
        serial_init = True
        if self.device_connected == False:
            self.device_port_value = self.device_port.get()

        if self.device_port_value.isdigit() and 1 <= int(self.device_port_value) <= 256:
            self.device_port_value = "COM" + self.device_port_value

        elif self.device_port_value.startswith("COM") and self.device_port_value[3:].isdigit() and 1 <= int(self.device_port_value[3:]) <= 256:
            pass  # Value is already in the correct format

        elif self.device_port_value.startswith("com") and self.device_port_value[3:].isdigit() and 1 <= int(self.device_port_value[3:]) <= 256:
            self.device_port_value = "COM" + self.device_port_value[3:].upper()
            
        else:
            messagebox.showerror("Error", self.language[self.current_language][0]["incorrect_com"])
            serial_init = False

            return

        history_data = []

        if SendToDevice(self.device_port_value, "receive") == b'transfer':
            self.device_connected = True

        if self.device_connected:
            
            try:
                ser = Serial(self.device_port_value, 9600)
            except Exception as e:
                serial_init = False

            if serial_init:

                try:
                    while True:

                        data = ser.readline().strip()  # Remove leading/trailing whitespace and newline characters

                        if data:
                            data_str = data.decode()  # Decode bytes to string

                            if "END" not in data_str:
                                if "eng" in data_str:
                                    self.language_option_val.set(self.language[self.current_language][0]["configure_english_language"])

                                elif "lat" in data_str:
                                    self.language_option_val.set(self.language[self.current_language][0]["configure_latvian_language"])

                                history_data.append(data_str)

                            else:
                                break

                        time.sleep(0.01)

                except Exception:
                    serial_init = False
                
                if serial_init and history_data != []:

                    try:
                        self.tt_cu_history = ParseHistoryData(history_data)

                        self.device_failed_label.place_forget()

                        self.device_connected_label.place_forget()
                        self.device_connected_label.config(text = self.language[self.current_language][0]["device_connected"]+": "+self.device_port_value)
                        self.device_connected_label.place(x=1050, y=110)

                    except:

                        self.device_connected_label.place_forget()

                        self.device_failed_label.place(x=1050, y=110)

                else:

                    self.device_connected_label.place_forget()

                    self.device_failed_label.place(x=1050, y=110)

                if self.clicked_history:
                    self.LoadHistory()

                elif self.clicked_config:
                    self.LoadConfigure()

        else:
            self.device_connected_label.place_forget()

            self.device_failed_label.place(x=1050, y=110)

            messagebox.showerror("Error", self.language[self.current_language][0]["no_connection"])
            

    def CreateWindow(self):

        self.clicked_history = False
        self.clicked_config = False

        self.root.title(self.language[self.current_language][0]["title"])

        self.content_box = Frame(self.root, width=1300, height=600, bg="#fff")

        image = Image.open("I2C_Scanner_V_1_1\ConfigurationApp\images\otradi copy.tif")
        image = image.resize((800, 400))

        self.image = ImageTk.PhotoImage(image)
        self.home_image = Label(self.content_box, image=self.image, width=800, height=500, anchor=CENTER, bg="#fff")
        self.home_image.image = self.image

        self.home_image.pack()

        self.history_box = Frame()
        self.configure_box = Frame()

        self.CreateNavbar()

        if self.device_connected:
            self.device_connected_label.place(x=1050, y=110)
        else:
            self.device_failed_label.place(x=1050, y=110)

        self.content_box.pack(side=BOTTOM)

        self.root.mainloop()

    def CreateNavbar(self):
        self.navbar = Frame(self.root, bg="green", height="150", width="2000")
        Frame(self.navbar, width="155", height="50", bg="#000").place(x="35", y="45")
        logo_frame = Frame(self.navbar, width="155", height="50")
        Label(logo_frame, fg="black", font=('MS Sans Serif', 28, 'bold'), text="IN").place(x="5", y="0")
        Label(logo_frame, fg="green", font=('MS Sans Serif', 28, 'bold'), text="PASS").place(x="45", y="0")
        logo_frame.place(x="30", y="40")

        self.history_button = Button(self.navbar, text=self.language[self.current_language][0]["history"], font=('MS Sans Serif', 16, 'bold'), padx=5, pady=5, command=self.LoadHistory, highlightbackground="black").place(x=350, y=45)

        self.configure_button = Button(self.navbar, text=self.language[self.current_language][0]["configure"], font=('MS Sans Serif', 16, 'bold'), padx=5, pady=5, command=self.LoadConfigure).place(x=550, y=45)

        self.language_button = Button(self.navbar, text=self.language[self.current_language][0]["language"], font=('MS Sans Serif', 16, 'bold'), padx=5, pady=5, command= self.ChangeLanguageHandler).place(x=1150, y=45)

        self.check_device = Button(self.navbar, text=self.language[self.current_language][0]["check_device"], font=('MS Sans Serif', 16, 'bold'), padx=5, pady=5, command= self.CheckDevice).place(x=900, y=45)

        self.device_failed_label = Label(self.navbar, text = self.language[self.current_language][0]["failed_device_connection"], font=('MS Sans Serif', 12, 'bold'), bg="white", fg="red")
        self.device_connected_label = Label(self.navbar, text = self.language[self.current_language][0]["device_connected"]+": "+self.device_port_value, font=('MS Sans Serif', 12, 'bold'), bg="white", fg="green")


        Label(self.navbar, text = self.language[self.current_language][0]["device_com_port"], font=('MS Sans Serif', 12, 'bold'), bg="green").place(x=800, y=110)

        self.device_port = Entry(self.navbar, width="10")
        self.device_port.place(x=950, y= 110)

        self.navbar.pack(side=TOP)

    def LoadHistory(self):
        
        self.clicked_history = True
        self.clicked_config = False

        self.configure_box.pack_forget()  
        self.configure_box.destroy()
        self.history_box.destroy()
        if hasattr(self, 'home_image') and self.home_image:
            self.home_image.destroy()
        else:
            self.CreateWindow()
        
        self.history_box = Frame(self.content_box, width=1300, height=600, bg="#fff")

        self.ttunit_box = Frame(self.history_box, width=600, height=500, bd=2, relief=SOLID, bg="#fff")
        Label(self.history_box, text=self.language[self.current_language][0]["history_tt_label"], font= ('MS Sans Serif', 16, 'bold'), bg="#fff").place(x=25, y=10)
        self.ttunit_box.place(x=20, y=50)

        self.controlunit_box = Frame(self.history_box, width=625, height=500, bd=2, relief=SOLID, bg="#fff")
        Label(self.history_box, text=self.language[self.current_language][0]["history_cu_label"], font=('MS Sans Serif', 16, 'bold'), bg="#fff").place(x=455, y=10)
        self.controlunit_box.place(x=450, y=50)

        Button(self.history_box, text=self.language[self.current_language][0]["history_delete_button"], command= self.DeleteHistoryHandler, bg="#fff").place(x=1110, y=25)

        headers = ["N.", "Status", "EEPROM", "RTC"]
        for i in range(4):
            Label(self.ttunit_box, text=headers[i], highlightbackground="black", highlightcolor="black", highlightthickness=1, width=10, bg="green").grid(row=0, column=i)

        if self.device_connected:
            row = 1
            for key, value in self.tt_cu_history['ttunit'].items():

                text_array = []

                key_list = value.keys()

                if "tt" in key_list:
                    if value["tt"] == 'true':
                        text_array.append("✔")
                    elif value["tt"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-")


                if "ee" in key_list:
                    if value["ee"] == 'true':
                        text_array.append("✔")
                    elif value["ee"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-")
              
                if "rtc" in key_list:  
                    if value["rtc"] == 'true':
                        text_array.append("✔")
                    elif value["rtc"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-")   

                Label(self.ttunit_box, text=str(row)+".", highlightbackground="black", highlightcolor="black", highlightthickness=1, width=10, bg="#fff").grid(row=row, column=0)
                column = 1
                for row_label in text_array:
                    Label(self.ttunit_box, text=row_label, highlightbackground="black", highlightcolor="black", highlightthickness=1, width=10, bg="#fff").grid(row=row, column=column)
                    column = column + 1
                row += 1


        headers = ["N.", "Status", "EEPROM", "RTC", "UART", "1. Wieg", "2. Wieg", "3. Wieg", "4. Wieg"]
        for i in range(9):
            Label(self.controlunit_box, text=headers[i], highlightbackground="black", highlightcolor="black", highlightthickness=1, width=7, bg="green").grid(row=0, column=i)


        if self.device_connected:
            row = 1

            for key, value in self.tt_cu_history['controlunit'].items():

                key_list = value.keys()

                text_array = []

                if "cu" in key_list:
                    if value["cu"] == 'true':
                        text_array.append("✔")
                    elif value["cu"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-")

                if "ee" in key_list:
                    if value["ee"] == 'true':
                        text_array.append("✔")
                    elif value["ee"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-")
                
                if "rtc" in key_list:                
                    if value["rtc"] == 'true':
                        text_array.append("✔")
                    elif value["rtc"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-") 

                if "com" in key_list:
                    if value["com"] == 'true':
                        text_array.append("✔")
                    elif value["com"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-")

                if "w1" in key_list:
                    if value["w1"] == 'true':
                        text_array.append("✔")
                    elif value["w1"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-")

                if "w2" in key_list:
                    if value["w2"] == 'true':
                        text_array.append("✔")
                    elif value["w2"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-") 

                if "w3" in key_list:
                    if value["w3"] == 'true':
                        text_array.append("✔")
                    elif value["w3"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-")

                if "w4" in key_list:
                    if value["w4"] == 'true':
                        text_array.append("✔")
                    elif value["w4"] == 'false':
                        text_array.append("X")
                else:
                    text_array.append("-")        

                Label(self.controlunit_box, text=str(row)+".", highlightbackground="black", highlightcolor="black", highlightthickness=1, width=7, bg="#fff").grid(row=row, column=0)

                column = 1

                for row_label in text_array:
                    Label(self.controlunit_box, text=row_label, highlightbackground="black", highlightcolor="black", highlightthickness=1, width=7, bg="#fff").grid(row=row, column=column)
                    column = column + 1
                
                row += 1

        self.history_box.pack()


    def LoadConfigure(self):

        self.clicked_history = False
        self.clicked_config = True

        self.configure_box.pack_forget()  
        self.configure_box.destroy()
        self.history_box.destroy()

        if hasattr(self, 'home_image') and self.home_image:
            self.home_image.destroy()
        else:
            self.CreateWindow()

        self.configure_box = Frame(self.content_box, width=1300, height=600, bg="#fff")
        self.configure_box.pack()

        Label(self.configure_box, text=self.language[self.current_language][0]["configure_label"], font=('MS Sans Serif', 18, 'bold'), bg="#fff").place(x=20, y= 20)

        Label(self.configure_box, text=self.language[self.current_language][0]["configure_language"], font=('MS Sans Serif', 14), bg="#fff").place(x=35, y= 100)

        if self.device_connected:
            Label(self.configure_box, text=self.language[self.current_language][0]["current_language"]+self.language_option_val.get(), font=('MS Sans Serif', 14), bg="#fff").place(x=900, y= 70)

        self.configure_option_menu = OptionMenu(self.configure_box, self.language_option_val, self.language[self.current_language][0]["configure_english_language"], self.language[self.current_language][0]["configure_latvian_language"])

        self.configure_option_menu.place(x=400, y=100)

        Button(self.configure_box, command=self.ConfigureHandler, text=self.language[self.current_language][0]["submit_button"], font=('MS Sans Serif', 16, 'bold'),  padx=5, pady=5).place(x=1100, y=500)


Window = ConfigTTCUChecker()
Window.CreateWindow()