import cv2
from ultralytics import YOLO
import pymysql
import datetime
import time
import threading
from contextlib import contextmanager
import signal
import sys
from flask import Flask, Response, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS  # Added for HTTP CORS
import argparse
import numpy as np

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Passenger Detection Script')
parser.add_argument('--bus_stop', type=str, default='Kivukoni', help='Bus stop name (e.g., Kivukoni, Gerezani, Morocco, Kimara)')
parser.add_argument('--sub_location', type=str, default='Kimara', help='Sub-location name (e.g., Kimara, Morocco, Gerezani)')
parser.add_argument('--flask_port', type=int, default=5000, help='Port for Flask server')
parser.add_argument('--camera_url', type=str, default='http://10.230.122.143:8080/video', help='IP camera stream URL (e.g., http://10.230.122.143:8080/video)')
args = parser.parse_args()

# Load YOLOv8 nano model
model = YOLO('yolov8n.pt')
model.fuse()

# MySQL config
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'people_counter_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Holidays dictionary for Tanzania (2025)
HOLIDAYS = {
    "2025-01-01": "New Year's Day",
    "2025-01-12": "Zanzibar Revolution Day",
    "2025-04-07": "Sheikh Abeid Amani Karume Day",
    "2025-04-18": "Good Friday",
    "2025-04-20": "Easter Sunday",
    "2025-04-21": "Easter Monday",
    "2025-04-26": "Union Day",
    "2025-05-01": "May Mosi",
    "2025-07-07": "Saba Saba",
    "2025-08-08": "Nane Nane",
    "2025-10-14": "Nyerere Day",
    "2025-12-09": "Independence Day",
    "2025-12-25": "Christmas Day",
    "2025-12-26": "Boxing Day",
    "2025-03-30": "Eid al-Fitr (estimated)",
    "2025-06-06": "Eid al-Adha (estimated)"
}

# Global variables
stop_event = threading.Event()
latest_frame = None
latest_data = {
    "passenger_count": 0,
    "weather": "Sunny",  # Placeholder: To be replaced with NodeMCU integration
    "time_value": "00:00:00",
    "day": "Unknown",
    "peak_hours": "No",
    "overcrowding": "Normal",
    "holidays": "No",
    "weekends": "No"
}
last_insert_time = None
passenger_threshold = 30
time_interval = 30 * 60  # 30 minutes in seconds

# Flask app with SocketIO
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for HTTP endpoints
socketio = SocketIO(app, cors_allowed_origins="*", path='socket.io')  # Match client SocketIO path

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        yield conn
    except pymysql.MySQLError as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

def initialize_camera():
    # List of possible stream URLs to try, starting with user-provided URL
    stream_urls = [
        args.camera_url,  # Primary URL from command-line argument
        f'http://{args.camera_url.split("://")[1].split("/")[0]}/mjpg',  # Alternative MJPEG path
        f'http://{args.camera_url.split("://")[1].split("/")[0]}/stream.mjpg',  # Common MJPEG path
        f'rtsp://{args.camera_url.split("://")[1].split("/")[0]}/stream1'  # RTSP stream (if supported)
    ]
    max_retries = 5
    retry_delay = 3  # seconds
    for url in stream_urls:
        print(f"Trying stream URL: {url}")
        for attempt in range(max_retries):
            cap = cv2.VideoCapture(url)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                cap.set(cv2.CAP_PROP_FPS, 30)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                print(f"IP Camera initialized at {url} on attempt {attempt + 1}")
                return cap, 0  # Return cap and dummy index (0) for IP cameras
            print(f"Attempt {attempt + 1} failed to connect to IP camera at {url}")
            cap.release()
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    print(f"Error: Could not connect to IP camera at any of the URLs: {stream_urls} after {max_retries} attempts")
    return None, -1

def gen_frames():
    global latest_frame
    while not stop_event.is_set():
        if latest_frame is not None:
            ret, buffer = cv2.imencode('.jpg', latest_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.033)

@app.route('/video_feed')
def video_feed():
    print("Received request for /video_feed")
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/data')
def get_data():
    global latest_data
    print("Received request for /data")
    try:
        return jsonify(latest_data)
    except Exception as e:
        print(f"Error in /data endpoint: {e}")
        return jsonify({
            "passenger_count": 0,
            "weather": "Unknown",
            "time_value": "00:00:00",
            "day": "Unknown",
            "peak_hours": "No",
            "overcrowding": "Normal",
            "holidays": "No",
            "weekends": "No"
        }), 500

@socketio.on('connect')
def handle_connect():
    print("Client connected to SocketIO")

@socketio.on('join')
def on_join(room):
    print(f"Client joined room: {room}")
    socketio.emit('update_data', latest_data, room=room)

