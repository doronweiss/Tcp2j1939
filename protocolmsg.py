import threading
import queue
from enum import Enum, auto
import zlib
import crcengine

class DecoderPhase(Enum):
    wait = auto()
    wait2 = auto()
    waitsz = auto()
    data = auto()
    crc1 = auto()
    crc2 = auto()

# >>> list(crcengine.algorithms_available())
# ['crc8', 'crc8-autosar', 'crc8-bluetooth', 'crc8-ccitt', 'crc8-gsm-b', 'crc8-sae-j1850', 'crc15-can', 'crc16-kermit', 'crc16-ccitt-true', 'crc16-xmodem', 'crc16-autosar', 'crc16-ccitt-false', 'crc16-cdma2000', 'crc16-ibm', 'crc16-modbus', 'crc16-profibus', 'crc24-flexray16-a', 'crc24-flexray16-b', 'crc32', 'crc32-bzip2', 'crc32-c', 'crc64-ecma']

class MessageDecoder  (threading.Thread):
    def __init__(self, topcb):
        threading.Thread.__init__(self)
        self.dataQueue = queue.Queue()
        self.mre = threading.Event()
        self.bcontinue = True
        self.topcb = topcb
        # decoding data
        self.decodPhase = DecoderPhase.wait
        self.bytesFilled=0
        self.messageData=[]
        self.messageSz = 0
        self.dataidx=0
        self.crcAlg = crcengine.new('crc16-modbus')
        self.crc = 0
        self.crcHi = self.cecLow = 0

    def enqueue (self, data):
        self.dataQueue.put(data)
        self.mre.set()

    def dequeue (self):
        try:
            return self.dataQueue.get(False)  # doesn't block
        except:
            return None

    def run(self):
        while self.bcontinue:
            self.mre.wait(0.1)
            self.mre.clear()
            while True: # queue emptying loop
                data = self.dequeue()
                if data is not None:
                    for b in data:
                        res = self.datadecoder(b)
                        if res is not None and self.topcb is not None:
                            self.topcb(res)
                else:
                    break

    def datadecoder (self,b) -> bytes:
        if self.decodPhase==DecoderPhase.wait:
            if b==255:
                self.bytesFilled=0
                self.decodPhase=DecoderPhase.wait2
            return None
        elif self.decodPhase==DecoderPhase.wait2:
            if b==255:
                self.decodPhase=DecoderPhase.waitsz
            return None
        elif self.decodPhase==DecoderPhase.waitsz:
            self.messageSz = int (b)
            self.dataidx = 0
            self.messageData = []
            self.decodPhase=DecoderPhase.data
            return None
        elif self.decodPhase==DecoderPhase.data:
            self.messageData.append(b)
            self.dataidx += 1
            if self.dataidx == self.messageSz:
                self.decodPhase = DecoderPhase.crc1
            return None
        elif self.decodPhase==DecoderPhase.crc1:
            self.crc = int(b)
            self.rcLow = b
            self.decodPhase = DecoderPhase.crc2
        elif self.decodPhase == DecoderPhase.crc2:
            self.crc += int(b) * 256
            self.crcHi = b
            self.decodPhase = DecoderPhase.wait
            calcedCrc = self.calcCrc(self.messageData)
            #print ("Msg cr = {}, calculated crc= {}".format(self.crc, calcedCrc))
            if self.crc == calcedCrc:
                #print ("got: {}".format(self.messageData[3:self.messageSz+3]))
                return self.messageData
            else:
                return None

    def calcCrc (self, data):
        return self.crcAlg(data)