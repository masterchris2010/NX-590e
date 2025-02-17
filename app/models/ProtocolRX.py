import logging
import time
from threading import Timer

class ProtocolRX:
    def __init__(self, ProtocolRXEventsListener):
        self.ByteStuff1Char = '}'
        self.ByteStuff1 = f"{self.ByteStuff1Char}^"
        self.ByteStuff2 = f"{self.ByteStuff1Char}]"
        self.CurrentBufferIn = ""
        self.CurrentBufferInTmp = ""
        self.LastPacketOK = time.time()
        self.MaximuPacketLength = 110
        self.MinumPacketLength = 5
        self.OnAnalizing = False
        self.ParseSleepTime = 0.02
        self.ProtocolRXEventsListener = ProtocolRXEventsListener
        self.StartChr = '~'
        self._ParseIsRunning = False
        self.myTimerParsing = None

    def GetParseIsRunning(self):
        return self._ParseIsRunning

    def StartParsing(self):
        self.myTimerParsing = Timer(self.ParseSleepTime, self.Parsing)
        self.myTimerParsing.start()

    def Parsing(self):
        if not self.OnAnalizing:
            self.OnAnalizing = True
            self.AnalizeBuffer()
            self.OnAnalizing = False
        self.StartParsing()

    def StopParsing(self):
        if self.myTimerParsing:
            self.myTimerParsing.cancel()
            self.myTimerParsing = None

    def ResetBuffer(self):
        self._ParseIsRunning = False
        self.CurrentBufferIn = ""

    def ReceiveBuffer(self, Buffer):
        self.CurrentBufferInTmp += Buffer
        if not self._ParseIsRunning:
            self._ParseIsRunning = True
            self.LastPacketOK = time.time()
            self.StartParsing()

    def AnalizeBuffer(self):
        CurBufferTmpLenght = len(self.CurrentBufferInTmp)
        self.CurrentBufferIn += self.CurrentBufferInTmp[:CurBufferTmpLenght]
        self.CurrentBufferInTmp = self.CurrentBufferInTmp[CurBufferTmpLenght:]
        if time.time() - self.LastPacketOK > 2 and len(self.CurrentBufferIn) > self.MaximuPacketLength * 4:
            self.ClearBuffer()
            self.LastPacketOK = time.time()
        if len(self.CurrentBufferIn) <= 0:
            return
        if self.CurrentBufferIn.startswith(self.StartChr):
            # self.WriteToLog("StartChar OK!")
            if len(self.CurrentBufferIn) >= self.MinumPacketLength:
                BufferUnstuffed = self.GetBufferUnByteStuffed()
                Lenght = ord(BufferUnstuffed[1]) + 4
                if Lenght <= len(BufferUnstuffed):
                    BufferUnstuffed2 = BufferUnstuffed[:Lenght][1:]
                    # self.WriteToLog("Lenght OK!")
                    if self.PairingChecksum(BufferUnstuffed2):
                        # self.WriteToLog("Checksum OK!")
                        self.ClearBufferOkFromBuffer(self.GetBufferByteStuffedLength(BufferUnstuffed2) + 1)
                        BufferOK = BufferUnstuffed2[:-2][1:]
                        Cmd = ord(BufferOK[0])
                        Data = BufferOK[1:] if len(BufferOK) > 1 else ""
                        self.ProtocolRXEventsListener.PacketReceived(Cmd, Data)
                        return
                    # self.WriteToLog("Checksum Fradicio!!!!!!!")
                    self.ClearBuffer()
                    return
                return
            return
        # self.WriteToLog("StartChar Fradicio!!!!!!!")
        self.ClearBuffer()

    def ClearBuffer(self):
        self.CurrentBufferIn = ""

    def GetBufferUnByteStuffed(self):
        St = self.CurrentBufferIn
        StOut = St[0]
        I = 1
        while I <= len(St) - 2:
            if St[I:I + 2] == self.ByteStuff1:
                StOut += self.StartChr
                I += 1
            elif St[I:I + 2] == self.ByteStuff2:
                StOut += self.ByteStuff1Char
                I += 1
            else:
                StOut += St[I]
            I += 1
        return StOut + St[-1]

    def GetBufferByteStuffedLength(self, St):
        StOut = ""
        for char in St:
            if char == self.StartChr:
                StOut += self.ByteStuff1
            elif char == self.ByteStuff1Char:
                StOut += self.ByteStuff2
            else:
                StOut += char
        return len(StOut)

    def PairingChecksum(self, BufferUnstuffed):
        return self.CalculateChk(BufferUnstuffed[:-2]) == BufferUnstuffed[-2:]

    def ClearBufferOkFromBuffer(self, PacketLengthUntilEnd):
        if PacketLengthUntilEnd < len(self.CurrentBufferIn):
            # self.WriteToLog("ClearBufferOkFromBuffer Buffer più lungo!")
            self.CurrentBufferIn = self.CurrentBufferIn[PacketLengthUntilEnd:]
        else:
            self.ClearBuffer()

    def CalculateChk(self, Data):
        Sum1 = 0
        Sum2 = 0
        for char in Data:
            Sum1 = (Sum1 + ord(char)) % 255
            Sum2 = (Sum2 + Sum1) % 255
        return chr(Sum1) + chr(Sum2)

    def WriteToLog(self, Data):
        logging.debug(f"Protocol RX - {Data}")
