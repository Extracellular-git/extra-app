import base64
import dilution_calc as dc
#import doe_to_idot as dti
import pandas as pd
#import qPCR_to_idot as qti
import streamlit as st

#from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide")

def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
        background-size: cover
    }}
    </style>
    """,
    unsafe_allow_html=True
    )
#add_bg_from_local('Screenshot 2023-03-30 155702.png')
add_bg_from_local("ExtracellularCorporateWallpaper.png")
st.title("Welcome to the cell culture dilution page")

container = st.container()

st.sidebar.header("Culture parameters")
options_form = st.sidebar.form("Options Form")
submit_sidebar = options_form.form_submit_button()

source_conc = options_form.text_input("Source concentration")
if source_conc is not '':
    source_conc = int(source_conc)
target_volume = options_form.text_input("Target volume")
if target_volume is not '':
    target_volume = int(target_volume)
target_conc = options_form.text_input("Target concentration")
if target_conc is not '':
    target_conc = int(target_conc)

if submit_sidebar:
    result = dc.conc_calc(source_conc, target_conc, target_volume)
    st.write(result)