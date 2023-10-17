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
    sorted_df = place_df_grouped.sort_values(by='Total Users Rated', ascending=False).reset_index(drop=True)


    st.subheader("Places Detail:")
    st.write(sorted_df)

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

    # Constructing the full URL
    map_url = f"{base_url}center={center}&zoom={zoom}&size={size}&maptype={maptype}&markers={marker}&path={path}&key={api_key}"

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
