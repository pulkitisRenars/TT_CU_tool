import time
import ustruct as struct
import sys
from machine import Pin, UART

class MSG():
    serial="/dev/ttyAMA0"
    rate=57600
    
    CU_conf={}
    _CU_conf={}
    
    conf=None
    PUSH_callback=None
    CONF_callback=None
    
    resend_delay=200
    queue=[]
    rQueue=[]
    sq=0
    send_time=0
    rxP=Pin(5)
    txP=Pin(4)
    dev=None
    
    # Viens kadrs ir 4 baiti.
    frame_size=4
    rcv_count=0
    buffer=bytearray(0)
    
    # Visas kommandas uz ControlUnit.
    type_map={
        "ACK":0,
        "GET":1,
        "SET":2,
        "PUSH":3,
        "SIGNAL":4,
        "CONF":5,
    }
    r_type_map = {v: k for k, v in type_map.items()}
    
    SIGNAL={
        "turnstile1_a":0,
        "turnstile1_b":1,
        "doorlock1":2,
        "turnstile2_a":3,
        "turnstile2_b":4,
        "doorlock2":5,
        "button1":6,
        "button2":7,
        "arm1_drop":8,
        "arm2_drop":9,
        "arm1_ready":10,
        "arm2_ready":11,
    }
    r_SIGNAL = {v: k for k, v in SIGNAL.items()}
    
    SET={
        "configuration_clear":1,
        "doorlock1_close_state":2,
        "doorlock2_close_state":3,
        "doorlock1_duration":4,
        "doorlock2_duration":5,
        
        "arm1_port":6,
        "arm2_port":7,
        
        "alarm_on_state": 8,
        
        "turnstile1_mode":9,
        "turnstile2_mode":10,
        
        "turnstile1_duration":11,
        "turnstile2_duration":12,
        
        "button1_channel":13,
        "button2_channel":14,
        
        "channel1":15,
        "channel2":16,
        "channel3":17,
        "channel4":18,
        
        "door1_open_mode": 35,
        "door2_open_mode": 36,
    }
    r_SET = {v: k for k, v in SET.items()}
    
    GET={
        "ping":0,
        "board_version":1,
        "configuration_revision":2,
        "alarm_state":3,
        "turnstile1_state":4,
        "turnstile2_state":5,
        "doorlock1_state":6,
        "doorlock2_state":7,
        "button1_state":8,
        "button2_state":9,
        "arm1_state":10,
        "arm2_state":11,
        "configuration":12,
        "door1_open_mode":13,
        "door2_open_mode":14,
        "power_state":15,
    }
    r_GET = {v: k for k, v in GET.items()}
    
    
    CONF={
        "configuration_revision":0,
        "board_version":1,
        "doorlock1_close_state":2,
        "doorlock2_close_state":3,
        "doorlock1_duration":4,
        "doorlock2_duration":5,
        "arm1_port":6,
        "arm2_port":7,
        
        "alarm_on_state": 8,
        
        "turnstile1_mode":9,
        "turnstile2_mode":10,
        "turnstile1_duration":11,
        "turnstile2_duration":12,
        "button1_channel":13,
        "button2_channel":14,
        "channel1_count":15,
        "channel2_count":16,
        "channel3_count":17,
        "channel4_count":18,

        "channel1_port1":19,
        "channel1_port2":20,
        "channel1_port3":21,
        "channel1_port4":22,
        
        "channel2_port1":23,
        "channel2_port2":24,
        "channel2_port3":25,
        "channel2_port4":26,
        
        "channel3_port1":27,
        "channel3_port2":28,
        "channel3_port3":29,
        "channel3_port4":30,
        
        "channel4_port1":31,
        "channel4_port2":32,
        "channel4_port3":33,
        "channel4_port4":34,
        
        "door1_open_mode": 35,
        "door2_open_mode": 36,
    }
    r_CONF = {v: k for k, v in CONF.items()}
    
    must_have_conf_keys=[
        "configuration_revision",
        "board_version",
        "doorlock1_close_state",
        "doorlock2_close_state",
        "doorlock1_duration",
        "doorlock2_duration",
        "arm1_port",
        "arm2_port",
        "alarm_on_state",
        "turnstile1_mode",
        "turnstile2_mode",
        "turnstile1_duration",
        "turnstile2_duration",
        "button1_channel",
        "button2_channel",
        "door1_open_mode",
        "door2_open_mode",
        "channel1_count",
        "channel2_count",
        "channel3_count",
        "channel4_count",
    ]


    channel_ports={
        "turnstile1_a":1,
        "turnstile1_b":2,
        "doorlock1":3,

        "turnstile2_a":4,
        "turnstile2_b":5,
        "doorlock2":6,
    }
    r_chP = {v: k for k, v in channel_ports.items()}

    # Konstruktors klasei, kas izveido savienojumu starp rīku un ControlUnit mikročipu.
    def __init__(self,print,rx=rxP,tx=txP,rate=rate):
        self.rate=rate
        self.PUSH=self.GET
        uart=UART(1,baudrate=57600,timeout=1,tx=tx,rx=rx, invert=0)
        uart.init(flow=uart.RTS|uart.CTS)
        #print(uart.read())
        self.Logger_handler=print
        self.dev=uart
        self.MSGSocket=None

    # Funkcija, kas pārbauda savienojamību starp rīku un ControlUnit mikročipu.
    def HWCheck(self,timeout=3000):
            print("rrr")
            ts = time.time()
            self.Queue("GET","board_version")
            self.Send(True)
            print("gsa")
            data=self.Receive(True)
            print(data)
        
            if data:
                    for frame in data:
                        if "value" in frame:
                            self.ACK(frame["sq"])
                            return True
            else:
                    time.sleep(1)

            return False
        
    def reverseE(self,byte):
        chunk_size = 4
        byte_list = [byte[i:i+chunk_size] for i in range(0, len(byte), chunk_size)]
        
        for chunk in byte_list:
            sq=chunk[0]
            method=chunk[1]
            cmd=chunk[2]
            value=chunk[3]
            print(str(method)+": method")
            print(str(cmd)+": command")
            print(str(value)+": val")
            if not method in self.r_type_map or ( not cmd in self.r_GET and not cmd in self.r_SET and not cmd in self.r_SIGNAL ):
                self.Logger("error","Failed to Queue({},{},{})".format(method,cmd,value))
                return
            type=self.r_type_map[method]
            if method==1:
                key=self.r_GET[cmd]
            elif method==2:
                key=self.r_SET[cmd]
            elif method==3:
                key=self.r_SET[cmd]
            elif method==4:
                key=self.r_SIGNAL[cmd]
            elif method==5:
                key=self.r_CONF[cmd]
            elif method==0:
                key=sq
            frame={
                "sq":sq,
                "type":type,
                "key":key,
                "value":value
            }
