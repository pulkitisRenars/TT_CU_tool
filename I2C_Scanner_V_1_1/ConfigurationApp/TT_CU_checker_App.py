# -*- coding: utf-8 -*-
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image  
import json
from os import path
import asyncio

from serial import Serial, PARITY_EVEN, STOPBITS_ONE
import time

# Funkcija, kas iecentrē aplikācijas logu.
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

# Funkcija, kas nosūta specifisku ziņu uz ierīci caur seriālo komunikāciju.
def SendToDevice(device_port,type):

    type = type+"\r"

    # Veic seriālo komunikāciju ar ierīci.
    try:
        s = Serial(port=device_port, parity=PARITY_EVEN, stopbits=STOPBITS_ONE, timeout=1)
        s.flush()

        # Nosūta ziņu.
        s.write(type.encode())

        # Nolasa atbildi.
        mes = s.read_until().strip()

        # Ja atbilde nav tukša tad ziņa tiek padota tālāk.
        if mes == b'':
            return False
        else:
            return mes
            
    except Exception:
        return False

# Funkcija, kas apstrādā saņemtos datus no rīka.
def ParseHistoryData(data):

    history_array = {
            "ttunit": {},
            "controlunit": {}
            }
    
    tt_count = 0
    cu_count = 0

    # Saskaita cik rezultātu ir par TTunit un par ControlUnit.
    for data_item in data:
            
            if data_item[0:2] == "tt":
                tt_count+=1

            elif data_item[0:2] == "cu":
                cu_count+=1

    # Par katru saskaitīto mikročipu rezultātu elementa pievieno tukšu datni.
    for i in range(tt_count):
        history_array["ttunit"][i] = {}

    for i in range(cu_count):
        history_array["controlunit"][i] = {}
    
    # Apstrādā saņemtos datus un tos ievieto datnē.
    for i, data_item in enumerate(data):

        split_data = data_item.split(":")

        # Ja elements ir TTunit.
        if data_item[0:2] == "tt":

            for item in split_data:
                key, value = item.split('-')

                for i in range(tt_count):

                    if len(history_array["ttunit"][i]) < 3:

                        if key not in history_array["ttunit"][i]:
                            
                            # Ievieto datnē rezultātu
                            history_array["ttunit"][i][key] = value
                            break
        # Ja elements ir ControlUnit.
        elif data_item[0:2] == "cu":

            for item in split_data:

                key, value = item.split('-')

                for i in range(cu_count):

                    if len(history_array["controlunit"][i]) < 8:

                        # Ievieto datnē rezultātu
                        history_array["controlunit"][i][key] = value
                        break

    return history_array

