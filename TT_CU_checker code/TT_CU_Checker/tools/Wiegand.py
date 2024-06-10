import machine
import time

MASK = 0x80000000


def ticks_ms():
    return int(round(time.time() * 1000))

def translateEnterEscapeKeyPress(originalKeyPress):
    if originalKeyPress == 0x0b:
        return 0x0d
    elif originalKeyPress == 0x0a:
        return 0x1b
    else:
        return originalKeyPress
    
# Funkcija, kas apgriež hex datus priekš korektas nolasīšanas.
def reverse_hex(hex_string):
    # Noņem nevajadzīgos datus.
    if hex_string.startswith('0x'):
        hex_string = hex_string[2:]

    # Validē hex datus.
    if not all(char in '0123456789abcdefABCDEF' for char in hex_string):
        raise ValueError("Invalid hexadecimal string")

    # Apgriež datus.
    byte_list = [hex_string[i:i + 2] for i in range(0, len(hex_string), 2)]
    reversed_hex = ''.join(byte_list[::-1])

    # Pievieno beigās hex datus.
    reversed_hex = '0x' + reversed_hex

    return reversed_hex

class Wiegand:

    # Konstruktors Wiegand protokola izmantošanai.
    def __init__(self, pin0, pin1):
        self.pin0 = machine.Pin(pin0, machine.Pin.IN)
        self.pin1 = machine.Pin(pin1, machine.Pin.IN)

        self.pin0.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.ReadD0)
        self.pin1.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.ReadD1)
        
        self._code=0
        self._revCode=0
        self._wiegandType=0
        self._bitCount=0
        self._cardTempHigh=0
        self._cardTemp=0
        self._lastWiegand=0
        self.bits=[]
        self.last_bit_time = time.ticks_ms()
        
# Atgriež RFID kartes datus.
    def GetCode(self):
        return self._code
    
    def GetRevCode(self):
        return self._revCode
        
    def GetType(self):
        return self._wiegandType

# Nolasa pirmās tapas datus.
    def ReadD0(self,pin):
        self._on_bit(0)
        self._bitCount += 1
        if self._bitCount > 31:
            self._cardTempHigh |= ((MASK & self._cardTemp)>>31)
            self._cardTempHigh <<= 1
            self._cardTemp <<=1
        else:
            self._cardTemp <<=1
        
        self._lastWiegand = ticks_ms()
    
# Nolasa otrās tapas datus.
    def ReadD1(self,pin):
        self._on_bit(1)
        self._bitCount += 1
        if self._bitCount > 25:
            self._cardTempHigh |= ((MASK & self._cardTemp)>>25)
            self._cardTempHigh <<= 1
            self._cardTemp |= 1
            self._cardTemp <<=1
        else:
            self._cardTemp |= 1
            self._cardTemp <<=1
            
        self._lastWiegand = ticks_ms()

# Bitu apstrāde no tapām.   
    def _on_bit(self, bit):
        current_time = time.ticks_ms()
        if current_time - self.last_bit_time > 10:
            self.bits = [] 
        self.bits.append(bit)
        self.last_bit_time = current_time
        print(self.bits)

# Nosaka vai kartes dati ir nolasīti. 
    def available(self):
        return self.ConvertWiegand()

# Funkcija, kas apstrādā kartes datus un tos atgriež.
    def ConvertWiegand(self):
        sysTick = ticks_ms()
        ret=False
        if (sysTick - self._lastWiegand) > 25:
            if self._bitCount in [24,26,32,34,8,4]:
                self._cardTemp >>= 1
                

                if self._bitCount>32:
                    self._cardTempHigh >>= 1

                # Kartes ar 8-bitu identifikātora apstrādes process.
                if self._bitCount==8:
                    highNibble = (self._cardTemp & 0xf0 ) >> 4
                    lowNibble = (self._cardTemp & 0x0f )
                    
                    if lowNibble == (~highNibble & 0x0f):
                        self._code = int(translateEnterEscapeKeyPress(lowNibble))
                        ret=True
                    else:
                        self._lastWiegand=sysTick
                        ret=False

                # Kartes ar 4-bitu identifikātora apstrādes process.
                elif self._bitCount==4:
                    self._code = int(translateEnterEscapeKeyPress(self._cardTemp & 0x0F))
                    ret=True
                
                # Kartes ar 26-bitu vai 32-bitu identifikātora apstrādes process.
                else:
                    if self._bitCount>32:
                        # Kartes ar 32-bitu identifikātora apstrādes process.
                        binArr=''.join(map(str, self.bits))[1:-1]
                        binArr=int(binArr,2)
                        fHex=hex(binArr)
                        bHex= reverse_hex(fHex)
                        self._code = int(fHex)
                        self._revCode=int(bHex)
                    else:
                        # Kartes ar 24-bitu identifikātora apstrādes process.
                        self._code = (self._cardTempHigh << 16) | (self._cardTemp & 0x0000FFFF)
                    
                    ret=True
            else:
                self._lastWiegand=sysTick
                ret=False
                
            self._wiegandType=0
            if ret==True:
                self._wiegandType=self._bitCount
                
            self._bitCount=0
            self._cardTemp=0
            self._cardTempHigh=0
        
        return ret
