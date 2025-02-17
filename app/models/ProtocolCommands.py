import logging
from datetime import datetime
from collections import defaultdict
from app.models.ProtocolRX import ProtocolRX
from app.models.ProtocolTX import ProtocolTX

class ProtocolCommands:
    def __init__(self, ProtocolCommandsEventsListener, Model, SettingPath):
        self.CMD_1C_CommandRequestFailed = chr(28)
        self.CMD_1D_PositiveAcknowledge = chr(29)
        self.CMD_1E_NegativeAcknowledge = chr(30)
        self.CMD_1F_MessageRejected = chr(31)
        self.CMD_21_InterfaceConfigurationRequest = chr(33)
        self.CMD_23_ZonaNameRequest = chr(35)
        self.CMD_24_ZonaStatusRequest = chr(36)
        self.CMD_25_ZonaSnapShotRequest = chr(37)
        self.CMD_27_PartitionSnapShotRequest = chr(39)
        self.CMD_28_SystemStatusRequest = chr(40)
        self.CMD_29_SendX10Message = chr(41)
        self.CMD_2A_LogEventRequest = chr(42)
        self.CMD_3B_SetClock = chr(59)
        self.CMD_3D_PrimaryKeyPadFunctionWithoutPIN = chr(61)
        self.CMD_3F_ZoneByPassToggle = chr(63)
        self.LastPacketSent = ""
        self.LogEventFirstRequest = False
        self.RX = ProtocolRX(self)
        self.TX = ProtocolTX()
        self._Areas = Areas(self)
        self._FirmwareVersion = ""
        self._MaxEventNumber = 0
        self._Model = Model
        self._X10s = X10s()
        self._Zones = Zones(self, SettingPath, Model)
        self._dicEvents = defaultdict(datetime)
        self.arrCommands = []
        self.arrCommandsAnswer = []
        self.arrCommandsPolling = []


    def ResetBuffer(self):
        self.RX.ResetBuffer()

    def Send_CMD_1C_CommandRequestFailed(self):
        return self.TX.Output(self.CMD_1C_CommandRequestFailed, "")

    def Send_CMD_1D_PositiveAcknowledged(self):
        return self.TX.Output(self.CMD_1D_PositiveAcknowledge, "")

    def Send_CMD_1E_NegativeAcknowledge(self):
        return self.TX.Output(self.CMD_1E_NegativeAcknowledge, "")

    def Send_CMD_1F_MessageRejected(self):
        return self.TX.Output(self.CMD_1F_MessageRejected, "")

    def Send_CMD_21_InterfaceConfigurationRequest(self):
        return self.TX.Output(self.CMD_21_InterfaceConfigurationRequest, "")

    def Send_CMD_23_ZonaNameRequest(self, ZoneNumber):
        return self.TX.Output(self.CMD_23_ZonaNameRequest, chr(ZoneNumber - 1))

    def Send_CMD_24_ZonaStatusRequest(self, ZoneNumber):
        return self.TX.Output(self.CMD_24_ZonaStatusRequest, chr(ZoneNumber - 1))

    def Send_CMD_25_ZonaSnapShotRequest(self, ZoneNumberStart):
        return self.TX.Output(self.CMD_25_ZonaSnapShotRequest, chr(ZoneNumberStart - 1))

    def Send_CMD_27_PartitionSnapShotRequest(self):
        return self.TX.Output(self.CMD_27_PartitionSnapShotRequest, "")

    def Send_CMD_28_SystemStatusRequest(self):
        return self.TX.Output(self.CMD_28_SystemStatusRequest, "")

    def Send_CMD_29_SendX10Message(self, HouseCode, UnitCode, FunctionCode):
        if 1 <= HouseCode <= 16 and 1 <= UnitCode <= 16:
            return self.TX.Output(self.CMD_29_SendX10Message, f"{chr(HouseCode - 1)}{chr(UnitCode - 1)}{chr(FunctionCode.value)}")
        return ""

    def Send_CMD_2A_LogEventRequest(self, EventNumber):
        return self.TX.Output(self.CMD_2A_LogEventRequest, chr(EventNumber))

    def Send_CMD_3B_SetClock(self):
        cDateTime = datetime.now()
        return self.TX.Output(self.CMD_3B_SetClock, f"{chr(cDateTime.year % 100)}{chr(cDateTime.month)}{chr(cDateTime.day)}{chr(cDateTime.hour)}{chr(cDateTime.minute)}{chr(cDateTime.weekday() + 1)}")

    def Send_CMD_3D_PrimaryKeyPadFunctionWithoutPIN(self, PartitionNumber, Mode, UserNumber):
        Data = f"{chr(int(Mode))}{chr(2 ** (PartitionNumber - 1))}{chr(UserNumber)}"
        return self.TX.Output(self.CMD_3D_PrimaryKeyPadFunctionWithoutPIN, Data)

    def Send_CMD_3F_ZoneByPassToggle(self, ZoneNumber):
        return self.TX.Output(self.CMD_3F_ZoneByPassToggle, chr(ZoneNumber - 1))


    def ReceiveBuffer(self, Buffer):
        self.RX.ReceiveBuffer(Buffer)

    def RX_PacketReceived(self, Cmd, Data):
        ClearLastPacketAndCommandSent = True
        AcknowledgePacket = False
        if Cmd & 128 == 128:
            AcknowledgePacket = True
        Cmd = Cmd & 63
        self.WriteToLog(f"Command = {Cmd}")
        if Cmd == 1:
            self._FirmwareVersion = Data[:4]
        elif Cmd == 3:
            self.RX_PacketReceived_03_ZonaNameMessage(Data)
        elif Cmd == 4:
            self.RX_PacketReceived_04_ZonaStatusRequest(Data)
        elif Cmd == 5:
            self.RX_PacketReceived_05_ZonaSnapShotMessage(Data)
        elif Cmd == 7:
            self.RX_PacketReceived_07_PartitionSnapShotMessage(Data)
        elif Cmd == 10:
            self.RX_PacketReceived_0A_LogEventMessage(Data)
        elif Cmd == 30:
            ClearLastPacketAndCommandSent = False

        if ClearLastPacketAndCommandSent:
            self.LastPacketSent = ""
        if AcknowledgePacket:
            self.WriteToLog("Add Command AcknowledgePacket")
            self.AddCommand_Answer(self.Send_CMD_1D_PositiveAcknowledged())
        self.ProtocolCommandsEventsListener.SendNextCommand()

    def RX_PacketReceived_03_ZonaNameMessage(self, Data):
        ZoneNumber = ord(Data[0]) + 1
        if ZoneNumber == 1:
            self.ProtocolCommandsEventsListener.OnZoneSetupStartedFinished(True)
        elif ZoneNumber >= self._Zones.MaxZones():
            self._Zones.SaveConfig()
            self.ProtocolCommandsEventsListener.OnZoneSetupStartedFinished(False)
        self._Zones.GetZone(ZoneNumber).SetName(Data[1:])

    def RX_PacketReceived_04_ZonaStatusRequest(self, Data):
        self._Zones.GetZone(ord(Data[0]) + 1).SetPartionEnabled(Data[1])

    def RX_PacketReceived_05_ZonaSnapShotMessage(self, Data):
        ZoneNumber = ord(Data[0]) * 16
        for char in Data[1:]:
            CurByte = ord(char)
            ZoneNumber += 1
            self._Zones.SetState(ZoneNumber, CurByte & 15)
            ZoneNumber += 1
            self._Zones.SetState(ZoneNumber, (CurByte >> 4) & 15)

    def RX_PacketReceived_07_PartitionSnapShotMessage(self, Data):
        for i, char in enumerate(Data):
            self._Areas.SetState(i + 1, char)



    def Init(self):
        self.ResetBuffer()
        self.arrCommands.clear()
        self.arrCommandsAnswer.clear()
        self.arrCommandsPolling.clear()
        self.AddCommand(self.Send_CMD_21_InterfaceConfigurationRequest())
        self.AddCommand(self.Send_CMD_2A_LogEventRequest(1))
        if not self._Zones.ConfigOK():
            self.AddCommandForSetupZones()
        self.AddCommand_Polling()

    def AddCommand(self, DataCommand):
        self.arrCommands.append(DataCommand)

    def AddCommand_Answer(self, DataCommand):
        self.arrCommandsAnswer.append(DataCommand)

    def AddCommandForSetupZones(self):
        for i in range(1, self._Zones.MaxZones() + 1):
            self.AddCommand(self.Send_CMD_23_ZonaNameRequest(i))

    def AddCommandForEventsLog(self):
        # Crea il comando di richiesta log eventi e lo aggiunge alla coda
        command = self.TX.Output(self.CMD_2A_LogEventRequest, "")
        self.arrCommands.append(command)
        # ... eventualmente gestire logica aggiuntiva o eventi ...
        # ...existing code...

    def AddCommand_Polling(self):
        ZonaBlockEnd = 1
        if self._Model in [actMain.E_Model.NX4, actMain.E_Model.NX6]:
            ZonaBlockEnd = 1
        elif self._Model in [actMain.E_Model.NX8, actMain.E_Model.NX8C]:
            ZonaBlockEnd = 3
        elif self._Model in [actMain.E_Model.NX8E, actMain.E_Model.NX8EC]:
            ZonaBlockEnd = 12
        for i in range(1, ZonaBlockEnd + 1):
            self.arrCommandsPolling.append(self.Send_CMD_25_ZonaSnapShotRequest(i))
        self.arrCommandsPolling.append(self.Send_CMD_27_PartitionSnapShotRequest())

    def GetNextCommand(self):
        if self.LastPacketSent:
            Ret = self.LastPacketSent
        elif self.arrCommandsAnswer:
            Ret = self.arrCommandsAnswer.pop(0)
        elif self.arrCommands:
            Ret = self.arrCommands.pop(0)
        else:
            if not self.arrCommandsPolling:
                self.AddCommand_Polling()
            Ret = self.arrCommandsPolling.pop(0)
        self.LastPacketSent = Ret
        self.WriteToLog("GetNextCommand")
        return Ret

    def Terminate(self):
        self.RX.StopParsing()
        self.ResetBuffer()

    def PacketReceived(self, Cmd, Data):
        self.RX_PacketReceived(Cmd, Data)

    def OnStateChange(self, Zone):
        self.ProtocolCommandsEventsListener.OnZoneChange(Zone)

    def OnStateChange(self, Area):
        self.ProtocolCommandsEventsListener.OnAreaChange(Area)

    def WriteToLog(self, Data):
        logging.debug(f"Protocol Commands - {Data}")

class LogEventDescription:
    def LoadLogEventDescriptionItalian(self):
        pass

    def GetLogEventDescription(self, EventType):
        return "Event Description"

class actMain:
    class E_Model:
        NX4 = 1
        NX6 = 2
        NX8 = 3
        NX8C = 4
        NX8E = 5
        NX8EC = 6

class Areas:
    def __init__(self, listener):
        pass

    def GetArea(self, PartitionNumber):
        return Area()

    def SetState(self, index, state):
        pass

class Area:
    def IsValid(self):
        return True

class Zones:
    def __init__(self, listener, SettingPath, Model):
        pass

    def MaxZones(self):
        return 8

    def GetZone(self, ZoneNumber):
        return Zone()

    def SetState(self, ZoneNumber, state):
        pass

    def SaveConfig(self):
        pass

    def ConfigOK(self):
        return True

class Zone:
    def SetName(self, name):
        pass

    def SetPartionEnabled(self, enabled):
        pass

class X10s:
    pass
