import logging, time
from flask import Flask, request, jsonify, send_from_directory
from app.models.TCPClient import TCPClient
from app.models.ProtocolRX import ProtocolRX
from app.models.ProtocolTX import ProtocolTX
from app.models.ProtocolCommands import ProtocolCommands
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)


SETTINGS_PATH = "settings_path"

class LogEventDescription:
    def __init__(self):
        self._event_descriptions = {}
        self.load_event_descriptions()

    def load_event_descriptions(self):
        self._event_descriptions = {
            0: "Allarme",
            1: "Ripristino Allarme",
            2: "Bypass",
            3: "Ripristino Bypass", 
            4: "Tamper",
            5: "Ripristino Tamper",
            6: "Problema",
            7: "Ripristino Problema",
            8: "Batteria TX Scarica",
            9: "Ripristino TX Batteria Scarica",
            10: "Zona Persa",
            11: "Rispristino Zona Persa",
            12: "Inizio Tempo di Attraversamento",
            13: "Supervisione Sprinkler",
            14: "Ripristinata Supervisione Sprinkler",
            15: "Zona Inattiva",
            16: "Ripristino Zona Inattiva",
            17: "Evento di Espansione Speciale",
            18: "Coercizione",
            19: "Attivazione Manuale",
            20: "Ausiliario 2 Panico",
            21: "Silenzioso Panico/ B - Allarme",
            22: "Panico",
            23: "Tamper Tastiera",
            24: "Box di Controllo Tamper",
            25: "Ripristino Box di Controllo Tamper",
            26: "Alimentazione Primaria",
            27: "Ripristino Alimentazione Primaria",
            28: "Batteria Scarica",
            29: "Ripristino Batteria Scarica",
            30: "Sovracorrente",
            31: "Ripristino Sovracorrente",
            32: "Tamper Sirena",
            33: "Ripristino Tamper Sirena",
            34: "Guasto Telefonico",
            35: "Ripristino Guasto Telefonico",
            36: "Problemi all'Expander",
            37: "Ripristino Problemi all'Expander",
            38: "Errore di Comunicazione",
            39: "Log Eventi Pieno",
            40: "Disinserimento",
            41: "Inserimento",
            42: "Errore di Uscita",
            43: "Inserimento Recente",
            44: "Auto Test",
            45: "Entrata in Programmazione",
            46: "Termine Programmazione",
            47: "Inizio Download",
            48: "Download Terminato",
            49: "Annulla",
            50: "Guasto Terra",
            51: "Ripristino Guasto Terra",
            52: "Test Manuale",
            53: "Inserimento con Zone Bypassate",
            54: "Inizia l'Ascolto in",
            55: "Tecnico in Programmazione",
            56: "Tecnico fuori Programmazione",
            57: "Controlo Alimentazione",
            58: "Anticipo di Apertura",
            59: "Ritardo di Chiusura",
            60: "Blocco RF",
            61: "Ripristino Blocco RF",
            62: "Zona Clean-Me",
            63: "Ripristino Zona Clean-Me",
            64: "Verificata Intrusione",
            65: "Ripristiono Verificata Intrusione",
            66: "Verificato Incendio",
            67: "Ripristino Verificato Incendio",
            68: "Disinserimento Dopo l'Allarme"
        }

    def get_description(self, event_code):
        return self._event_descriptions.get(event_code, f"Unknown Event {event_code}")

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

