import logging, time
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
from app.models.parent_object import ParentObject
from app.models.TCPClient import TCPClient
from app.models.protocol_enums import E_PrimaryKeypadFunctionMode

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Inizializza gli oggetti principali
parent_object = ParentObject()
tcp_client = TCPClient(parent_object)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/connect', methods=['POST'])
def connect():
    data = request.json
    server_ip = data.get('server_ip', '')
    server_port = data.get('server_port', 0)
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
    message = parent_object.protocol_commands.Send_CMD_3D_PrimaryKeyPadFunctionWithoutPIN(
        area, 
        E_PrimaryKeypadFunctionMode.ArmInAwayMode, 
        1
    )
    tcp_client.Send(message)
    # Request immediate status update
    status_message = parent_object.protocol_commands.Send_CMD_27_PartitionSnapShotRequest()
    tcp_client.Send(status_message)
    return jsonify({"status": "Arm command sent.", "areas": parent_object.latest_status}), 200

@app.route('/disarm', methods=['POST'])
def disarm():
    data = request.json
    area = data.get('area', 1)
    message = parent_object.protocol_commands.Send_CMD_3D_PrimaryKeyPadFunctionWithoutPIN(
        area, 
        E_PrimaryKeypadFunctionMode.Disarm, 
        1
    )
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
def get_last_events(count=185):
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
