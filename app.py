# Import required libraries
import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup as BS
from math import sin, cos, sqrt, atan2, radians
import pydeck as pdk
import overpy
# import cv2
import numpy as np

import json
from google.cloud import vision
from google.oauth2.service_account import Credentials

# Memuat kredensial dari secrets.toml
# creds_info = json.loads(st.secrets["google"]["credentials"])
creds_info = st.secrets["google"]["credentials"]

creds = Credentials.from_service_account_info(creds_info)
client = vision.ImageAnnotatorClient(credentials=creds)

headers = {'User-agent': 'Mozilla/5.0'}

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

def get_latlong(url):
    response = requests.get(url, headers=headers)
    soup = BS(response.text, 'html.parser')
    soup = str(soup)
    latlong = soup.find('APP_INITIALIZATION_STATE')
    latlong_temp = soup[latlong+44:latlong+99]
    lat = latlong_temp.split(',')[2]
    lattitude = lat.split(']')[0]
    longitude = latlong_temp.split(',')[1]
    return lattitude, longitude

# def get_nearby_places(latitude, longitude, api_key):
#     endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
#     params = {
#         'location': f"{latitude},{longitude}",
#         'rankby': 'distance',
#         'key': api_key
#     }
#     response = requests.get(endpoint_url, params=params)
#     result = response.json()
#     total_places = len(result['results'])
#     total_ratings = 0
#     total_users_rated = 0
#     for place in result['results']:
#         if 'user_ratings_total' in place:
#             total_users_rated += place['user_ratings_total']
#         if 'rating' in place:
#             total_ratings += place['rating']
#     return total_places, total_ratings, total_users_rated



def calculate_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula to calculate the distance
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c * 1000  # Convert distance from km to meters

    return distance

# def get_nearby_places_2(latitude, longitude, api_key):
#     endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
#     params = {
#         'location': f"{latitude},{longitude}",
#         # 'radius': rad,
#         'rankby': 'distance',
#         'key': api_key
#     }
#     response = requests.get(endpoint_url, params=params)
#     result = response.json()
#     place_data_list = []
#     for place in result['results']:
#         data = {}
#         data['name'] = place['name']
#         data['primary_type'] = place['types'][0]
#         data['user_ratings_total'] = place.get('user_ratings_total', 0)
#         data['latitude'] = place['geometry']['location']['lat']
#         data['longitude'] = place['geometry']['location']['lng']
#         data['distance'] = calculate_distance(float(latitude), float(longitude), data['latitude'], data['longitude'])
#         place_data_list.append(data)
#     return place_data_list

import requests

def get_nearby_places_2(latitude, longitude, api_key):
    endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    place_data_list = []
    next_page_token = None

    for _ in range(3):  # 3 kali permintaan untuk mendapatkan hingga 60 hasil
        params = {
            'location': f"{latitude},{longitude}",
            'rankby': 'distance',
            'key': api_key
        }
        if next_page_token:  # Jika ada token halaman berikutnya, tambahkan ke parameter
            params['pagetoken'] = next_page_token

        response = requests.get(endpoint_url, params=params)
        result = response.json()

        for place in result['results']:
            data = {}
            data['name'] = place['name']
            data['primary_type'] = place['types'][0]
            data['user_ratings_total'] = place.get('user_ratings_total', 0)
            data['latitude'] = place['geometry']['location']['lat']
            data['longitude'] = place['geometry']['location']['lng']
            data['distance'] = calculate_distance(float(latitude), float(longitude), data['latitude'], data['longitude'])
            place_data_list.append(data)

        next_page_token = result.get('next_page_token')  # Ambil token untuk halaman berikutnya

        if not next_page_token:  # Jika tidak ada token untuk halaman berikutnya, berhenti
            break

        # Tunggu beberapa detik sebelum melakukan permintaan berikutnya karena ada delay antara permintaan
        import time
        time.sleep(2)

    return place_data_list


def generate_circle_points(lat, lon, radius, num_points=36):
    """Generate points that approximate a circle on a map for a given latitude, longitude, and radius."""
    points = []
    for i in range(num_points):
        angle = float(i) / num_points * (2.0 * 3.141592653589793)  # 2*Pi radians = 360 degrees
        dx = radius * cos(angle)
        dy = radius * sin(angle)
        point_lat = lat + (dy / 111300)  # roughly 111.3km per degree of latitude
        point_lon = lon + (dx / (111300 * cos(lat)))  # adjust for latitude in longitude calculation
        points.append((point_lat, point_lon))
    return points