class ParentObject:
    def __init__(self):
        self.protocol_rx = ProtocolRX(self)
        self.protocol_tx = ProtocolTX()
        self.protocol_commands = ProtocolCommands(self, "NX8", SETTINGS_PATH)
        self.tcp_client = TCPClient(self)
        self.latest_status = {}
        self.zone_status = {}  # Add zone status tracking
        self.zone_names = {}  # Add zone names dictionary
        self.log_event = LogEventDescription()
        self.LogEventFirstRequest = True
        self._dicEvents = {}
        self._dicEventDescriptions = {}  # Aggiungi dizionario per le descrizioni
        self._MaxEventNumber = 0
        self._Zones = Zones(self, SETTINGS_PATH, "NX8") # Will be initialized with Zones class if needed
        logger.debug("ParentObject initialized")

    def TCPClients_OnNewBuffer(self, objectID, msg):
        self.protocol_rx.ReceiveBuffer(msg)

    def PacketReceived(self, cmd, data):
        decoded_data = data
        if cmd == 7:  # Assuming 7 is the command for partition snapshot
            self.print_partition_status(decoded_data)
        elif cmd == 5:  # Zone snapshot
            self.print_zone_status(decoded_data)
        elif cmd == 3:  # Zone name
            self.handle_zone_name(decoded_data)
        elif cmd == 10:
            self.RX_PacketReceived_0A_LogEventMessage(decoded_data)

    def RX_PacketReceived_0A_LogEventMessage(self, Data):
        try:
            EventNumber = ord(Data[0])
            self._MaxEventNumber = ord(Data[1])
            EventType = ord(Data[2]) & 127  # KEYCODE_MEDIA_PAUSE = 127
            
            # if self.LogEventFirstRequest:
            #     self.LogEventFirstRequest = False
            #     return

            EventDateTime = datetime(
                year=datetime.now().year,
                month=ord(Data[5]),
                day=ord(Data[6]),
                hour=ord(Data[7]),
                minute=ord(Data[8])
            )

            # Check for duplicate events
            # EventExist = (EventNumber in self._dicEvents and 
            #             self._dicEvents[EventNumber] == EventDateTime)
            # if EventExist:
            #     return

            # Format timestamp for better readability
            timestamp = EventDateTime.strftime("%Y-%m-%d %H:%M:%S")

            if not (69 <= EventType <= 117):
                EventB05 = ord(Data[3])
                EventB06 = ord(Data[4])
                EventDescription = self.log_event.get_description(EventType)

                # Zone events with fixed numbering
                if (0 <= EventType <= 16) or (62 <= EventType <= 67):
                    ZoneNumber = EventB05 + 1  # The zone number is 1-based
                    Zone = self._Zones.GetZone(ZoneNumber)
                    if Zone:
                        zone_name = Zone.GetName()
                        EventDescription = f"{EventDescription} - {zone_name}"
                    else:
                        EventDescription = f"{EventDescription} - Zone {ZoneNumber}"

                    logger.debug(f"Event {EventNumber} at {timestamp}: {EventDescription}")

                # Peripheral events
                elif (24 <= EventType <= 33) or EventType in (36, 37, 118):
                    EventDescription = f"{EventDescription} - Periferica n.{EventB05}"

                # User events
                elif ((40 <= EventType <= 43) or 
                    EventType in (49, 53, 58, 68) or 
                    (119 <= EventType <= 122) or 
                    EventType == 126):
                    EventDescription = f"{EventDescription} - Utente n.{EventB05 + 1}"

                # Area events
                if ((0 <= EventType <= 16) or 
                    (18 <= EventType <= 20) or 
                    EventType in (22, 23) or 
                    (40 <= EventType <= 43) or 
                    EventType in (49, 53, 58, 59) or 
                    (62 <= EventType <= 68) or 
                    (120 <= EventType <= 122) or 
                    EventType == 125):
                    EventDescription = f"{EventDescription} - Area n.{EventB06 + 1}"

                self._dicEvents[EventNumber] = EventDateTime
                self._dicEventDescriptions[EventNumber] = EventDescription  # Salva la descrizione
                logger.debug(f"Event {EventNumber} at {EventDateTime}: {EventDescription}")
                
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}")


    def print_partition_status(self, data):
        status = [ord(char) for char in data]
        status_dict = {}
        area_updates = {}
        
        for i, state in enumerate(status):
            # print(f"Area {i + 1}: {state}")
            if state == 3:
                state_text = "disarmed"
            elif state == 71 or state == 7:
                state_text = "armed"
            elif state == 135:
                state_text = "armed in alarm"
            elif state == 2:
                break
            else:
                state_text = f"unknown ({state})"
            status_dict[f"Area_{i + 1}"] = state_text
            area_updates[i + 1] = state_text
        
        self.latest_status = status_dict
        
        # Print formatted area status
        # print("\n=== Area Status Update ===")
        # for area_num in sorted(area_updates.keys()):
        #     status = area_updates[area_num]
        #     status_symbol = "🔴" if status == "armed" else "🟢"
        #     print(f"Area {area_num:2d}: {status_symbol} {status}")
        # print("======================\n")

    def print_zone_status(self, data):
        zone_base = ord(data[0]) * 16
        zone_updates = {}
        for byte in data[1:]:
            byte_val = ord(byte)
            # Process first zone in byte
            zone_num = zone_base + 1
            zone_state = byte_val & 0x0F
            is_bypassed = (zone_state & 2) == 2  # Check bypass bit
            status = "alarm" if (zone_state & 1) else "normal"
            self.zone_status[f"Zone_{zone_num}"] = {
                "status": status,
                "bypassed": is_bypassed
            }
            zone_updates[zone_num] = {"status": status, "bypassed": is_bypassed}
            
            # Process second zone in byte
            zone_num = zone_base + 2
            zone_state = (byte_val >> 4) & 0x0F
            is_bypassed = (zone_state & 2) == 2  # Check bypass bit
            status = "alarm" if (zone_state & 1) else "normal"
            self.zone_status[f"Zone_{zone_num}"] = {
                "status": status,
                "bypassed": is_bypassed
            }
            zone_updates[zone_num] = {"status": status, "bypassed": is_bypassed}
            
            zone_base += 2

    def handle_zone_name(self, data):
        zone_number = ord(data[0]) + 1
        zone_name = data[1:].strip('\x00')  # Remove null characters
        self.zone_names[f"Zone_{zone_number}"] = zone_name
        print(f"Zone {zone_number} name: {zone_name}")

    def SendNextCommand(self):
        next_command = self.protocol_commands.GetNextCommand()
        if (next_command):
            self.tcp_client.Send(next_command)

    def request_events(self):
        """Request the last event from the system"""
        message = self.protocol_commands.Send_CMD_2A_LogEventRequest(1)
        self.tcp_client.Send(message)

