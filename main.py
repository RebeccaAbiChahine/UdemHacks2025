#from google import genai
#import streamlit as st

#client = genai.Client(api_key="AIzaSyBFBDkj30pm2HJSRa78-KVKgj0-CPl4UCU") #Bad practice, to hide later!!
#response = client.models.generate_content(
 #   model="gemini-2.0-flash", contents="Generate and run a streamlit web app showing only 'Hello, world!'for the moment. "
#)
import streamlit as st
import google.generativeai as genai
import requests
import folium
from streamlit_folium import st_folium
import geocoder
from datetime import datetime
import pydeck as pdk

# Configure the Gemini API
GEMINI_API_KEY = "AIzaSyBFBDkj30pm2HJSRa78-KVKgj0-CPl4UCU"  # Replace with your API key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize chat model
model = genai.GenerativeModel("gemini-2.0-flash")

# Function to get weather forecast for the whole day using Open-Meteo (Free Alternative to OpenWeatherMap)
def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,weathercode"
    response = requests.get(url).json()
    if "hourly" in response:
        return response["hourly"]
    return None

# Function to get user's geolocation using geocoder (Free Alternative to Google Geolocation API)
def get_location():
    location = geocoder.ip('me')
    if location.latlng:
        return location.city, location.latlng[0], location.latlng[1]
    return "Unknown", None, None

# Function to get address suggestions using OpenStreetMap Nominatim API
def get_address_suggestions(query):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}&addressdetails=1&limit=5"
    headers = {"User-Agent": "MyWellnessApp/1.0 (contact@example.com)"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except requests.exceptions.RequestException as e:
        print("Error fetching address suggestions:", e)
        return []

# Function to find nearby places using OpenStreetMap Nominatim API
def get_nearby_places(activity_type, lat, lon):
    if lat is None or lon is None:
        return []

    url = f"https://nominatim.openstreetmap.org/search?format=json&q={activity_type}&lat={lat}&lon={lon}&radius=5000"
    headers = {"User-Agent": "MyWellnessApp/1.0 (contact@example.com)"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()[:5]  # Return top 5 results
        else:
            return []
    except requests.exceptions.RequestException as e:
        print("Error fetching data:", e)
        return []

# Streamlit UI
def main():
    st.set_page_config(page_title="Wellness & Fitness AI", page_icon="💪", layout="wide")
    
    st.markdown("<h1 style='text-align: center; color: #008CBA;'>💪 Chat with FitForecast!</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #333;'>Your AI-Powered Wellness Companion</h3>", unsafe_allow_html=True)
    
    city, lat, lon = get_location()
    weather_data = get_weather(lat, lon) if lat and lon else None
    
    if city != "Unknown" and weather_data:
        st.markdown(f"### 🌍 Current Location: {city}")
        st.markdown("### ☀️ Today's Weather Forecast")
        for i in range(0, 24, 3):  # Show weather every 3 hours
            time = datetime.now().replace(hour=i, minute=0).strftime("%I %p")
            temp = weather_data['temperature_2m'][i]
            st.markdown(f"**{time}:** {temp}°C")
    else:
        st.warning("Couldn't retrieve your location or weather data.")
    
    # User inputs
    mood = st.selectbox("How are you feeling today?", ["Happy", "Stressed", "Bored", "Sad", "Energetic", "Tired"])
    activity_type = st.radio("Would you like to:", ["Workout", "Relax"])
    intensity = st.radio("Select intensity:", ["High", "Low"] if activity_type == "Workout" else ["Deep relaxation", "Light relaxation"])
    group_preference = st.radio("Would you prefer to be:", ["Alone", "In a group"])
    
    # Address input with live suggestions
    user_query = st.text_input("Start typing your address:")
    selected_address = None
    if user_query:
        suggestions = get_address_suggestions(user_query)
        if suggestions:
            selected_address = st.selectbox("Select an address:", [s["display_name"] for s in suggestions])
            lat, lon = float(suggestions[0]["lat"]), float(suggestions[0]["lon"])
        else:
            st.warning("No address suggestions found.")
    
    # Let user select the activity before generating the map
    activity_options = ["Yoga in a park", "High-intensity gym session", "Meditation by the lake", "Group dance class", "Solo nature walk", "Spa session", "Cycling route"]
    selected_activity = st.selectbox("Select an activity you’d like to do:", activity_options)
    
    # Generate button
    if st.button("Generate Map & Suggestions") and lat and lon:
        # Find and display locations based on the selected activity
        places = get_nearby_places(selected_activity, lat, lon)
        
        if places:
            st.write(f"📍 Suggested locations for {selected_activity.lower()} near {selected_address}:")
            
            # Display 3D Map using PyDeck
            map_data = [{
                "lat": float(place["lat"]),
                "lon": float(place["lon"]),
                "name": place["display_name"]
            } for place in places]
            
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_data,
                get_position="[lon, lat]",
                get_color="[255, 0, 0, 150]",
                get_radius=100,
                pickable=True,
            )
            view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=12, pitch=50)
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))
        else:
            st.write("No locations found near you.")
    
    # Chatbot interaction
    user_input = st.chat_input("Ask me anything about fitness, nutrition, or well-being...")
    
    if user_input:
        st.chat_message("user").markdown(user_input)
        response = model.generate_content(user_input)
        ai_reply = response.text if response.text else "Sorry, I couldn't generate a response."
        with st.chat_message("assistant"):
            st.markdown(ai_reply)

if __name__ == "__main__":
    main()
