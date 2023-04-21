import base64
import doe_to_idot as dti
import pandas as pd
import qPCR_to_idot as qti
import streamlit as st

from st_aggrid import AgGrid, GridOptionsBuilder


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
add_bg_from_local('Screenshot 2023-03-30 155702.png')    

st.title("Welcome to the DoE to iDOT setup page")

#df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})  # Original csv
# df = pd.read_excel('qPCR_assay_template_v1.xlsx', sheet_name='Sheet2')

# st.write(df)
container = st.container()
st.sidebar.header("Assay parameters")
options_form = st.sidebar.form("Options Form")
source_path = st.text_input("Path to DoE csv template")
columns = None
if '.csv' in source_path:
    df = pd.read_csv(source_path)
    columns = df.columns
    st.write(columns, 'Components')
elif '.xlsx' in source_path:
    df = pd.read_excel(source_path)
    columns = df.columns
    st.write(columns)


destination_path = st.text_input("Path for iDOT file")

ncol = st.sidebar.number_input("Number of components", 0, 20, 1)
ncol = int(ncol)
cols = st.columns(ncol)
final_well_volume = st.sidebar.number_input("Final well volume", 0)
replicates = st.sidebar.number_input("Number of replicates", 1)
component_name_list = []
concentration_list = []
units_list = []
st.text("Don't forget to check that the conc. units are the same between source file and what is here")
submit_sidebar = options_form.form_submit_button()

if columns is not None:
    for i, x in enumerate(cols):
        comp_input = x.text_input(f"Component {i+1}", f"{columns[i]}", key=1+i)
        component_name_list.append(comp_input)
        conc_input = x.text_input(f"{columns[i]} conc.", 0, key=100+i)
        concentration_list.append(conc_input)
        units_input = x.selectbox(f"{columns[i]} units", ['mM', 'uM', 'nM', 'mg/mL', 'ug/mL', 'ng/mL'], key=200+i)
        units_list.append(units_input)
        #input = x.expander(f"{component_name_list[i]} conc.")

if submit_sidebar:
    conc_dict = {}
    for i, name in enumerate(component_name_list):
        conc_dict[name] = float(concentration_list[i])
        dti.doe_to_idot_main(source_path, final_well_volume, conc_dict, destination_path, replicates = 1, orientation ='by_columns')
    


    
    # x.text_input("Units", key=200+i)

# for i, y in enumerate(cols):
#     y.number_input(f"Component {i+1} concentration")

# new_tab = st.text_input("Tab label", "New Tab")
# if st.button("Add tab"):
#     st.session_state["tabs"].append(new_tab)
#     st.experimental_rerun()