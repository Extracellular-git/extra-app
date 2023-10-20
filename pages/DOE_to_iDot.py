import pandas as pd
import streamlit as st
import tempfile

import to_idot

session = st.session_state

#from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide")

st.title("Welcome to the DoE to iDOT setup page")

if "source_file" not in session:
    session.source_file = None
if "file_done" not in session:
    session.file_done = False
if "in_df" not in session:
    session.in_df = None
if "params_done" not in session:
    session.param_done = False

with st.form("File submission"):
    source_file = st.file_uploader("Upload your DoE csv template", ["csv","xlsx"])
    session.source_file = source_file
    submit_file_button = st.form_submit_button("Submit")

if submit_file_button:
    session.file_done = True

if session.file_done:

    if source_file == None:
        st.warning("No file uploaded", icon="⚠")
        st.rerun()

    try:
        df = pd.read_csv(source_file)
        columns = df.columns
    except UnicodeDecodeError:
        df = pd.read_excel(source_file)
        columns = df.columns
    else:
        st.warning("File type unknown, use CSV or XLSX", icon="⚠")


    if columns is not None:
        component_name_list = []
        concentration_list = []
        units_list = []
        ncols = len(columns)

    session.in_df = df

    data_preview=st.expander("Preview", expanded=False)
    data_preview.dataframe(session.in_df, use_container_width=True)

    destination_name = st.text_input("Name for iDOT file")
    final_well_volume = st.number_input("Final well volume", 0)
    replicates = st.number_input("Number of replicates", 1)
    orientation_pick = st.selectbox("Orientation by rows or columns?", ["Rows", "Columns"], index=0)
    if orientation_pick == "Rows":
        orientation = "by_rows"
    else:
        orientation = "by_columns"

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
        session.param_done = True

if (session.file_done and session.param_done):
    conc_dict = {}
    for i, name in enumerate(component_name_list):
        conc_dict[name] = float(concentration_list[i])

    stringstore = None

    with tempfile.TemporaryFile(mode="w+", newline='') as finished_file:
        to_idot.doe_to_idot_main(session.in_df, final_well_volume, conc_dict, finished_file, replicates=replicates, orientation=orientation)
        finished_file.seek(0)
        stringstore = finished_file.read()

    download_button = st.download_button(
        label="Download finished file",
        data=stringstore,
        file_name=destination_name,
        mime="text/csv"
    )

