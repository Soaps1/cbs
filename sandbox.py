import streamlit as st
import pandas as pd
import pydeck as pdk
import json
from shapely.geometry import Point, Polygon
from shapely.ops import transform
from functools import partial
import pyproj

# Set page title
st.set_page_config(page_title="NYC Neighborhoods Map", layout="wide")

# Add a title
st.title("New York City Neighborhoods Map")

# Function to create a circular polygon from a point
def point_to_circle(lon, lat, radius=0.001):
    point = Point(lon, lat)
    proj_wgs84 = pyproj.Proj('EPSG:4326')
    proj_meters = pyproj.Proj('EPSG:3857')
    project = partial(pyproj.transform, proj_wgs84, proj_meters)
    point_transformed = transform(project, point)
    buffer = point_transformed.buffer(radius)
    project_back = partial(pyproj.transform, proj_meters, proj_wgs84)
    buffer_wgs84 = transform(project_back, buffer)
    return list(buffer_wgs84.exterior.coords)

# Load GeoJSON data
with open("Neighborhoods Boundries.geojson", "r") as f:
    geojson_data = json.load(f)

# Extract neighborhood data
neighborhoods = []
for feature in geojson_data['features']:
    geometry = feature['geometry']
    properties = feature['properties']
    
    if geometry['type'] == 'Point':
        lon, lat = geometry['coordinates']
        polygon = point_to_circle(lon, lat)
    elif geometry['type'] == 'Polygon':
        polygon = geometry['coordinates'][0]
    else:
        continue  # Skip any other geometry types
    
    neighborhoods.append({
        'name': properties.get('name', 'Unknown'),
        'borough': properties.get('borough', 'Unknown'),
        'polygon': polygon
    })

# Convert to DataFrame for easier handling
neighborhoods_df = pd.DataFrame(neighborhoods)

# Sidebar for user inputs
st.sidebar.header("Map Controls")

# Default coordinates for New York City
default_lat = 40.7128
default_lon = -74.0060

# Let user input coordinates
latitude = st.sidebar.number_input("Latitude", value=default_lat, step=0.01)
longitude = st.sidebar.number_input("Longitude", value=default_lon, step=0.01)

# Color mapping for boroughs
borough_colors = {
    'Manhattan': [255, 0, 0],
    'Brooklyn': [0, 255, 0],
    'Queens': [0, 0, 255],
    'Bronx': [255, 255, 0],
    'Staten Island': [255, 0, 255]
}

# Create map layers
layers = [
    pdk.Layer(
        'PolygonLayer',
        data=neighborhoods_df,
        get_polygon='polygon',
        get_fill_color=[
            'match',
            ['get', 'borough'],
            'Manhattan', borough_colors['Manhattan'],
            'Brooklyn', borough_colors['Brooklyn'],
            'Queens', borough_colors['Queens'],
            'Bronx', borough_colors['Bronx'],
            'Staten Island', borough_colors['Staten Island'],
            [180, 180, 180]  # Default color
        ],
        get_line_color=[0, 0, 0],
        line_width_min_pixels=1,
        opacity=0.6,
        pickable=True,
        auto_highlight=True
    ),
    pdk.Layer(
        'ScatterplotLayer',
        data=pd.DataFrame({'lat': [latitude], 'lon': [longitude]}),
        get_position='[lon, lat]',
        get_color=[0, 0, 0, 200],  # Black
        get_radius=300,
    )
]

# Create map
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=latitude,
        longitude=longitude,
        zoom=10,
        pitch=0,
    ),
    layers=layers,
    tooltip={
        'html': '{name}<br/>{borough}',
        'style': {
            'backgroundColor': 'steelblue',
            'color': 'white'
        }
    }
))

# Display the coordinates
st.write(f"Selected Coordinates: {latitude}, {longitude}")

# Add a reset button
if st.button("Reset to NYC"):
    st.experimental_rerun()

# Add a legend
st.sidebar.markdown("### Borough Colors")
for borough, color in borough_colors.items():
    st.sidebar.markdown(
        f'<div style="display: flex; align-items: center;">'
        f'<div style="width: 20px; height: 20px; background-color: rgba({color[0]}, {color[1]}, {color[2]}, 0.6); margin-right: 10px;"></div>'
        f'{borough}'
        '</div>',
        unsafe_allow_html=True
    )