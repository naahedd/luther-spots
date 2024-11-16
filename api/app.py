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
    # Convert coordinates to floats to ensure proper calculation
    lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    
    R = 6371  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    # Return distance rounded to 2 decimal places for consistency
    return round(distance, 2)

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

        # Validate coordinates
        if user_lat is None or user_lng is None:
            return jsonify({"error": "Invalid location data. 'lat' and 'lng' are required."}), 400
        
        try:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
            if not (-90 <= user_lat <= 90) or not (-180 <= user_lng <= 180):
                return jsonify({"error": "Coordinates out of valid range"}), 400
        except ValueError:
            return jsonify({"error": "Coordinates must be valid numbers"}), 400

    data = load_college_data()
    building_info_list = []

    for feature in data.get('data', {}).get('features', []):
        building_coords = feature['geometry']['coordinates']
        
        # Calculate distance only if user coordinates are provided
        distance = None
        if user_lat is not None and user_lng is not None:
            try:
                # Note that coordinates in GeoJSON are [longitude, latitude]
                distance = haversine(user_lat, user_lng, building_coords[1], building_coords[0])
            except Exception as e:
                print(f"Error calculating distance for building {feature['properties']['buildingName']}: {e}")
                distance = float('inf')  # Set to infinity if calculation fails
        
        building_info = {
            "building": feature['properties']['buildingName'],
            "building_code": feature['properties']['buildingCode'],
            "coords": building_coords,
            "distance": distance
        }
        # Rest of your building info processing...
        building_info_list.append(building_info)

    # Sort by distance only if user coordinates were provided
    if user_lat is not None and user_lng is not None:
        building_info_list = sorted(building_info_list, key=lambda x: float('inf') if x['distance'] is None else x['distance'])
        
        # Debug output
        print("Sorted distances:", [(b['building'], b['distance']) for b in building_info_list])

    return jsonify(building_info_list)

if __name__ == '__main__':
    app.run()