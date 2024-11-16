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
    R = 6371  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_slot_status(current_time, start_time_str, end_time_str):
    """
    Determines the status of a classroom slot based on the current time.
    
    Args:
        current_time (time): The current time as a time object
        start_time_str (str): Start time in "HH:MM:SS" format
        end_time_str (str): End time in "HH:MM:SS" format
        
    Returns:
        str: Status of the slot ("available", "upcoming", or "unavailable")
    """
    # Convert string times to time objects
    start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
    end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()
    
    # Calculate minutes until start time
    current_datetime = datetime.combine(datetime.today(), current_time)
    start_datetime = datetime.combine(datetime.today(), start_time)
    
    time_until = (start_datetime - current_datetime).total_seconds() / 60
    
    print(f"Time comparison for slot {start_time_str}-{end_time_str}:")
    print(f"Current time: {current_time}")
    print(f"Start time: {start_time}")
    print(f"End time: {end_time}")
    print(f"Minutes until start: {time_until}")
    
    # If current time is between start and end time
    if start_time <= current_time <= end_time:
        print("Status: available (current time is within slot)")
        return "available"
    # If slot starts within next 20 minutes
    elif time_until > 0 and time_until <= 20:
        print("Status: upcoming (starts within 20 minutes)")
        return "upcoming"
    # Otherwise unavailable
    else:
        print("Status: unavailable")
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
    
    # Load data from your college JSON file
    data = load_college_data()
    current_time = datetime.now().time()
    
    # Add debugging output for current time
    print(f"\nCurrent server time: {current_time}")
    
    current_day_abbrev = datetime.now().strftime("%a").upper()
    current_day = {
        'MON': 'MON',
        'TUE': 'TUES',
        'WED': 'WED',
        'THU': 'THURS',
        'FRI': 'FRI',
        'SAT': 'SAT',
        'SUN': 'SUN'
    }.get(current_day_abbrev)

    if not current_day:
        return jsonify({"error": "Invalid current day"}), 500

    print(f"Current day: {current_day}")

    # Define status priorities
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
        
        print(f"\nProcessing building: {building_name}")
        
        open_classroom_slots = feature['properties']['openClassroomSlots']
        rooms = {}
        building_status = "unavailable"

        for room in open_classroom_slots.get('data', []):
            room_number = room['roomNumber']
            schedule = room['Schedule']
            slots_with_status = []
            room_status = "unavailable"

            print(f"\nRoom {room_number}:")
            
            for slot in schedule:
                if slot['Weekday'] != current_day:
                    continue
                    
                for time_slot in slot['Slots']:
                    start_time = time_slot['StartTime']
                    end_time = time_slot['EndTime']
                    
                    # Get status for this time slot
                    status = get_slot_status(current_time, start_time, end_time)
                    
                    slots_with_status.append({
                        "StartTime": start_time,
                        "EndTime": end_time,
                        "Status": status
                    })
                    
                    # Update room status based on highest priority status found
                    if status_priority[status] > status_priority[room_status]:
                        room_status = status
                        print(f"Updated room status to: {room_status}")

            if slots_with_status:
                rooms[room_number] = {
                    "slots": slots_with_status,
                    "room_status": room_status
                }
                
                # Update building status based on highest priority room status
                if status_priority[room_status] > status_priority[building_status]:
                    building_status = room_status
                    print(f"Updated building status to: {building_status}")

        building_info = {
            "building": building_name,
            "building_code": building_code,
            "building_status": building_status,
            "rooms": rooms,
            "coords": building_coords,
            "distance": haversine(user_lat, user_lng, building_coords[1], building_coords[0]) if user_lat != 0 and user_lng != 0 else 0
        }

        if rooms:
            building_info_list.append(building_info)
            print(f"Added building {building_name} with status {building_status}")

    # Sort buildings by distance if user location is provided
    if user_lat != 0 and user_lng != 0:
        building_info_list = sorted(building_info_list, key=lambda x: x['distance'])

    return jsonify(building_info_list)

if __name__ == '__main__':
    app.run()