from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import math

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",
            "https://luther-spots.vercel.app",
        ]
    }
})

def load_college_data():
    with open('OpenClassrooms.json', 'r') as f:
        return json.load(f)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_slot_status(current_time, start_time_str, end_time_str):
    # Convert string times to datetime.time objects
    start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
    end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()
    
    # Convert all to minutes since midnight for easier comparison
    current_minutes = current_time.hour * 60 + current_time.minute
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    
    # Calculate minutes until start
    minutes_until_start = start_minutes - current_minutes
    
    # Output for debugging
    print(f"Current time (minutes): {current_minutes}")
    print(f"Start time (minutes): {start_minutes}")
    print(f"Minutes until start: {minutes_until_start}")
    
    # If current time is before start time and within 20 minutes
    if 0 <= minutes_until_start <= 20:
        return "upcoming"
    # If current time is between start and end time
    elif start_minutes <= current_minutes <= end_minutes:
        return "available"
    # Otherwise unavailable
    else:
        return "unavailable"

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Open Classrooms API!"})

@app.route('/api/open-classrooms', methods=['GET', 'POST'])
def get_open_classrooms():
    user_lat = 0
    user_lng = 0

    if request.method == 'POST':
        user_location = request.get_json()
        if user_location is None:
            return jsonify({"error": "No data provided"}), 400

        user_lat = user_location.get('lat')
        user_lng = user_location.get('lng')

        if user_lat is None or user_lng is None:
            return jsonify({"error": "Invalid location data. 'lat' and 'lng' are required."}), 400
    
    data = load_college_data()
    current_time = datetime.now().time()
    current_day_abbrev = datetime.now().strftime("%a").upper()
    
    print(f"Current time: {current_time}")
    print(f"Current day: {current_day_abbrev}")
    
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

    status_priority = {
        "available": 3,
        "upcoming": 2,
        "unavailable": 1
    }

    building_info_list = []

    for feature in data.get('data', {}).get('features', []):
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
                    
                    print(f"Room {room_number} slot {start_time}-{end_time}: {status}")
                    
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
                "coords": building_coords,
                "distance": haversine(user_lat, user_lng, building_coords[1], building_coords[0]) if user_lat != 0 and user_lng != 0 else 0
            }
            building_info_list.append(building_info)

    if user_lat != 0 and user_lng != 0:
        building_info_list = sorted(building_info_list, key=lambda x: x['distance'])

    return jsonify(building_info_list)

if __name__ == '__main__':
    app.run()