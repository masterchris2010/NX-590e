
class Zone:
    def __init__(self):
        self.name = ""
        self.number = 0
        self.partition_enabled = False

    def SetName(self, name):
        self.name = name

    def SetPartionEnabled(self, enabled):
        self.partition_enabled = enabled

    def SetNumber(self, number):
        self.number = number

    def GetName(self):
        return self.name if self.name else f"Zone {self.number}"

    def __str__(self):
        return f"Zone {self.number}: {self.name}" if self.name else f"Zone {self.number}"

    def __repr__(self):
        return self.__str__()

class Zones:
    def __init__(self, listener, SettingPath, Model):
        self._zones = {}

    def MaxZones(self):
        return 8

    def GetZone(self, ZoneNumber):
        if ZoneNumber not in self._zones:
            zone = Zone()
            zone.SetNumber(ZoneNumber)
            self._zones[ZoneNumber] = zone
        return self._zones[ZoneNumber]

    def SetState(self, ZoneNumber, state):
        pass

    def SaveConfig(self):
        pass

    def ConfigOK(self):
        return True