def broadcast_data(data):
    namespace = f"/{args.bus_stop}/{args.sub_location}"
    print(f"Emitting data to namespace {namespace}: {data}")
    socketio.emit('update_data', data, namespace=namespace)

def detect_and_count():
    global latest_frame, latest_data, last_insert_time
    cap, camera_index = initialize_camera()
    if cap is None:
        return

    frame_skip = 3
    frame_counter = 0
    retry_count = 0
    max_retries = 5
    cached_day = None
    cached_date = None
    last_minute = -1

    try:
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print(f"Warning: Frame failed on {camera_index}.")
                retry_count += 1
                if retry_count >= max_retries:
                    cap.release()
                    cap, camera_index = initialize_camera()
                    if cap is None:
                        break
                    retry_count = 0
                time.sleep(0.1)
                continue

            retry_count = 0
            frame_counter += 1
            if frame_counter % frame_skip != 0:
                continue

            try:
                results = model.predict(frame, classes=0, conf=0.5, verbose=False, imgsz=640)
                passenger_count = len(results[0].boxes)
                display_frame = frame.copy()

                if len(results[0].boxes) > 0:
                    boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
                    for box in boxes:
                        cv2.rectangle(display_frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)

                cv2.putText(display_frame, f'Passengers: {passenger_count}', (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                latest_frame = display_frame

                now = datetime.datetime.now()
                current_minute = now.minute


                if current_minute != last_minute:
                    cached_day = now.strftime('%A')
                    cached_date = now.date()
                    last_minute = current_minute

                time_value = now.time().strftime('%H:%M:%S')
                is_weekday = now.weekday() < 5
                peak_hours = 1 if is_weekday and (6 <= now.hour < 9 or 16 <= now.hour < 20) else 0
                weekends = 1 if now.weekday() >= 5 else 0
                date_str = cached_date.strftime('%Y-%m-%d')
                holidays_val = 1 if date_str in HOLIDAYS else 0
                # Placeholder for NodeMCU weather integration
                # TODO: Replace with NodeMCU API call, e.g., weather = requests.get('http://nodemcu-ip/weather').json()['weather']
                weather = "Sunny"

                new_data = {
                    "passenger_count": passenger_count,
                    "weather": weather,
                    "time_value": time_value,
                    "day": cached_day,
                    "peak_hours": "Yes" if peak_hours else "No",
                    "overcrowding": "High" if passenger_count > passenger_threshold else "Normal",
                    "holidays": "Yes" if holidays_val else "No",
                    "weekends": "Yes" if weekends else "No"
                }

                if abs(new_data["passenger_count"] - latest_data["passenger_count"]) > 2 or \
                   new_data["weather"] != latest_data["weather"]:
                    latest_data = new_data
                    threading.Thread(target=broadcast_data, args=(latest_data.copy(),), daemon=True).start()
                else:
                    latest_data.update(new_data)

                current_time = time.time()
                should_insert = False
                if passenger_count > passenger_threshold:
                    should_insert = True
                elif last_insert_time is None or (current_time - last_insert_time >= time_interval):
                    should_insert = True

                if should_insert:
                    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
                    bus_stop = args.bus_stop
                    sub_location = args.sub_location

                    def insert_data():
                        try:
                            with get_db_connection() as conn:
                                with conn.cursor() as cursor:
                                    cursor.execute(
                                        "INSERT INTO counts (timestamp, passengers, day, date, weather, time_value, peak_hours, weekends, holidays, bus_stop, sub_location) "
                                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                        (timestamp, passenger_count, cached_day, cached_date, weather, time_value, peak_hours, weekends, holidays_val, bus_stop, sub_location)
                                    )
                                conn.commit()
                            print(f"Inserted data: {passenger_count} passengers at {timestamp} for {bus_stop} - {sub_location}")
                        except Exception as e:
                            print(f"Database insert error: {e}")

                    threading.Thread(target=insert_data, daemon=True).start()
                    last_insert_time = current_time

                if frame_counter % 2 == 0:
                    cv2.imshow('IP Camera - Passenger Counter', display_frame)

            except Exception as e:
                print(f"Error: {e}")

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                stop_event.set()
                break

    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        print("Cleanup complete.")

def signal_handler(sig, frame):
    print("Interrupt received. Stopping...")
    stop_event.set()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Start Flask and SocketIO
flask_thread = threading.Thread(target=lambda: socketio.run(app, host='0.0.0.0', port=args.flask_port, debug=True, use_reloader=False))
flask_thread.daemon = True
flask_thread.start()

# Start detection
detection_thread = threading.Thread(target=detect_and_count)
detection_thread.start()
detection_thread.join()
flask_thread.join()
print("All threads terminated.")