# def get_road_name_from_placeid(place_id, api_key):
#     endpoint_url = "https://maps.googleapis.com/maps/api/place/details/json"
#     params = {
#         'place_id': place_id,
#         'key': api_key
#     }
#     response = requests.get(endpoint_url, params=params)
#     result = response.json()
#     return result['result']['name'] if 'name' in result['result'] else "Unknown"

# def get_nearby_roads(latitude, longitude, api_key, rad):
#     endpoint_url = "https://roads.googleapis.com/v1/nearestRoads"
#     params = {
#         'points': f"{latitude},{longitude}",
#         'key': api_key
#     }
#     response = requests.get(endpoint_url, params=params)
#     result = response.json()

#     road_data_list = []
#     for road in result.get('snappedPoints', []):
#         data = {}
#         place_id = road.get('placeId')
#         data['road_name'] = get_road_name_from_placeid(place_id, api_key)
#         data['latitude'] = road['location']['latitude']
#         data['longitude'] = road['location']['longitude']
#         data['distance'] = calculate_distance(float(latitude), float(longitude), data['latitude'], data['longitude'])
#         road_data_list.append(data)
#     return road_data_list

# def get_osm_roads_within_radius(latitude, longitude, rad):
#     # Convert radius from meters to degrees (approximation)
#     radius_in_degrees = rad / 111300

#     overpass_url = "https://overpass-api.de/api/interpreter"
#     overpass_query = f"""
#     [out:json][timeout:25];
#     (
#       way["highway"](around:{rad},{latitude},{longitude});
#     );
#     out geom;
#     """
#     response = requests.get(overpass_url, params={'data': overpass_query})

#     # Error handling for bad response or empty data
#     if response.status_code != 200:
#         print(f"Overpass API returned status {response.status_code}: {response.text}")
#         return []
    
#     data = response.json()

#     road_dict = {}

#     for element in data['elements']:
#         if element['type'] == 'way':
#             road_id = element['id']
#             road_type = element['tags'].get('highway', 'Unknown')

#             if road_id not in road_dict:
#                 road_dict[road_id] = {
#                     'road_id': road_id,
#                     'road_name': element['tags'].get('name', 'Unknown'),
#                     'road_type': road_type,
#                     'distance': float("inf")
#                 }

#             for geometry in element.get("geometry", []):
#                 lat, lon = geometry['lat'], geometry['lon']
#                 distance = calculate_distance(float(latitude), float(longitude), lat, lon)
#                 if distance < road_dict[road_id]['distance']:
#                     road_dict[road_id]['distance'] = distance
#                     road_dict[road_id]['latitude'] = lat
#                     road_dict[road_id]['longitude'] = lon

#     return list(road_dict.values())

def get_osm_details(latitude, longitude):
    api = overpy.Overpass()
    # Query untuk mencari jalan di sekitar koordinat tertentu
    query = f"""
    way(around:50,{latitude},{longitude})["highway"];
    (._;>;);
    out body;
    """
    result = api.query(query)
    if result.ways:  # Jika menemukan satu atau lebih jalan
        way = result.ways[0]  # Ambil informasi dari jalan pertama
        road_name = way.tags.get("name", "Unknown")
        road_type = way.tags.get("highway", "Unknown")
        return road_name, road_type
    else:  # Jika tidak menemukan jalan
        return "Unknown", "Unknown"


def get_road_details_from_place_id(place_id, api_key):
    endpoint_url = f"https://maps.googleapis.com/maps/api/geocode/json?place_id={place_id}&key={api_key}"
    response = requests.get(endpoint_url)
    if response.status_code != 200:
        return None, None

    data = response.json()
    if not data['results']:
        return None, None

    address_components = data['results'][0]['address_components']
    road_name = None
    for component in address_components:
        if "route" in component['types']:
            road_name = component['long_name']
            break

    # Here, the road type is not exactly provided by Google Geocoding API, 
    # but you can infer it from the road name or other properties.
    # I'm setting it to 'Unknown' for this example.
    # road_type = "Unknown"
    return road_name