#             self.Logger("debug","Queue({},{},{})".format(method,cmd,value) )
            self.rQueue.append( frame )
        return self.rQueue


    # Funkcija, kas pievieno sarakstei komandu.
    def Queue(self,method,cmd,value=0):
        if not method in self.type_map or ( not cmd in self.GET and not cmd in self.SET and not cmd in self.SIGNAL ):
            self.Logger("error","Failed to Queue({},{},{})".format(method,cmd,value))
            return

        self.sq+=1
        if self.sq>255:
            self.sq=1

        # Atšifrē komandas atslēgu.
        type=self.type_map[method]
        if method=="GET":
            key=self.GET[cmd]
        elif method=="SET":
            key=self.SET[cmd]
        elif method=="SIGNAL":
            key=self.SIGNAL[cmd]

        frame={
            "sq":int(self.sq),
            "type":int(type),
            "key":int(key),
            "value":int(value)
        }

        self.Logger("debug","Queue({},{},{})".format(method,cmd,value) )
        self.queue.append( frame )

    # Funkcija, kas nosūta sarakstei pievienotās komandas uz ControlUnit mikročipu.
    def Send(self,no_resend=False):
        global blobData
        now  = self.millis()
        blob=bytes()
        for frame in self.queue:
                blob += struct.pack('BBBB', int(frame["sq"]), int(frame["type"]), int(frame["key"]), int(frame["value"]))
                # blob+=struct.pack('B', int(frame["sq"]) ); # sq
                # blob+=struct.pack('B', int(frame["type"]) ); # type
                # blob+=struct.pack('B', int(frame["key"]) ); # key
                # blob+=struct.pack('B', int(frame["value"]) ); # value

        self.Logger("debug","Sending {} bytes / {} frames".format(len(blob) , len(self.queue) ) )
        print(blob)
        print("sending")
        self.dev.write(blob)
        blobData=list(blob)
        print(blob)
        print(blobData)
        self.send_time=self.millis()

            # Clear queue after sending data
        if no_resend:
            self.queue=[]

    # Funkcija, kas saņem atbildi no ControlUnit mikročipa.
    def Receive(self, return_data=False):
        rcv_size = len(blobData)
        if rcv_size > 0:
            # Kad ir jauni dati, izveido saraksti.
            if self.rcv_count == 0:
                self.buffer = []
            dump = ""
            for i in range(0, rcv_size):
                self.buffer.append(blobData[i])
                dump += "{} ".format(int(self.buffer[self.rcv_count]))
                self.rcv_count += 1
                print(self.buffer)    
                if self.rcv_count % 4 == 0:
                    self.Logger("debug", "Receive buffer: {}".format(dump))
                    dump = ""

        if self.rcv_count > 0:
            if self.rcv_count % self.frame_size == 0:
                frame_count = int(self.rcv_count / self.frame_size)

                self.Logger("debug", "Received {} bytes / {} frames".format(self.rcv_count, frame_count))
                rcv_data = []
                for i in range(frame_count):
                    frame = {}
                    for c, cmd in enumerate(["sq", "type", "key", "value"]):
                        index = ((c + 1) + (4 * i)) - 1
                        frame[cmd] = self.buffer[index]
                    rcv_data.append(frame)
                print("in receive")
                print(rcv_data)
               
                # Atgriež datus, ja tie ir saņemti.
                if return_data:
                    print("log")
                    # Iztīra saraksti.
                    self.buffer = bytearray(0)
                    self.rcv_count = 0
                    return rcv_data

                for data in rcv_data:
                    # Validē atgrieztos datus
                    if data["type"] == 0 and data["key"] == 0 and data["value"] == 0:
                        self.Logger("error", "Received invalid data bits: {}".format(data))
                        continue

                    if data["type"] == self.type_map["ACK"]:
                        self.ProcACK(data["key"])
                        self.ACK_callback(data["key"])
                    else:
                        self.ACK(data["sq"])
                        
                            
                        if data["type"]==self.type_map["PUSH"]:
                            self.KeyToPUSHCMD(data["key"]) , data["value"] 
                            self.PUSH_callback(data["key"],data["value"])
                        elif data["type"]==self.type_map["CONF"]:
                            self.KeyToCONFCMD(data["key"]) , data["value"] 
                            self.CONF_callback(data["key"],data["value"])

            # Atgriež, ka neveiksmīgi saņemta atbilde
            else:
                blob_bytes = []
                for i in range(0, self.rcv_count):
                    blob_bytes.append(str(self.buffer[i]))

                self.Logger("error", "Invalid data received ({} bytes): {}".format(self.rcv_count, " ".join(blob_bytes)))

            # clear buffer
            self.buffer = bytearray(0)
            self.rcv_count = 0


