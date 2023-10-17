# Import required libraries
import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup as BS

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
        'Total Ratings': [total_ratings],
        'Total Users Rated': [total_users_rated],
        'Density (places/m^2)': [density]
    }
    df = pd.DataFrame(data)

    st.subheader("Population Density:")
    st.write(df)

    place_data_list = get_nearby_places_2(lat, lon, api_key, rad)
    place_df = pd.DataFrame(place_data_list)
    place_df_grouped = place_df.groupby(['primary_type', 'name']).agg({'user_ratings_total': 'sum'}).reset_index()
    place_df_grouped.columns = ['Place Type', 'Name', 'Total Users Rated']
    sorted_df = place_df_grouped.sort_values(by='Total Users Rated', ascending=False).reset_index(drop=True)

    st.subheader("Places Detail:")
    st.write(sorted_df)
