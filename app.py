import streamlit as st
import google.generativeai as genai
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Configure the Gemini API
GEMINI_API_KEY = "AIzaSyBFBDkj30pm2HJSRa78-KVKgj0-CPl4UCU"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Function to fetch coordinates
def get_coordinates(place):
    geolocator = Nominatim(user_agent="ai_wellness_chatbot")
    try:
        loc = geolocator.geocode(place)
        if loc:
            return loc.latitude, loc.longitude
    except:
        return None, None
    return None, None

# Function to generate activity suggestions
def suggest_places(mood, activity_type, intensity, group_preference, cost_option, user_address, distance_km):
    prompt = (f"I am located at {user_address}. I feel {mood}, I want to {activity_type.lower()}, and prefer {intensity.lower()} intensity. "
              f"I prefer to be {group_preference.lower()} and the activity to be {cost_option.lower()}. "
              f"Within {distance_km} km of my location, suggest specific activity locations with their names only.")
    response = model.generate_content(prompt)
    if response.text:
        return response.text.split("\n")  # Return as a list of suggestions
    return ["No suitable activities found nearby."]

# Streamlit UI
st.set_page_config(page_title="Fit Forecast - AI Wellness Chatbot", page_icon="💪", layout="wide")
st.markdown("<h1 style='text-align: center; color: #008CBA;'>💪 Fit Forecast - AI Wellness Chatbot</h1>", unsafe_allow_html=True)

# Address input
user_query = st.text_input("Enter your address:")

# User inputs for activity preferences
mood = st.selectbox("How are you feeling today?", ["Happy", "Stressed", "Bored", "Sad", "Energetic", "Tired"])
activity_type = st.radio("Would you like to:", ["Workout", "Relax"])
intensity = st.radio("Select intensity:", ["High", "Low"] if activity_type == "Workout" else ["Deep relaxation", "Light relaxation"])
group_preference = st.radio("Would you prefer to be:", ["Alone", "In a group"])
cost_option = st.radio("Do you want the activity to be free or paid?", ["Free", "Paid"])
distance = st.slider("Maximum distance you are willing to travel (in km):", 1, 50, 10)

# Generate and display activity suggestions
if user_query:
    lat, lon = get_coordinates(user_query)
    if lat and lon:
        st.write(f"📍 Selected Address: {user_query}")
        
        # Generate activity suggestions
        activity_suggestions = suggest_places(mood, activity_type, intensity, group_preference, cost_option, user_query, distance)

        # Display activity suggestions
        st.markdown("### 🤖 Activity Suggestions Based on Your Preferences")
        map = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], popup="Your Address", icon=folium.Icon(color='blue')).add_to(map)

        for suggestion in activity_suggestions:
            if suggestion != "No suitable activities found nearby.":
                suggestion_lat, suggestion_lon = get_coordinates(suggestion)
                if suggestion_lat and suggestion_lon:
                    # Calculate distance and check if within range
                    distance_to_place = geodesic((lat, lon), (suggestion_lat, suggestion_lon)).kilometers
                    if distance_to_place <= distance:
                        folium.Marker(
                            [suggestion_lat, suggestion_lon],
                            popup=suggestion,
                            icon=folium.Icon(color='green')
                        ).add_to(map)
                        st.write(f"- {suggestion}")

        # Display the map with pinpoints
        folium_static(map)
    else:
        st.warning("Unable to determine coordinates for the entered address.")
