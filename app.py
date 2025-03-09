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

# Function to fetch coordinates and address
def get_coordinates_and_address(place):
    geolocator = Nominatim(user_agent="ai_wellness_chatbot")
    try:
        loc = geolocator.geocode(place)
        if loc:
            return loc.latitude, loc.longitude, loc.address
    except:
        return None, None, None
    return None, None, None

# Function to generate activity suggestions
def suggest_places(mood, activity_type, intensity, group_preference, cost_option, user_address, distance_km):
    prompt = (f"I am located at {user_address}. I feel {mood}, I want to {activity_type.lower()}, and prefer {intensity.lower()} intensity. "
              f"I prefer to be {group_preference.lower()} and the activity to be {cost_option.lower()}. "
              f"Within {distance_km} km of my location, suggest specific activity locations with their names only.")
    response = model.generate_content(prompt)
    if response.text:
        suggestions = response.text.split("\n")
        return [suggestion for suggestion in suggestions if suggestion.strip()]  # Return non-empty suggestions
    return []

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
    lat, lon, address = get_coordinates_and_address(user_query)
    if lat and lon:
        st.write(f"📍 Selected Address: {user_query}")

        # Generate activity suggestions
        activity_suggestions = suggest_places(mood, activity_type, intensity, group_preference, cost_option, user_query, distance)

        # Ensure there is always at least one suggestion
        if not activity_suggestions:
            activity_suggestions = ["Try exploring a new park in your area! 🌳"]

        # Display activity suggestions
        st.markdown("### 🤖 Activity Suggestions Based on Your Preferences")
        map = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], popup="Your Address", icon=folium.Icon(color='blue')).add_to(map)

        valid_suggestions = False  # Track whether any suggestions are valid within distance

        for suggestion in activity_suggestions:
            suggestion_lat, suggestion_lon, suggestion_address = get_coordinates_and_address(suggestion)
            if suggestion_lat and suggestion_lon:
                # Calculate distance and check if within range
                distance_to_place = geodesic((lat, lon), (suggestion_lat, suggestion_lon)).kilometers
                if distance_to_place <= distance:
                    valid_suggestions = True
                    folium.Marker(
                        [suggestion_lat, suggestion_lon],
                        popup=f"{suggestion}<br>{suggestion_address}",
                        icon=folium.Icon(color='green')
                    ).add_to(map)
                    st.write(f"- **{suggestion}**: {suggestion_address}")

        # Notify user if no valid suggestions are found within the distance
        if not valid_suggestions:
            st.warning(f"No activities found within {distance} km of your address.")

        # Display the map with pinpoints
        folium_static(map)
    else:
        st.warning("Unable to determine coordinates for the entered address.")