parent_object = ParentObject()
tcp_client = TCPClient(parent_object)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/connect', methods=['POST'])
def connect():
    data = request.json
    server_ip = data.get('server_ip', '192.168.0.50')
    server_port = data.get('server_port', 3434)
    object_id = data.get('object_id', 1)
    timeout = data.get('timeout', 5)
    
    tcp_client.Init(server_ip, server_port, object_id)
    
    if tcp_client.Open(timeout):
        # Request zone names after successful connection
        # for i in range(1, 17):  # Request names for first 16 zones
        #     message = parent_object.protocol_commands.Send_CMD_23_ZonaNameRequest(i)
        #     tcp_client.Send(message)

        return jsonify({"status": "Connection established successfully."}), 200
    else:
        return jsonify({"status": "Failed to establish connection."}), 500

@app.route('/disconnect', methods=['POST'])
def disconnect():
    try:
        tcp_client.Close()
        return jsonify({"status": "Disconnected successfully."}), 200
    except Exception as e:
        return jsonify({"status": "Error disconnecting", "error": str(e)}), 500

@app.route('/arm', methods=['POST'])
def arm():
    data = request.json
    area = data.get('area', 1)
    message = parent_object.protocol_commands.Send_CMD_3D_PrimaryKeyPadFunctionWithoutPIN(area, ProtocolCommands.E_PrimaryKeypadFunctionMode.ArmInAwayMode, 1)
    tcp_client.Send(message)
    # Request immediate status update
    status_message = parent_object.protocol_commands.Send_CMD_27_PartitionSnapShotRequest()
    tcp_client.Send(status_message)
    return jsonify({"status": "Arm command sent.", "areas": parent_object.latest_status}), 200

