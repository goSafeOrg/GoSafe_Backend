from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from flask_cors import CORS
import eventlet

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize SocketIO with additional configuration
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
)

@app.route('/socket_test')
def test():
    return "SocketIO server is running."

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connection_response', {'status': 'connected', 'sid': request.sid})


@socketio.on('boom')
def handle_message(data):
    try:
        device_id = data.get('roomId')
        
        if device_id :
            print(f"Broadcasting message to room {device_id}: 'hi")
            emit('boom_res', {
                'message': 'bakayaro',
              
            }, room=device_id)
    except Exception as e:
        print(f"Error in handle_message: {str(e)}")
        emit('error', {'error': str(e)})

pending_requests = {}

@app.route('/')
def index():
    return "SocketIO Server Running"

@socketio.on('request_approval')
def handle_request_approval(data):
    # Generate a unique ID for the request
    request_id = data.get('request_id')
    user_id = data.get('user_id')

    # Store the request in pending_requests
    pending_requests[request_id] = user_id
    
    # Notify the user to approve or deny the request
    emit('notify_user', {'message': 'New approval request!', 'request_id': request_id}, room=user_id)

@socketio.on('approve_request')
def handle_approve_request(data):
    request_id = data.get('request_id')
    
    # Check if the request is valid
    if request_id in pending_requests:
        user_id = pending_requests.pop(request_id)
        
        # Notify the original requestor that approval was granted
        emit('approval_event', {'approved': True}, room=user_id)
    else:
        emit('approval_event', {'approved': False}, room=user_id)

@socketio.on('deny_request')
def handle_deny_request(data):
    request_id = data.get('request_id')
    
    # Check if the request is valid
    if request_id in pending_requests:
        user_id = pending_requests.pop(request_id)
        
        # Notify the original requestor that approval was denied
        emit('approval_event', {'approved': False}, room=user_id)
@socketio.on('joinRoom')
def handle_join_room(data):
    try:
        room_id = data.get('roomId')
        print(data)
        if room_id:
            join_room(room_id)
            print(f'Device {request.sid} joined room {room_id}')
            emit('room_joined', {
                'status': 'success',
                'room': room_id,
                'sid': request.sid
            }, room=room_id)
    except Exception as e:
        print(f"Error in join_room: {str(e)}")
        emit('error', {'error': str(e)})

@socketio.on('message')
def handle_message(data):
    try:
        device_id = data.get('deviceId')
        message = data.get('message')
        if device_id and message:
            print(f"Broadcasting message to room {device_id}: {message}")
            emit('message_response', {
                'message': message,
                'from': request.sid,
                'deviceId': device_id
            }, room=device_id)
    except Exception as e:
        print(f"Error in handle_message: {str(e)}")
        emit('error', {'error': str(e)})

@socketio.on('requestLocation')
def handle_request_location(data):
    device_id = data.get('deviceId')
    print(f'Requesting location for device: {device_id}')

    # Send the location back to the requesting client
    emit('GetlocationUpdate', room=device_id)

@socketio.on('locationUpdate')
def handle_update_location(data):
    try:
        loc = data.get('loc')
        device_id = data.get('room')
        
        if not loc or not device_id:
            emit('error', {'message': 'Missing location or room information'})
            return
        
        print(f"Sending location for device: {device_id}")
        emit('locationDetails', {'loc': loc}, room=device_id)
    except Exception as e:
        print(f"Error in handle_update_location: {str(e)}")
        emit('error', {'message': str(e)})


@socketio.on('requestStatus')
def handle_request_Status(data):
    status = data.get('status')
    device_id = data.get('deviceId')
    print(f'Giving Access')
  
    emit('getStatus', {"status":status},room=device_id)
    print(status," Given")

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

if __name__ == '__main__':
    # Use eventlet's wsgi server
    # eventlet.monkey_patch()
    socketio.run(
        app,
        host='0.0.0.0',  # Important: Listen on all interfaces
        port=5005,
        debug=True,
        # use_reloader=False  # Disable reloader when using eventlet
    )