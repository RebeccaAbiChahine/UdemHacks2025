import streamlit as st
import google.generativeai as genai
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
import requests
from geopy.distance import geodesic

# Configure the Gemini API
GEMINI_API_KEY = "AIzaSyA5-LfT8Wcf02ABUKySXOZpNhQd5sDajtg"
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

# Function to fetch weather data
def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,weathercode"
    try:
        response = requests.get(url).json()
        if "hourly" in response:
            return response["hourly"]
    except:
        return None
    return None

# Function to fetch paid activity places
def fetch_paid_activity_places(user_address, distance_km):
    prompt = (f"Find paid gyms or activity places like Éconofitness or World Gym near {user_address} within {distance_km} km. "
              f"Provide their names and real addresses.")
    response = model.generate_content(prompt)
    places = [place.strip() for place in response.text.split("\n") if place.strip()]
    return places[:5]

# Function to suggest activities including weather data
def suggest_places(mood, activity_type, intensity, group_preference, cost_option, user_address, distance_km, weather):
    weather_desc = ""
    if weather:
        temp = weather['temperature_2m'][0]
        weather_desc = f"The current temperature is {temp}°C. "
    
    if cost_option.lower() == "paid":
        return fetch_paid_activity_places(user_address, distance_km)
    else:
        prompt = (f"I am located at {user_address}. {weather_desc}I feel {mood}, I want to {activity_type.lower()}, and prefer {intensity.lower()} intensity. "
                  f"I prefer to be {group_preference.lower()} and the activity to be {cost_option.lower()}. "
                  f"Within {distance_km} km of my location, suggest specific parks, gyms, or activities with their names only.")
        response = model.generate_content(prompt)
        suggestions = [suggestion.strip() for suggestion in response.text.split("\n") if suggestion.strip()]
        
        if not suggestions or len(suggestions) < 5:
            fallback_suggestions = [
                "Nearby small park 🌳",
                "Local community gym 🏋️",
                "Relaxation area at a café ☕",
                "Popular walking trail 🚶‍♀️",
                "Yoga studio around you 🧘"
            ]
            suggestions.extend(fallback_suggestions[:5 - len(suggestions)])

        return suggestions[:5]

# Streamlit UI
st.set_page_config(page_title="Fitness Forecast - AI Wellness Chatbot", page_icon="💪", layout="wide")
st.markdown("<h1 style='text-align: center; color: #008CBA;'>💪 Fitness Forecast - AI Wellness Chatbot</h1>", unsafe_allow_html=True)

# Address input
user_query = st.text_input("Enter your address:")

if user_query:
    lat, lon, address = get_coordinates_and_address(user_query)
    if lat and lon:
        weather = get_weather(lat, lon)
        if weather:
            st.markdown(f"""
                ### 🌤️ Today's Weather
                - **Temperature:** {weather['temperature_2m'][0]}°C
            """)
        else:
            st.warning("Unable to fetch weather data. Please try again later.")

        # Collect user inputs
        mood = st.selectbox("How are you feeling today?", ["Select an option", "Happy", "Stressed", "Bored", "Sad", "Energetic", "Tired"])
        activity_type = st.radio("Would you like to:", ["Select an option", "Workout", "Relax"])
        intensity = st.radio("Select intensity:", ["Select an option", "High", "Low"])
        group_preference = st.radio("Would you prefer to be:", ["Select an option", "Alone", "In a group"])
        cost_option = st.radio("Do you want the activity to be free or paid?", ["Select an option", "Free", "Paid"])
        distance = st.slider("Maximum distance you are willing to travel (in km):", 1, 50, 10)

        if mood != "Select an option" and activity_type != "Select an option" and intensity != "Select an option" and group_preference != "Select an option" and cost_option != "Select an option":
            activity_suggestions = suggest_places(mood, activity_type, intensity, group_preference, cost_option, user_query, distance, weather)
            
            st.markdown("### 🤖 Activity Suggestions Based on Your Preferences")
            map = folium.Map(location=[lat, lon], zoom_start=12)
            
            # Add user's address as a marker on the map
            folium.Marker(
                [lat, lon],
                popup=f"User's Address: {address}",
                icon=folium.Icon(color='blue')
            ).add_to(map)

            valid_suggestions = False
            
            for suggestion in activity_suggestions:
                suggestion_lat, suggestion_lon, suggestion_address = get_coordinates_and_address(suggestion)
                if suggestion_lat and suggestion_lon:
                    distance_to_place = geodesic((lat, lon), (suggestion_lat, suggestion_lon)).kilometers
                    if distance_to_place <= distance:
                        valid_suggestions = True
                        folium.Marker(
                            [suggestion_lat, suggestion_lon],
                            popup=f"{suggestion}<br>{suggestion_address or 'Address not available'}",
                            icon=folium.Icon(color='green')
                        ).add_to(map)
                        st.write(f"- **{suggestion}**: {suggestion_address or 'Address not available'}")
                    
            if not valid_suggestions:
                st.warning("No valid locations found within the specified distance.")
            
            folium_static(map)
        else:
            st.warning("Please complete all fields to proceed.")
