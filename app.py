# Import required libraries
import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup as BS
from math import sin, cos, sqrt, atan2, radians
import pydeck as pdk

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

def get_nearby_places(latitude, longitude, api_key, rad):
    endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'location': f"{latitude},{longitude}",
        'radius': rad,
        'key': api_key
    }
    response = requests.get(endpoint_url, params=params)
    result = response.json()
    total_places = len(result['results'])
    total_ratings = 0
    total_users_rated = 0
    for place in result['results']:
        if 'user_ratings_total' in place:
            total_users_rated += place['user_ratings_total']
        if 'rating' in place:
            total_ratings += place['rating']
    return total_places, total_ratings, total_users_rated


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

def get_nearby_places_2(latitude, longitude, api_key, rad):
    endpoint_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'location': f"{latitude},{longitude}",
        'radius': rad,
        'key': api_key
    }
    response = requests.get(endpoint_url, params=params)
    result = response.json()
    place_data_list = []
    for place in result['results']:
        data = {}
        data['name'] = place['name']
        data['primary_type'] = place['types'][0]
        data['user_ratings_total'] = place.get('user_ratings_total', 0)
        data['latitude'] = place['geometry']['location']['lat']
        data['longitude'] = place['geometry']['location']['lng']
        data['distance'] = calculate_distance(float(latitude), float(longitude), data['latitude'], data['longitude'])
        place_data_list.append(data)
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
    road_type = "Unknown"
    return road_name, road_type

def get_google_roads_nearby(latitude, longitude, rad, api_key):
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
        
        road_name, road_type = get_road_details_from_place_id(road_data['road_id'])
        road_data['road_name'] = road_name or 'Unknown'
        road_data['road_type'] = road_type

        road_data['latitude'] = float(road_info['location']['latitude'])
        road_data['longitude'] = float(road_info['location']['longitude'])
        road_data['distance'] = calculate_distance(latitude, longitude, road_data['latitude'], road_data['longitude'])
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
        'unclassified': 5,
        'residential': 4,
        'service': 3,
        'track': 2
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

# Streamlit App UI
st.title("Nearby Places Analysis")

# Taking inputs
rad = st.number_input("Input Radius (in meters)", min_value=10, value=200)
latlong = st.text_input("Input location link", "")
api_key = st.secrets['GOOGLE_API_KEY'] # This is not secure. Consider using secrets management or Streamlit Secrets

if st.button('Analyze'):
    lat, lon = get_latlong(latlong)
    total_places, total_ratings, total_users_rated = get_nearby_places(lat, lon, api_key, rad)

    # Calculate density
    area = 3.14 * (1**2)
    density = total_places / area

    # Create DataFrame
    data = {
        'Total Places': [total_places],
        # 'Total Ratings': [total_ratings],
        'Total Users Rated': [total_users_rated],
        'Density (places/m^2)': [density]
    }
    df = pd.DataFrame(data)

    st.subheader("Population Density:")
    st.write(df)

    place_data_list = get_nearby_places_2(lat, lon, api_key, rad)
    place_df = pd.DataFrame(place_data_list)
    place_df_grouped = place_df.groupby(['primary_type', 'name']).agg({
        'user_ratings_total': 'sum',
        'distance': 'mean'  # Assuming you want the average distance in case of multiple places with the same name and type
    }).reset_index()
    place_df_grouped.columns = ['Place Type', 'Name', 'Total Users Rated', 'Distance (in meters)']
    sorted_df = place_df_grouped.sort_values(by='Distance (in meters)', ascending=True).reset_index(drop=True)


    st.subheader("Places Detail:")
    st.write(sorted_df)

    # roads_data_list = get_osm_roads_within_radius(lat, lon, rad)
    roads_data_list = get_google_roads_nearby(lat, lon, rad, api_key)
    
    roads_df = pd.DataFrame(roads_data_list)
    roads_df['intensitas'], roads_df['intensitas_score'] = zip(*roads_df['road_type'].apply(assign_intensity))
    roads_df_sorted = roads_df.sort_values(by='distance', ascending=True).reset_index(drop=True)
    
    st.subheader("Nearby Roads :")
    st.write(roads_df_sorted)

    st.subheader("Input Location Map:")

    # Convert lat and lon to float for arithmetic operations
    lat_float = float(lat)
    lon_float = float(lon)

    # Build the Google Maps Static API URL
    base_url = "https://maps.googleapis.com/maps/api/staticmap?"

    # Parameters
    center = f"{lat_float},{lon_float}"
    zoom = "14"
    size = "600x300"
    maptype = "roadmap"
    marker = f"color:red|label:C|{lat_float},{lon_float}"
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

    # st.subheader("Input Location Map:")

    # # Create a DataFrame for the input latitude and longitude
    # map_data = pd.DataFrame({'lat': [float(lat)], 'lon': [float(lon)]})

    # # Display map with circle overlay for the input radius
    # view_state = pdk.ViewState(
    #     latitude=float(lat),
    #     longitude=float(lon),
    #     zoom=14,
    #     pitch=0,
    #     bearing=0
    # )

    # circle_layer = pdk.Layer(
    #     "ScatterplotLayer",
    #     map_data,
    #     get_position=["lon", "lat"],
    #     get_radius=rad,  # radius in meters
    #     get_fill_color=[255, 0, 0, 100],
    #     pickable=True,
    #     stroked=True
    # )

    # st.pydeck_chart(pdk.Deck(
    #     layers=[circle_layer],
    #     initial_view_state=view_state,
    # ))
