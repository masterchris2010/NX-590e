import logging
from datetime import datetime
from .ProtocolRX import ProtocolRX
from .ProtocolTX import ProtocolTX
from .ProtocolCommands import ProtocolCommands
from .log_event import LogEventDescription
from .zones import Zones

logger = logging.getLogger(__name__)

class ParentObject:
    # Configuration Constants
    PANEL_TYPE = "NX8"
    SETTINGS_PATH = "settings_path"
    
    # Event Type Constants
    EVENT_TYPE_ZONE = range(0, 17)
    EVENT_TYPE_PERIPHERAL = range(24, 34)
    EVENT_TYPE_USER = range(40, 44)
    EVENT_TYPE_SPECIAL = range(69, 118)
    
    # Status Constants
    STATUS_DISARMED = 3
    STATUS_ARMED = (7, 71)
    STATUS_ARMED_ALARM = 135
    STATUS_END = 2
    
    # Command Constants
    CMD_PARTITION_STATUS = 7
    CMD_ZONE_STATUS = 5
    CMD_ZONE_NAME = 3
    CMD_LOG_EVENT = 10

    def __init__(self):
        """Initialize ParentObject with all required components"""
        self.protocol_rx = ProtocolRX(self)
        self.protocol_tx = ProtocolTX()
        self.protocol_commands = ProtocolCommands(
            self, 
            self.PANEL_TYPE, 
            self.SETTINGS_PATH
        )
        
        # Status tracking
        self.latest_status = {}
        self.zone_status = {}
        self.zone_names = {}
        
        # Event handling
        self.log_event = LogEventDescription()
        self.LogEventFirstRequest = True
        self._dicEvents = {}
        self._dicEventDescriptions = {}
        self._MaxEventNumber = 0
        
        # Zone management
        self._Zones = Zones(self, self.SETTINGS_PATH, self.PANEL_TYPE)

    def TCPClients_OnNewBuffer(self, objectID: int, msg: bytes) -> None:
        """Process incoming TCP buffer data"""
        self.protocol_rx.ReceiveBuffer(msg)

    def PacketReceived(self, cmd: int, data: bytes) -> None:
        """Route received packets to appropriate handlers"""
        handlers = {
            self.CMD_PARTITION_STATUS: self._handle_partition_status,
            self.CMD_ZONE_STATUS: self._handle_zone_status,
            self.CMD_ZONE_NAME: self._handle_zone_name,
            self.CMD_LOG_EVENT: self._handle_log_event
        }
        handler = handlers.get(cmd)
        if handler:
            handler(data)

    def _handle_partition_status(self, data: bytes) -> None:
        """Process partition status updates"""
        status = [ord(char) for char in data]
        status_dict = {}
        
        for i, state in enumerate(status):
            if state == self.STATUS_END:
                break
                
            state_text = {
                self.STATUS_DISARMED: "disarmed",
                self.STATUS_ARMED[0]: "armed",
                self.STATUS_ARMED[1]: "armed",
                self.STATUS_ARMED_ALARM: "armed in alarm"
            }.get(state, f"unknown ({state})")
            
            status_dict[f"Area_{i + 1}"] = state_text
        
        self.latest_status = status_dict

    def _handle_zone_status(self, data: bytes) -> None:
        """Process zone status updates"""
        zone_base = ord(data[0]) * 16
        
        for byte in data[1:]:
            byte_val = ord(byte)
            
            # Process two zones per byte
            for offset in (0, 4):
                zone_num = zone_base + (offset//4 + 1)
                zone_state = (byte_val >> offset) & 0x0F
                
                status_data = {
                    "status": "alarm" if (zone_state & 1) else "normal",
                    "bypassed": bool(zone_state & 2)
                }
                
                self.zone_status[f"Zone_{zone_num}"] = status_data
            
            zone_base += 2

    def _handle_zone_name(self, data: bytes) -> None:
        """Process zone name updates"""
        zone_number = ord(data[0]) + 1
        zone_name = data[1:].strip('\x00')
        self.zone_names[f"Zone_{zone_number}"] = zone_name
        logger.debug(f"Zone {zone_number} name: {zone_name}")

    def _handle_log_event(self, data: bytes) -> None:
        """Process log event messages"""
        try:
            event_num = ord(data[0])
            self._MaxEventNumber = ord(data[1])
            event_type = ord(data[2]) & 127
            
            event_time = datetime(
                year=datetime.now().year,
                month=ord(data[5]),
                day=ord(data[6]),
                hour=ord(data[7]),
                minute=ord(data[8])
            )
            
            if event_type in self.EVENT_TYPE_SPECIAL:
                return
                
            event_data = ord(data[3])
            area_num = ord(data[4])
            description = self._build_event_description(
                event_type, 
                event_data, 
                area_num
            )
            
            self._dicEvents[event_num] = event_time
            self._dicEventDescriptions[event_num] = description
            
            logger.debug(
                f"Event {event_num} at {event_time}: {description}"
            )
            
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")

    def _build_event_description(self, event_type: int, 
                               event_data: int, 
                               area_num: int) -> str:
        """Build descriptive string for event types"""
        description = self.log_event.get_description(event_type)
        
        # Add zone information
        if event_type in self.EVENT_TYPE_ZONE:
            zone_num = event_data + 1
            zone = self._Zones.GetZone(zone_num)
            zone_info = zone.GetName() if zone else f"Zone {zone_num}"
            description = f"{description} - {zone_info}"
            
        # Add peripheral information
        elif event_type in self.EVENT_TYPE_PERIPHERAL:
            description = f"{description} - Peripheral #{event_data}"
            
        # Add user information
        elif event_type in self.EVENT_TYPE_USER:
            description = f"{description} - User #{event_data + 1}"
            
        # Add area information if applicable
        if area_num != 0:
            description = f"{description} - Area #{area_num + 1}"
            
        return description