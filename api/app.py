from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, time
import json
import math
import pytz  # To handle timezones

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",
            "https://luther-spots.vercel.app",
        ]
    }
})

# Load timezone based on the building location
LOCAL_TIMEZONE = pytz.timezone("America/Chicago")  # Adjust to your location

def load_college_data():
    with open('OpenClassrooms.json', 'r') as f:
        return json.load(f)

def haversine(lat1, lon1, lat2, lon2):
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        R = 6371  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return round(distance, 2)
    except Exception as e:
        print(f"Error in haversine calculation: {e}")
        return float('inf')

def get_slot_status(current_time, start_time_str, end_time_str):
    try:
        # Convert string times to datetime.time objects
        start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
        end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()

        # Convert all to minutes since midnight for easier comparison
        current_minutes = current_time.hour * 60 + current_time.minute
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute

        print(f"Slot: {start_time_str} - {end_time_str}, Current: {current_time}, "
              f"Start Minutes: {start_minutes}, End Minutes: {end_minutes}, Current Minutes: {current_minutes}")

        # Calculate slot status
        if start_minutes <= current_minutes <= end_minutes:
            return "available"
        elif 0 <= (start_minutes - current_minutes) <= 20:
            return "upcoming"
        else:
            return "unavailable"
    except Exception as e:
        print(f"Error in get_slot_status: {e}")
        return "unavailable"

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Open Classrooms API!"})

@app.route('/api/open-classrooms', methods=['GET', 'POST'])
def get_open_classrooms():
    user_lat = None
    user_lng = None

    if request.method == 'POST':
        user_location = request.get_json()
        if user_location is None:
            return jsonify({"error": "No data provided"}), 400

        user_lat = user_location.get('lat')
        user_lng = user_location.get('lng')

        if user_lat is None or user_lng is None:
            return jsonify({"error": "Invalid location data. 'lat' and 'lng' are required."}), 400

    data = load_college_data()

    # Get current time and day in local timezone
    now = datetime.now(LOCAL_TIMEZONE)
    current_time = now.time()
    current_day_abbrev = now.strftime("%a").upper()

    print(f"Current local time: {current_time}, Day: {current_day_abbrev}")

    day_mapping = {
        'MON': 'MON',
        'TUE': 'TUES',
        'WED': 'WED',
        'THU': 'THURS',
        'FRI': 'FRI',
        'SAT': 'SAT',
        'SUN': 'SUN'
    }

    current_day = day_mapping.get(current_day_abbrev)
    if not current_day:
        return jsonify({"error": "Invalid current day"}), 500

    status_priority = {"available": 3, "upcoming": 2, "unavailable": 1}
    building_info_list = []

    for feature in data.get('data', {}).get('features', []):
        try:
            building_name = feature['properties']['buildingName']
            building_code = feature['properties']['buildingCode']
            building_coords = feature['geometry']['coordinates']
            open_classroom_slots = feature['properties']['openClassroomSlots']
            rooms = {}
            building_status = "unavailable"

            for room in open_classroom_slots.get('data', []):
                room_number = room['roomNumber']
                schedule = room['Schedule']
                slots_with_status = []
                room_status = "unavailable"

                for slot in schedule:
                    if slot['Weekday'] != current_day:
                        continue

                    for time_slot in slot['Slots']:
                        start_time = time_slot['StartTime']
                        end_time = time_slot['EndTime']
                        status = get_slot_status(current_time, start_time, end_time)

                        slots_with_status.append({
                            "StartTime": start_time,
                            "EndTime": end_time,
                            "Status": status
                        })

                        if status_priority[status] > status_priority[room_status]:
                            room_status = status

                if slots_with_status:
                    rooms[room_number] = {
                        "slots": slots_with_status,
                        "room_status": room_status
                    }
                    if status_priority[room_status] > status_priority[building_status]:
                        building_status = room_status

            if rooms:
                building_info = {
                    "building": building_name,
                    "building_code": building_code,
                    "building_status": building_status,
                    "rooms": rooms,
                    "coords": building_coords
                }
                building_info_list.append(building_info)

        except Exception as e:
            print(f"Error processing building {feature.get('properties', {}).get('buildingName', 'unknown')}: {e}")

    return jsonify(building_info_list)

if __name__ == '__main__':
    app.run()