@app.route('/disarm', methods=['POST'])
def disarm():
    data = request.json
    area = data.get('area', 1)
    message = parent_object.protocol_commands.Send_CMD_3D_PrimaryKeyPadFunctionWithoutPIN(area, ProtocolCommands.E_PrimaryKeypadFunctionMode.Disarm, 1)
    tcp_client.Send(message)
    # Request immediate status update
    status_message = parent_object.protocol_commands.Send_CMD_27_PartitionSnapShotRequest()
    tcp_client.Send(status_message)
    return jsonify({"status": "Disarm command sent.", "areas": parent_object.latest_status}), 200

@app.route('/status', methods=['GET'])
def status():
    try:
        # Request partition status
        message = parent_object.protocol_commands.Send_CMD_27_PartitionSnapShotRequest()
        tcp_client.Send(message)
        
        # Request zone status for first 16 zones
        zone_message = parent_object.protocol_commands.Send_CMD_25_ZonaSnapShotRequest(1)
        tcp_client.Send(zone_message)
        
        return jsonify({
            "status": "Status request sent.",
            "areas": parent_object.latest_status,
            "zones": parent_object.zone_status,
            "zone_names": parent_object.zone_names  # Add zone names to response
        }), 200
    except Exception as e:
        return jsonify({
            "status": "Error getting status",
            "error": str(e)
        }), 500

@app.route('/events', methods=['GET'])
def get_last_events(count=184):
    try:
        parent_object.protocol_rx.ResetBuffer()  # Reset buffer before requesting events
        
        # Richiedi gli ultimi eventi uno alla volta con un piccolo delay
        for i in range(count):
            parent_object.protocol_rx.ClearBuffer()  # Clear buffer before each request
            message = parent_object.protocol_commands.Send_CMD_2A_LogEventRequest(i+1)
            tcp_client.Send(message)
            time.sleep(0.1)  # Increase delay between requests
        
        time.sleep(1)  # Wait for all responses
        
        # Ordina gli eventi per data/ora in ordine decrescente
        sorted_events = sorted(
            [
                (num, dt, parent_object._dicEventDescriptions.get(num, "Evento sconosciuto"))
                for num, dt in parent_object._dicEvents.items()
                if isinstance(dt, datetime)
            ],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Prendi solo gli eventi più recenti
        events_dict = {
            str(num): {
                "datetime": dt.isoformat(),
                "description": desc
            }
            for num, dt, desc in sorted_events[:184]  # Limit to 50 most recent events
        }
        
        logger.debug(f"Sending {len(events_dict)} sorted events")
        
        return jsonify({
            "status": "success",
            "events": events_dict,
            "count": len(events_dict)
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving events: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    command = data.get('command', '')
    command_data = data.get('data', '')
    
    try:
        if command == '0x23':  # Zone name request
            message = parent_object.protocol_commands.Send_CMD_23_ZonaNameRequest(int(command_data))
        elif command == '0x42':  # Zone bypass command
            # Convert zone number to int and subtract 1 for 0-based indexing
            zone_num = int(command_data)
            message = parent_object.protocol_commands.Send_CMD_3F_ZoneByPassToggle(zone_num)
            logger.debug(f"Sending bypass command for zone {zone_num + 1}")
        elif command == '0x43':  # Zone include command
            # Convert zone number to int and subtract 1 for 0-based indexing
            zone_num = int(command_data)
            message = parent_object.protocol_commands.Send_CMD_3F_ZoneByPassToggle(zone_num)
            logger.debug(f"Sending include command for zone {zone_num + 1}")
        else:
            message = parent_object.protocol_tx.Output(command, command_data)
        
        tcp_client.Send(message)
        
        # Request immediate status update after bypass/include
        if command in ['0x42', '0x43']:
            status_message = parent_object.protocol_commands.Send_CMD_25_ZonaSnapShotRequest(1)
            tcp_client.Send(status_message)
        
        return jsonify({
            "status": "Command sent successfully",
            "command": command,
            "zone": command_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending command {command}: {str(e)}")
        return jsonify({
            "status": "Error sending command",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    # app.run(debug=True)
