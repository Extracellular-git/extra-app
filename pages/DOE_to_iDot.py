import pandas as pd
import streamlit as st

import to_idot

#from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide")

st.title("Welcome to the DoE to iDOT setup page")

container = st.container()
# source_path = st.text_input("Path to DoE csv template")

with st.form("File submission"):
    source_file = st.file_uploader("Upload your DoE csv template", ["csv","xlsx"])
    submit_file_button = st.form_submit_button("Submit")

if submit_file_button:

    if source_file == None:
        st.warning("No file uploaded", icon="⚠")
        st.rerun()

    if '.csv' in source_file.name:
        df = pd.read_csv(source_file)
        columns = df.columns
    elif '.xlsx' in source_file.name:
        df = pd.read_excel(source_file)
        columns = df.columns
    else:
        st.warning("File type unknown, trying to read as CSV", icon="⚠")
        df = pd.read_csv(source_file)
        columns = df.columns


    if columns is not None:
        component_name_list = []
        concentration_list = []
        units_list = []
        ncols = len(columns)


    destination_name = st.text_input("name for iDOT file")
    final_well_volume = st.number_input("Final well volume", 0)
    replicates = st.number_input("Number of replicates", 1)

    st.write("Don't forget to check that the conc. units are the same between source file and what is here")
    ui_cols = st.columns(ncols)
    for i, x in enumerate(ui_cols):
        comp_input = x.text_input(f"Component {i+1}", f"{columns[i]}", key=1+i)
        component_name_list.append(comp_input)
        conc_input = x.text_input(f"{columns[i]} conc.", 0, key=100+i)
        concentration_list.append(conc_input)
        units_input = x.selectbox(f"{columns[i]} units", ['mM', 'uM', 'nM', 'mg/mL', 'ug/mL', 'ng/mL', 'x'], key=200+i)
        units_list.append(units_input)

    submit_param_button = st.button("Submit")

    if submit_param_button:
        conc_dict = {}
        for i, name in enumerate(component_name_list):
            conc_dict[name] = float(concentration_list[i])

        finished_file = to_idot.doe_to_idot_main(source_file, final_well_volume, conc_dict, destination_name, replicates=1, orientation='by_columns')

        download_button = st.download_button(
            label="Download finished file",
            data=finished_file,
            file_name=destination_name,
            mime="text/csv"
        )

