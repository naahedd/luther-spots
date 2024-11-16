from flask import Flask, jsonify, request
from datetime import datetime
import json
import math

app = Flask(__name__)

# Load JSON data for your college
def load_college_data():
    with open('OpenClassrooms.json', 'r') as f:
        return json.load(f)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lat2 - lon2)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c 

def get_slot_status(current_time, start_time_str, end_time_str):
    start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
    end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()

    time_until = (datetime.combine(datetime.today(), start_time) - datetime.combine(datetime.today(), current_time)).total_seconds() / 60

    if start_time <= current_time <= end_time:
        return "available"
    elif 0 < time_until < 20:
        return "upcoming"
    else:
        return "unavailable"

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
    current_day_abbrev = datetime.now().strftime("%a").upper()  # E.g., 'MON', 'TUE', etc.

    # Map strftime abbreviations to those used in your JSON data
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

    print(f"Current day: {current_day}")  # Debugging: Print current day

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
        
        open_classroom_slots = feature['properties']['openClassroomSlots']
        rooms = {}
        building_status = "unavailable"  # Default building status

        for room in open_classroom_slots.get('data', []):
            room_number = room['roomNumber']
            schedule = room['Schedule']
            slots_with_status = []
            room_status = "unavailable"  # Default room status

            print(f"Processing room: {room_number} in building {building_code}")  # Debugging

            # Process time slots for the current day only
            for slot in schedule:
                print(f"Slot Weekday: {slot['Weekday']}")  # Debugging
                if slot['Weekday'] != current_day:
                    print(f"Skipping slot for day: {slot['Weekday']}")  # Debugging
                    continue  # Skip slots that are not for the current day
                for time_slot in slot['Slots']:
                    start_time = time_slot['StartTime']
                    end_time = time_slot['EndTime']
                    status = get_slot_status(current_time, start_time, end_time)

                    # Update room_status based on slot status
                    if status_priority[status] > status_priority[room_status]:
                        room_status = status

                    # Add all slots to the list
                    print(f"Adding slot for room {room_number}: {start_time} - {end_time} with status {status}")  # Debugging
                    slots_with_status.append({
                        "StartTime": start_time,
                        "EndTime": end_time,
                        "Status": status
                    })

            # Only add the room if it has slots for the current day
            if slots_with_status:
                rooms[room_number] = {"slots": slots_with_status, "room_status": room_status}

                # Update building_status based on room_status
                if status_priority[room_status] > status_priority[building_status]:
                    building_status = room_status

        building_info = {
            "building": building_name,
            "building_code": building_code,
            "building_status": building_status,  # Could be "available", "upcoming", or "unavailable"
            "rooms": rooms,
            "coords": building_coords,
            "distance": haversine(user_lat, user_lng, building_coords[1], building_coords[0]) if user_lat != 0 and user_lng != 0 else 0
        }

        # Add the building to the response if it has rooms with slots for the current day
        if rooms:
            building_info_list.append(building_info)
    
    if not building_info_list:
        print('No buildings with available slots found.')  # Debugging

    # Sort buildings by distance if user location is provided
    if user_lat != 0 and user_lng != 0:
        building_info_list = sorted(building_info_list, key=lambda x: x['distance'])

    print('Building info list:', building_info_list)  # Debugging
    return jsonify(building_info_list)

if __name__ == '__main__':
    app = app