def get_google_roads_nearby(latitude, longitude, api_key):
    endpoint_url = f"https://roads.googleapis.com/v1/nearestRoads?points={latitude},{longitude}&key={api_key}"
    response = requests.get(endpoint_url)
    
    if response.status_code != 200:
        print(f"Google Maps API returned status {response.status_code}: {response.text}")
        return []

    data = response.json()
    roads_data_list = []

    for road_info in data.get('snappedPoints', []):
        road_data = {}
        road_data['road_id'] = road_info.get('placeId')
        road_name = get_road_details_from_place_id(road_data['road_id'], api_key)
        
        # Get OSM road name and type using the function
        road_name_ver_OSM, road_type_ver_OSM = get_osm_details(road_info.get('location', {}).get('latitude', 0),
                                               road_info.get('location', {}).get('longitude', 0))
        road_data['Road Name (Google)'] = road_name
        road_data['Road Name (OSM)'] = road_name_ver_OSM
        road_data['Road Type'] = road_type_ver_OSM

        road_data['latitude'] = float(road_info.get('location', {}).get('latitude', 0))
        road_data['longitude'] = float(road_info.get('location', {}).get('longitude', 0))

        latitude = float(latitude)
        longitude = float(longitude)

        road_data['Distance (meters)'] = calculate_distance(latitude, longitude, road_data['latitude'], road_data['longitude'])
        roads_data_list.append(road_data)

    return roads_data_list

# Fungsi untuk mengembalikan nilai intensitas berdasarkan jenis jalan
def assign_intensity(road_type):
    intensity_map = {
        'motorway': 10,
        'trunk': 9,
        'primary': 8,
        'secondary': 7,
        'tertiary': 6,
        'residential': 5,
        'service': 4,
        'track': 3,
        'unclassified': 2,
        'no_road': 0
    }
    
    score = intensity_map.get(road_type, 1)
    
    # Penentuan label berdasarkan skor
    if score >= 7:
        label = "tinggi"
    elif score >= 4:
        label = "sedang"
    else:
        label = "rendah"
    
    return label, score

# Fungsi untuk mendeteksi kendaraan dalam gambar
def detect_vehicles(img, net, output_layers):
    height, width, _ = img.shape
    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)
    
    class_ids = []
    confidences = []
    boxes = []
    
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5: # Anda dapat menyesuaikan ambang batas ini
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)
                
    # Gunakan Non Maximum Suppression
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    vehicle_count = 0
    for i in range(len(boxes)):
        if i in indexes:
            label = str(classes[class_ids[i]])
            if label in ['car', 'truck', 'bus', 'motorcycle']: # Anda dapat menambahkan lebih banyak kategori kendaraan jika perlu
                vehicle_count += 1
                
    return vehicle_count

# Streamlit App UI
st.title("Spot Score Analyzer")

# Memberikan pilihan kepada pengguna
input_method = st.radio("Choose input method:", ["Input location link", "Select from map (Soon)"])