# Palīg-funkcijas rīka un ControlUnit komunikācijai.
    def ACK(self,sq):
        self.Logger("debug","ACK({})".format(sq))
        frame={
            "sq":0,
            "type":self.type_map["ACK"],
            "key":sq,
            "value":0
        }
        print("ack")
        blob = struct.pack('BBBB', int(frame["sq"]), int(frame["type"]), int(frame["key"]), int(frame["value"]))
        print(blob)

        # blob+=struct.pack('B', int(frame["sq"]) ); # sq
        # blob+=struct.pack('B', int(frame["type"]) ); # type
        # blob+=struct.pack('B', int(frame["key"]) ); # key
        # blob+=struct.pack('B', int(frame["value"]) ); # value
        self.dev.write(blob)
    
    def ProcACK(self,sq):
        self.Logger("debug","ProcACK({})".format(sq))
        
        found_sq=False
        tmp_queue=[]
        for data in self.queue:
            if data["sq"]==sq:
                found_sq=True
            else:
                tmp_queue.append( data )
        if found_sq==True:
            self.queue=tmp_queue
        else:
            self.Logger("error","ProcACK sq:{} not found in queue!".format(sq))
            
    
    def QueueSize(self):
        return len(self.queue)
    
    def KeyToCONFCMD(self,key):
        for cmd in self.CONF:
            if self.CONF[cmd]==key:
                return cmd
        
        return False
    
    def KeyToPUSHCMD(self,key):
        for cmd in self.PUSH:
            if self.PUSH[cmd]==key:
                return cmd
        
        return False
    
    def millis(self):
        return int(round(time.time() * 1000))
    
    def Logger(self,sev,msg):
        print( sev, "MSG: {}".format(msg))
        if not type(self.Logger_handler)==None:
            if sev=="debug" and ( self.conf==None or not "debug" in self.conf or not self.conf["debug"].lower()=="true" ):
                return
            self.Logger_handler( sev, "MSG: {}".format(msg) )
        else:
                print ("{}: {} - {}".format(time.strftime("%H:%M:%S", time.localtime()), sev, msg))