class ConfigTTCUChecker:
    global center

    # Konstruktors, kas izveido aplikacijas logu.
    def __init__(self):

        self.language = {}

        # Ielādē aplikācijas saskarnes vārdnīcu.
        self.GetConf()
    
        self.root =  Tk()
        self.root.option_add('*Font', 'Arial 12')
        self.root.option_add('*TkDefaultFont', 'Arial 12')
        self.root.option_add('*Dialog.msg.font', 'Arial 12')

        self.root.resizable(0, 0)
        self.root.minsize(1280, 720) # Pievieno minimālās un maksimālās vērtības logam.
        self.root.maxsize(1920, 1080)
        self.root.geometry('1280x720')
        self.root.configure(bg="#fff")
        
        self.device_port_value = ""
        self.device_connected = False
        self.tt_cu_history = {}

        self.language_option_val = StringVar(self.root)

        center(self.root)# Funkcijas palaišana, lai iecentrētu programmatūru ekrāna vidū.

        self.current_language = "english"

    # Funkcija, kas ielādē aplikācijas saskarnes vārdnīcu.
    def GetConf(self):
        with open(path.abspath(path.join(path.dirname(__file__), 'conf.json')), encoding='utf-8') as f:
            self.language = json.load(f)

    # Funkcija, kas pārmaina aplikācijas saskarnes valodu un to ielādē aplikācijas logā.
    def ChangeLanguageHandler(self):

        if self.current_language == "english":
            self.current_language = "latvian"

        elif self.current_language == "latvian":
            self.current_language = "english"

        self.navbar.destroy()
        self.content_box.destroy()
        self.CreateWindow()

    # Funkcija, kas veic rīka pārbaudes rezultātu izdzēšanu.
    def DeleteHistoryHandler(self):
        if self.device_connected:
            if SendToDevice(self.device_port_value, "delete") == b'deleted':

                # Izvada atsevišķu logu, kas signalizē par datu izdzēšanu.
                messagebox.showwarning(self.language[self.current_language][0]["deleted_history_title"], self.language[self.current_language][0]["deleted_history_message"])

                # No jauna iegūst ierīces datus. 
                self.CheckDevice()

    # Funkcija, kas veic rīka valodas saskarnes maiņu.
    def ConfigureHandler(self):
        if self.device_connected:
            if self.language_option_val.get() == "Latvian" or self.language_option_val.get() == "Latviešu":
                res = SendToDevice(self.device_port_value, "lat")

            elif self.language_option_val.get() == "English" or self.language_option_val.get() == "Angļu":
                res = SendToDevice(self.device_port_value, "eng")

            if res == b'lat_configured' or res == b'eng_configured':
                messagebox.showwarning("Warning!", self.language[self.current_language][0]["changed_language_message"]+self.language_option_val.get())
                self.CheckDevice()

    # Funkcija, kas izveido savienojumu ar rīku, nolasot nosūtītos datus un tos apstrādājot.
    def CheckDevice(self):

        serial_init = True

        # Veic seriālās komunikācijas numura ievades validāciju.
        if self.device_connected == False:
            self.device_port_value = self.device_port.get()

        if self.device_port_value.isdigit() and 1 <= int(self.device_port_value) <= 256:
            self.device_port_value = "COM" + self.device_port_value

        elif self.device_port_value.startswith("COM") and self.device_port_value[3:].isdigit() and 1 <= int(self.device_port_value[3:]) <= 256:
            pass  # Value is already in the correct format

        elif self.device_port_value.startswith("com") and self.device_port_value[3:].isdigit() and 1 <= int(self.device_port_value[3:]) <= 256:
            self.device_port_value = "COM" + self.device_port_value[3:].upper()
            
        else:
            # Uz atsevišķa loga izvada, ka nav veiksmīgs savienojums.
            messagebox.showerror("Error", self.language[self.current_language][0]["incorrect_com"])
            serial_init = False

            return

        history_data = []

        # Nosūta rīkam apstiprinājumu par datu nepieciešamību un ja tas ir korekts, tad process turpinas.
        if SendToDevice(self.device_port_value, "receive") == b'transfer':
            self.device_connected = True

        if self.device_connected:
            
            try:
                ser = Serial(self.device_port_value, 9600)
            except Exception as e:
                serial_init = False

            if serial_init:

                try:
                    # Veic datu nolasīšanu un to saglabāšanu, apstrādāšanu
                    while True:

                        data = ser.readline().strip()

                        if data:
                            data_str = data.decode()
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
                
                # Veic datu apstrādi un paziņošanu, ka ierīce veiksmīgi savienota un nolasīta.
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

                # Ja iepriekš aplikācija bijusi vēstures sadaļā, tad to ielādē vēlreiz ar jauniem datiem.
                if self.clicked_history:
                    self.LoadHistory()

                # Ja iepriekš aplikācija bijusi konfigurācijas sadaļā, tad to ielādē vēlreiz ar jauniem datiem.
                elif self.clicked_config:
                    self.LoadConfigure()

        else:
            self.device_connected_label.place_forget()

            self.device_failed_label.place(x=1050, y=110)

            # Uz atsevišķa loga izvada, ka nav veiksmīgs savienojums.
            messagebox.showerror("Error", self.language[self.current_language][0]["no_connection"])
            
    #Funkcija, kas izveido aplikācijas logu un tā saturu.
    def CreateWindow(self):

        self.clicked_history = False
        self.clicked_config = False

        self.root.title(self.language[self.current_language][0]["title"])

        self.content_box = Frame(self.root, width=1300, height=600, bg="#fff")

        # Ievieto bildi sākuma lapā.
        image = Image.open(path.abspath(path.join(path.dirname(__file__), "images\otradi copy.tif")))
        image = image.resize((800, 400))

        self.image = ImageTk.PhotoImage(image)
        self.home_image = Label(self.content_box, image=self.image, width=800, height=500, anchor=CENTER, bg="#fff")
        self.home_image.image = self.image

        self.home_image.pack()

        self.history_box = Frame()
        self.configure_box = Frame()

        # Izveido navigācijas joslu.
        self.CreateNavbar()

        if self.device_connected:
            self.device_connected_label.place(x=1050, y=110)
        else:
            self.device_failed_label.place(x=1050, y=110)

        self.content_box.pack(side=BOTTOM)

    #Funkcija, kas izveido navigācijas joslu.
    def CreateNavbar(self):
        self.navbar = Frame(self.root, bg="green", height="150", width="2000")
        # Izveido logo uz navigācijas joslas
        Frame(self.navbar, width="155", height="50", bg="#000").place(x="35", y="45")
        logo_frame = Frame(self.navbar, width="155", height="50")
        Label(logo_frame, fg="black", font=('MS Sans Serif', 28, 'bold'), text="IN").place(x="5", y="0")
        Label(logo_frame, fg="green", font=('MS Sans Serif', 28, 'bold'), text="PASS").place(x="45", y="0")
        logo_frame.place(x="30", y="40")

        # Izvieto dažādas pogas un ievades laukus uz navigācijas joslas.
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

    # Funkcija, kas ielādē vēstures sadaļas rāmi uz aplikācijas loga.
    def LoadHistory(self):
        
        self.clicked_history = True
        self.clicked_config = False

        # Iznīcina nevajadzīgos rāmjus no loga.
        self.configure_box.pack_forget()  
        self.configure_box.destroy()
        self.history_box.destroy()
        if hasattr(self, 'home_image') and self.home_image:
            self.home_image.destroy()
        else:
            self.CreateWindow()
        
        # Izveido attiecošos elementus uz rāmja.
        self.history_box = Frame(self.content_box, width=1300, height=600, bg="#fff")

        self.ttunit_box = Frame(self.history_box, width=600, height=500, bd=2, relief=SOLID, bg="#fff")
        Label(self.history_box, text=self.language[self.current_language][0]["history_tt_label"], font= ('MS Sans Serif', 16, 'bold'), bg="#fff").place(x=25, y=10)
        self.ttunit_box.place(x=20, y=50)

        self.controlunit_box = Frame(self.history_box, width=625, height=500, bd=2, relief=SOLID, bg="#fff")
        Label(self.history_box, text=self.language[self.current_language][0]["history_cu_label"], font=('MS Sans Serif', 16, 'bold'), bg="#fff").place(x=455, y=10)
        self.controlunit_box.place(x=450, y=50)

        Button(self.history_box, text=self.language[self.current_language][0]["history_delete_button"], command= self.DeleteHistoryHandler, bg="#fff").place(x=1110, y=25)

        # Izveido TTunit tabulas galvenes.
        headers = ["N.", "Status", "EEPROM", "RTC"]
        for i in range(4):
            Label(self.ttunit_box, text=headers[i], highlightbackground="black", highlightcolor="black", highlightthickness=1, width=10, bg="green").grid(row=0, column=i)

        # Ja ierīce pievienota un saņemti dati, tad tos apstrādā un izvieto tabulā.
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

        # Izveido ControlUnit tabulas galvenes.
        headers = ["N.", "Status", "EEPROM", "RTC", "UART", "1. Wieg", "2. Wieg", "3. Wieg", "4. Wieg"]
        for i in range(9):
            Label(self.controlunit_box, text=headers[i], highlightbackground="black", highlightcolor="black", highlightthickness=1, width=7, bg="green").grid(row=0, column=i)

        # Ja ierīce pievienota un saņemti dati, tad tos apstrādā un izvieto tabulā.
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

    # Funkcija, kas ielādē rīka konfigurācijas rāmi uz aplikācijas loga.
    def LoadConfigure(self):

        self.clicked_history = False
        self.clicked_config = True

        # Iznīcina nevajadzīgos rāmjus no loga.
        self.configure_box.pack_forget()  
        self.configure_box.destroy()
        self.history_box.destroy()

        if hasattr(self, 'home_image') and self.home_image:
            self.home_image.destroy()
        else:
            self.CreateWindow()

        # Izveido attiecošos elementus uz rāmja.
        self.configure_box = Frame(self.content_box, width=1300, height=600, bg="#fff")
        self.configure_box.pack()

        Label(self.configure_box, text=self.language[self.current_language][0]["configure_label"], font=('MS Sans Serif', 18, 'bold'), bg="#fff").place(x=20, y= 20)

        Label(self.configure_box, text=self.language[self.current_language][0]["configure_language"], font=('MS Sans Serif', 14), bg="#fff").place(x=35, y= 100)

        # Ja rīks savienots, tad tiek izvadīta izmantotā valoda uz rīka saskarnes.
        if self.device_connected:
            Label(self.configure_box, text=self.language[self.current_language][0]["current_language"]+self.language_option_val.get(), font=('MS Sans Serif', 14), bg="#fff").place(x=900, y= 70)

        self.configure_option_menu = OptionMenu(self.configure_box, self.language_option_val, self.language[self.current_language][0]["configure_english_language"], self.language[self.current_language][0]["configure_latvian_language"])

        self.configure_option_menu.place(x=400, y=100)

        Button(self.configure_box, command=self.ConfigureHandler, text=self.language[self.current_language][0]["submit_button"], font=('MS Sans Serif', 16, 'bold'),  padx=5, pady=5).place(x=1100, y=500)

started = False
Window = ConfigTTCUChecker()

# Galvenā funkcija, kas tiek palaista, lai visi procesi funkcionētos asinhroni.
async def main():
    started = False

    # Atjauno Tkinter loga informāciju.
    async def RunTkinter():
        while True:
            Window.root.update()
            await asyncio.sleep(0.01)

    # Funkcija, kas pārbauda vai rīks ir savienots ar darbstaciju asinhroni.
    async def CheckConnectedDevice():
        ser = Serial()
        while True:

            # Process turpinas, ja rīks ir iepriekš izveidots.
            if Window.device_connected is not False:

                check = True

                try:
                    ser = Serial(Window.device_port_value, 9600)
                except Exception as e:
                    check = False

                if check is False:
                    Window.device_connected_label.place_forget()

                    Window.device_failed_label.place(x=1050, y=110)

                    Window.device_connected = False


                ser.close()
                await asyncio.sleep(4)
            else:
                await asyncio.sleep(1)
    
    while not started:
        Window.CreateWindow()
        started = True

    # Ievieto divas asinhronās funkcijas, asyncio funkciju palaišanai.
    await asyncio.gather(RunTkinter(), CheckConnectedDevice())

# Tiek palaists viss process.
asyncio.run(main())