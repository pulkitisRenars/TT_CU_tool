# -*- coding: utf-8 -*-
from tkinter import *
from PIL import ImageTk, Image  
import json

from serial import Serial

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

class ConfigTTCUChecker:
    global center

    def __init__(self):

        self.language = {}
        self.GetConf()
    
        self.root =  Tk()
        self.root.option_add('*Font', 'Arial 12')  # Change font if necessary
        self.root.option_add('*TkDefaultFont', 'Arial 12')  # Change font if necessary
        self.root.option_add('*Dialog.msg.font', 'Arial 12')  # Change font if necessary

        self.root.resizable(0, 0)
        self.root.minsize(1280, 720) # Pievieno minimālās un maksimālās vērtības logam
        self.root.maxsize(1920, 1080)
        self.root.geometry('1280x720')
        self.root.configure(bg="#fff") # Pievieno logam aizmugures krāsu
        
        self.com_port = "COM1"
        center(self.root)# Funkcijas palaišana, lai iecentrētu programmatūru ekrāna vidū

        self.current_language = "english"

    def GetConf(self):
                # Load the JSON data from file
        with open('I2C_Scanner_V_1_1\ConfigurationApp\conf.json', encoding='utf-8') as f:
            self.language = json.load(f)

    def HandleClick(self):

        if self.current_language == "english":
            self.current_language = "latvian"

        elif self.current_language == "latvian":
            self.current_language = "english"

        self.navbar.destroy()
        self.content_box.destroy()
        self.CreateWindow()

    def CheckDevice(self):

        self.device_port_value = self.device_port.get()

        # Check if the value is a number in the range 1-256
        if self.device_port_value.isdigit() and 1 <= int(self.device_port_value) <= 256:
            self.device_port_value = "COM" + self.device_port_value

        # Check if the value starts with "COM" and has a number in the range 1-256
        elif self.device_port_value.startswith("COM") and self.device_port_value[3:].isdigit() and 1 <= int(self.device_port_value[3:]) <= 256:
            pass  # Value is already in the correct format

        # Check if the value starts with "com" and has a number in the range 1-256
        elif self.device_port_value.startswith("com") and self.device_port_value[3:].isdigit() and 1 <= int(self.device_port_value[3:]) <= 256:
            self.device_port_value = "COM" + self.device_port_value[3:].upper()  # Convert to uppercase and prepend "COM"
            
        else:
            print("Invalid device COM port:", self.device_port_value)
            return  # Return if the value doesn't match any of the conditions
    
        print("Modified device COM port:", self.device_port_value)

    def CreateWindow(self):

        self.clicked_history = False
        self.clicked_config = False

        self.root.title(self.language[self.current_language][0]["title"])

        self.content_box = Frame(self.root, width=1300, height=600)

        image = Image.open("I2C_Scanner_V_1_1\ConfigurationApp\images\otradi copy.tif")
        image = image.resize((800, 400))

        self.image = ImageTk.PhotoImage(image)
        self.home_image = Label(self.content_box, image=self.image, width=800, height=500, anchor=CENTER, bg="#fff")
        self.home_image.image = self.image

        self.home_image.pack()

        self.history_box = Frame()
        self.configure_box = Frame()

        self.CreateNavbar()
        self.content_box.pack(side=BOTTOM)

        self.root.mainloop()

    def CreateNavbar(self):
        self.navbar = Frame(self.root, bg="green", height="150", width="2000")
        Frame(self.navbar, width="200", height="50", bg="#000").place(x="35", y="45")
        logo_frame = Frame(self.navbar, width="200", height="50")
        Label(logo_frame, fg="black", font=('MS Sans Serif', 28, 'bold'), text="IN").place(x="5", y="0")
        Label(logo_frame, fg="green", font=('MS Sans Serif', 28, 'bold'), text="PASS").place(x="45", y="0")
        logo_frame.place(x="30", y="40")

        self.history_button = Button(self.navbar, text=self.language[self.current_language][0]["history"], font=('MS Sans Serif', 16, 'bold'), padx=5, pady=5, command=self.LoadHistory, highlightbackground="black").place(x=350, y=45)

        self.configure_button = Button(self.navbar, text=self.language[self.current_language][0]["configure"], font=('MS Sans Serif', 16, 'bold'), padx=5, pady=5, command=self.LoadConfigure).place(x=550, y=45)

        self.language_button = Button(self.navbar, text=self.language[self.current_language][0]["language"], font=('MS Sans Serif', 16, 'bold'), padx=5, pady=5, command= self.HandleClick).place(x=1150, y=45)

        self.check_device = Button(self.navbar, text=self.language[self.current_language][0]["check_device"], font=('MS Sans Serif', 16, 'bold'), padx=5, pady=5, command= self.CheckDevice).place(x=900, y=45)

        Label(self.navbar, text = self.language[self.current_language][0]["device_com_port"], font=('MS Sans Serif', 12, 'bold'), bg="green").place(x=800, y=110)
        self.device_port = Entry(self.navbar)
        self.device_port.place(x=950, y= 110)
        self.navbar.pack(side=TOP)

    def LoadHistory(self):
        if self.clicked_history:
            return
            
        self.clicked_history = True
        
        self.configure_box.destroy()
        if hasattr(self, 'home_image') and self.home_image:
            self.home_image.destroy()
        else:
            self.CreateWindow()
        
        self.history_box = Frame(self.content_box, width=1300, height=600,)

        self.ttunit_box = Frame(self.history_box, width=500, height=500, bd=2, relief=SOLID)
        Label(self.ttunit_box, text=self.language[self.current_language][0]["history_tt_label"], font= ('MS Sans Serif', 16, 'bold') ).place(x=5, y=5)
        Button(self.ttunit_box, text=self.language[self.current_language][0]["history_delete_button"]).place(x=350, y=5)
        self.ttunit_box.place(x=20, y=20)

        self.controlunit_box = Frame(self.history_box, width=500, height=500, bd=2, relief=SOLID)
        Label(self.controlunit_box, text=self.language[self.current_language][0]["history_cu_label"], font=('MS Sans Serif', 16, 'bold')).place(x=5, y=5)
        Button(self.controlunit_box, text=self.language[self.current_language][0]["history_delete_button"]).place(x=350, y=5)
        self.controlunit_box.place(x=620, y=20)

        self.history_box.pack()
        self.clicked_config = False

    def LoadConfigure(self):
        if self.clicked_config:
            return
            
        self.clicked_config = True
        
        self.history_box.destroy()
        if hasattr(self, 'home_image') and self.home_image:
            self.home_image.destroy()
        else:
            self.CreateWindow()

        self.configure_box = Frame(self.content_box, width=1200, height=500, bd=2, relief=SOLID)
        self.configure_box.place(x=30, y=5)

        Label(self.configure_box, text=self.language[self.current_language][0]["configure_label"], font=('MS Sans Serif', 18, 'bold')).place(x=20, y= 20)

        self.clicked_history = False


Window = ConfigTTCUChecker()
Window.CreateWindow()