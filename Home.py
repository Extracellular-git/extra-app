import streamlit as st
from PIL import Image

logo = Image.open("/home/runner/Extracellular/extra_app/CoreLogo.png")

st.image(logo, use_column_width="always")

st.title("Welcome to the Extracellular app")
st.write("Have a look through the pages on the sidebar to see what you can do.")
