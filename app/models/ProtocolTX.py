class ProtocolTX:
    def __init__(self):
        self.ByteStuff1Char = '}'
        self.ByteStuff1 = f"{self.ByteStuff1Char}^"
        self.ByteStuff2 = f"{self.ByteStuff1Char}]"
        self.StartChr = '~'

    def Output(self, Command, Data):
        MessageLength = chr(len(Data) + 1)
        MessageNumber = Command
        message = f"{MessageLength}{MessageNumber}{Data}{self.CalculateChk(f'{MessageLength}{MessageNumber}{Data}')}"
        return f"{self.StartChr}{self.GetBufferByteStuffed(message)}"

    def GetBufferByteStuffed(self, St):
        StOut = ""
        for char in St:
            if char == self.StartChr:
                StOut += self.ByteStuff1
            elif char == self.ByteStuff1Char:
                StOut += self.ByteStuff2
            else:
                StOut += char
        return StOut

    def CalculateChk(self, Data):
        Sum1 = 0
        Sum2 = 0
        for char in Data:
            Sum1 = (Sum1 + ord(char)) % 255
            Sum2 = (Sum2 + Sum1) % 255
        return chr(Sum1) + chr(Sum2)