if input_method == "Input location link":
    # Taking inputs
    # rad = st.number_input("Input Radius (in meters)", min_value=10, value=200)
    latlong = st.text_input("Input location link", "")
    api_key = st.secrets['GOOGLE_API_KEY'] # This is not secure. Consider using secrets management or Streamlit Secrets
    
    if st.button('Analyze'):
        with st.spinner('Analyzing...(~6 seconds)'):
            lat, lon = get_latlong(latlong)
            # total_places, total_ratings, total_users_rated = get_nearby_places(lat, lon, api_key)
        
            # Calculate density
            # area = 3.14 * (1**2)
            # density = total_places / area
        
            # Create DataFrame
            # data = {
            #     'Total Places': [total_places],
            #     # 'Total Ratings': [total_ratings],
            #     'Total Users Rated': [total_users_rated],
            #     'Density (places/m^2)': [density]
            # }
            # df = pd.DataFrame(data)
        
            # st.subheader("Population Density:")
            # st.write(df)
        
            place_data_list = get_nearby_places_2(lat, lon, api_key)
            place_df = pd.DataFrame(place_data_list)
            place_df_grouped = place_df.groupby(['primary_type', 'name']).agg({
                'user_ratings_total': 'sum',
                'distance': 'mean'  # Assuming you want the average distance in case of multiple places with the same name and type
            }).reset_index()
            place_df_grouped.columns = ['Place Type', 'Name', 'Total Users Rated', 'Distance (meters)']
            sorted_df = place_df_grouped.sort_values(by='Distance (meters)', ascending=True).reset_index(drop=True)
        
        
            st.subheader("Places Detail:")
            st.write(sorted_df)
        
            # roads_data_list = get_osm_roads_within_radius(lat, lon, rad)
            roads_data_list = get_google_roads_nearby(lat, lon, api_key)
            
            roads_df = pd.DataFrame(roads_data_list)
            # try:
            roads_df['Intensitas'], roads_df['Intensitas (Score)'] = zip(*roads_df['Road Type'].apply(assign_intensity))
            roads_df = roads_df.drop('road_id', axis = 1)
            roads_df = roads_df.drop_duplicates()
            roads_df_sorted = roads_df.sort_values(by='Distance (meters)', ascending=True).reset_index(drop=True)
            
            st.subheader("Nearby Roads :")
            st.write(roads_df_sorted)
        
            st.subheader("Effectivity Score :")
            
            # place_df_grouped['POI Reviewers'] = place_df_grouped['Total Users Rated'].apply(lambda x: x/1000 if x <= 1000 else 1)
            place_df_grouped['Distance Score Place'] = place_df_grouped['Distance (meters)'].apply(lambda x: 1 - x/500 if x <= 500 else 0)
            place_df_grouped['POI Reviewers Norm'] = place_df_grouped['Total Users Rated']*place_df_grouped['Distance Score Place']#.apply(lambda x: x/1000 if x <= 1000 else 1)
            
            # 2. Hitung rata-rata UserScore dan DistanceScorePlace
            sum_user_score = place_df_grouped['POI Reviewers Norm'].sum()
            if sum_user_score <= 1000:
                sum_user_score_norm = sum_user_score / 1000
            else:
                sum_user_score_norm = 1
            avg_distance_score_place = place_df_grouped['Distance Score Place'].mean()
            
            # 3. Ambil nilai Intensitas (Score) dan Distance (meters) dari roads_df
            road_intensity_score = roads_df['Intensitas (Score)'].iloc[0] / 10
            distance_score_road = 1 - roads_df['Distance (meters)'].iloc[0] / 100 if roads_df['Distance (meters)'].iloc[0] <= 100 else 0
            
            # 4. Hitung Effectivity Score
            # poi_weight = st.slider('Choose weight of POI / Road Type :', 0, 100)
            if road_intensity_score < 0.8:
                poi_weight = 0.7
                effectivity_score = (poi_weight*sum_user_score_norm + (1-poi_weight)*(road_intensity_score * distance_score_road)) * 100
            if road_intensity_score >= 0.8:
                poi_weight = 0.3
                effectivity_score = (poi_weight*sum_user_score_norm + (1-poi_weight)*(road_intensity_score * distance_score_road)) * 100
            
            # 5. Simpan ke DataFrame baru
            df_effectivity = pd.DataFrame({
                'Effectivity Score': [effectivity_score],
                'POI Reviewers': [sum_user_score],
                'Avg Distance POI': [avg_distance_score_place],
                'POI Reviewers Norm Distance': [sum_user_score_norm],
                'Road Intensity Score': [road_intensity_score],
                'Road Distance': [distance_score_road]
            })
    
            formatted_score = "{:.2f}%".format(effectivity_score)
            st.markdown(f"<span style='font-size: 32px; color: red;'>{formatted_score}</span>", unsafe_allow_html=True)
            # st.write("")
            st.write(df_effectivity)
        
            st.subheader("Input Location Map:")
        
            # Convert lat and lon to float for arithmetic operations
            lat_float = float(lat)
            lon_float = float(lon)
        
            # Build the Google Maps Static API URL
            base_url = "https://maps.googleapis.com/maps/api/staticmap?"
        
            # Parameters
            center = f"{lat_float},{lon_float}"
            zoom = "18"
            size = "600x300"
            maptype = "roadmap"
            marker = f"color:red|label:C|{lat_float},{lon_float}"
            rad = 200
            path = f"fillcolor:0xAA000033|color:0xFFFF0033|enc:{lat_float},{lon_float}|{lat_float+rad/111300},{lon_float}|{lat_float},{lon_float-rad/111300}|{lat_float-rad/111300},{lon_float}|{lat_float},{lon_float+rad/111300}|{lat_float+rad/111300},{lon_float}|{lat_float},{lon_float-rad/111300}"
        
            # # Constructing the full URL
            # map_url = f"{base_url}center={center}&zoom={zoom}&size={size}&maptype={maptype}&markers={marker}&path={path}&key={api_key}"
        
            # Generate points for circle approximation
            circle_points = generate_circle_points(lat_float, lon_float, rad)
            
            # Construct circle path string
            circle_path = "color:0xFFFF0033|weight:2|" + "|".join([f"{point[0]},{point[1]}" for point in circle_points])
            
            # Incorporate circle path into the full URL
            map_url = f"{base_url}center={center}&zoom={zoom}&size={size}&maptype={maptype}&markers={marker}&path={circle_path}&key={api_key}"
    
            # Display the map in Streamlit
            st.image(map_url)
    
            # # Display the map in Streamlit
            # st.write("Street Views")
            # # Build the Google Street View Static API URL for different directions
            # street_view_base_url = "https://maps.googleapis.com/maps/api/streetview?"
            # street_view_size = "600x300"
            
            # directions = {
            #     "North": 0,
            #     "East": 90,
            #     "South": 180,
            #     "West": 270
            # }
            
            # # Fetch and display Street View images for each direction
            # for direction_name, heading_value in directions.items():
            #     street_view_url = f"{street_view_base_url}size={street_view_size}&location={lat_float},{lon_float}&heading={heading_value}&key={api_key}"
                
            #     # Display the Street View image in Streamlit
            #     st.image(street_view_url, caption=f"Street View ({direction_name})", use_column_width=True)

            # Display the map in Streamlit
            st.write("Street Views")
            # Build the Google Street View Static API URL for different directions
            street_view_base_url = "https://maps.googleapis.com/maps/api/streetview?"
            street_view_size = "600x300"
            
            directions = {
                "North": 0,
                "East": 90,
                "South": 180,
                "West": 270
            }
            
            total_vehicles = 0
            
            # Fetch and display Street View images for each direction
            for direction_name, heading_value in directions.items():
                street_view_url = f"{street_view_base_url}size={street_view_size}&location={lat_float},{lon_float}&heading={heading_value}&key={api_key}"
                
                # Display the Street View image in Streamlit
                st.image(street_view_url, caption=f"Street View ({direction_name})", use_column_width=True)
            
                # Use Vision API to detect vehicles
                image = vision.Image()
                image.source.image_uri = street_view_url
                response = client.object_localization(image=image)
                for obj in response.localized_object_annotations:
                    if obj.name in ["Car", "Truck", "Bus", "Bicycle", "Motorcycle"]:
                        total_vehicles += 1
            
            st.write(f"Total vehicles detected: {total_vehicles}")

            # except:
            #     st.write("There is no road nearby, please submit another coordinate.")

