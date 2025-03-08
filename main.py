from google import genai
import streamlit as st
import pandas as pd


client = genai.Client(api_key="AIzaSyBFBDkj30pm2HJSRa78-KVKgj0-CPl4UCU")
response = client.models.generate_content(
    model="gemini-2.0-flash", contents="How are you?"
)
print(response.text)
##streamlit below
import numpy as np

dataframe = np.random.randn(10, 20)
st.dataframe(dataframe)