if input_method == "Select from map (Soon)":
    st.write("Coming Soon...")
    # location = st_googlemap()
    # if location:
    #     lat, lon = location['lat'], location['lng']

    #     # total_places, total_ratings, total_users_rated = get_nearby_places(lat, lon, api_key)

    #     # Calculate density
    #     # area = 3.14 * (1**2)
    #     # density = total_places / area
    
    #     # Create DataFrame
    #     # data = {
    #     #     'Total Places': [total_places],
    #     #     # 'Total Ratings': [total_ratings],
    #     #     'Total Users Rated': [total_users_rated],
    #     #     'Density (places/m^2)': [density]
    #     # }
    #     # df = pd.DataFrame(data)
    
    #     # st.subheader("Population Density:")
    #     # st.write(df)
    
    #     place_data_list = get_nearby_places_2(lat, lon, api_key)
    #     place_df = pd.DataFrame(place_data_list)
    #     place_df_grouped = place_df.groupby(['primary_type', 'name']).agg({
    #         'user_ratings_total': 'sum',
    #         'distance': 'mean'  # Assuming you want the average distance in case of multiple places with the same name and type
    #     }).reset_index()
    #     place_df_grouped.columns = ['Place Type', 'Name', 'Total Users Rated', 'Distance (meters)']
    #     sorted_df = place_df_grouped.sort_values(by='Distance (meters)', ascending=True).reset_index(drop=True)
    
    
    #     st.subheader("Places Detail:")
    #     st.write(sorted_df)
    
    #     # roads_data_list = get_osm_roads_within_radius(lat, lon, rad)
    #     roads_data_list = get_google_roads_nearby(lat, lon, api_key)
        
    #     roads_df = pd.DataFrame(roads_data_list)
    #     roads_df['Intensitas'], roads_df['Intensitas (Score)'] = zip(*roads_df['Road Type'].apply(assign_intensity))
    #     roads_df = roads_df.drop('road_id', axis = 1)
    #     roads_df = roads_df.drop_duplicates()
    #     roads_df_sorted = roads_df.sort_values(by='Distance (meters)', ascending=True).reset_index(drop=True)
        
    #     st.subheader("Nearby Roads :")
    #     st.write(roads_df_sorted)
    
    #     st.subheader("Effectivity Score :")
    #     # place_df_grouped['POI Reviewers'] = place_df_grouped['Total Users Rated'].apply(lambda x: x/1000 if x <= 1000 else 1)
    #     place_df_grouped['Distance Score Place'] = place_df_grouped['Distance (meters)'].apply(lambda x: 1 - x/500 if x <= 500 else 0)
    #     place_df_grouped['POI Reviewers Norm'] = place_df_grouped['Total Users Rated']*place_df_grouped['Distance Score Place']#.apply(lambda x: x/1000 if x <= 1000 else 1)
        
    #     # 2. Hitung rata-rata UserScore dan DistanceScorePlace
    #     sum_user_score = place_df_grouped['POI Reviewers Norm'].sum()
    #     if sum_user_score <= 1000:
    #         sum_user_score_norm = sum_user_score / 1000
    #     else:
    #         sum_user_score_norm = 1
    #     avg_distance_score_place = place_df_grouped['Distance Score Place'].mean()
        
    #     # 3. Ambil nilai Intensitas (Score) dan Distance (meters) dari roads_df
    #     road_intensity_score = roads_df['Intensitas (Score)'].iloc[0] / 10
    #     distance_score_road = 1 - roads_df['Distance (meters)'].iloc[0] / 100 if roads_df['Distance (meters)'].iloc[0] <= 100 else 0
        
    #     # 4. Hitung Effectivity Score
    #     effectivity_score = (sum_user_score_norm + road_intensity_score * distance_score_road)/2 * 100
        
    #     # 5. Simpan ke DataFrame baru
    #     df_effectivity = pd.DataFrame({
    #         'Effectivity Score': [effectivity_score],
    #         'POI Reviewers': [sum_user_score],
    #         'Avg Distance POI': [avg_distance_score_place],
    #         'POI Reviewers Norm Distance': [sum_user_score_norm],
    #         'Road Intensity Score': [road_intensity_score],
    #         'Road Distance': [distance_score_road]
    #     })
        
    #     st.write(df_effectivity)
    
    #     st.subheader("Input Location Map:")
    
    #     # Convert lat and lon to float for arithmetic operations
    #     lat_float = float(lat)
    #     lon_float = float(lon)
    
    #     # Build the Google Maps Static API URL
    #     base_url = "https://maps.googleapis.com/maps/api/staticmap?"
    
    #     # Parameters
    #     center = f"{lat_float},{lon_float}"
    #     zoom = "18"
    #     size = "600x300"
    #     maptype = "roadmap"
    #     marker = f"color:red|label:C|{lat_float},{lon_float}"
    #     rad = 200
    #     path = f"fillcolor:0xAA000033|color:0xFFFF0033|enc:{lat_float},{lon_float}|{lat_float+rad/111300},{lon_float}|{lat_float},{lon_float-rad/111300}|{lat_float-rad/111300},{lon_float}|{lat_float},{lon_float+rad/111300}|{lat_float+rad/111300},{lon_float}|{lat_float},{lon_float-rad/111300}"
    
    #     # # Constructing the full URL
    #     # map_url = f"{base_url}center={center}&zoom={zoom}&size={size}&maptype={maptype}&markers={marker}&path={path}&key={api_key}"
    
    #     # Generate points for circle approximation
    #     circle_points = generate_circle_points(lat_float, lon_float, rad)
        
    #     # Construct circle path string
    #     circle_path = "color:0xFFFF0033|weight:2|" + "|".join([f"{point[0]},{point[1]}" for point in circle_points])
        
    #     # Incorporate circle path into the full URL
    #     map_url = f"{base_url}center={center}&zoom={zoom}&size={size}&maptype={maptype}&markers={marker}&path={circle_path}&key={api_key}"
        
    #     # Display the map in Streamlit
    #     st.image(map_url)
