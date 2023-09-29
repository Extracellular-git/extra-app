import streamlit as st

import to_idot

#from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(layout="wide")

st.title("Welcome to the qPCR setup page")

container = st.container()
st.sidebar.header("Assay parameters")
options_form = st.sidebar.form("Options Form")
source_path = st.text_input("Path to excel template")
with_idot_choice = st.checkbox('Plate with the iDot?')
target_path = st.text_input("Path for idot file")
dna_volume = options_form.text_input("Volume of DNA in reaction", value = 1)
dna_volume = int(dna_volume)
primer_volume = options_form.text_input("Volume of primer in reaction", value=2)
primer_volume = int(primer_volume)
number_primer_tubes = options_form.text_input("Number of primer tubes", value=1)
number_primer_tubes = int(number_primer_tubes)
final_reaction_volume = options_form.text_input("Final reaction volume", value=10)
final_reaction_volume = int(final_reaction_volume)
CFX_choice = st.checkbox('Create a CFX plate template file?')
target_path_plate = st.text_input("Path for CFX file")
submit_sidebar = options_form.form_submit_button()
if submit_sidebar:
    path = source_path
    if with_idot_choice:
        df = to_idot.qPCR_to_idot_main(path, target_path, dna_volume, primer_volume, final_reaction_volume/2, number_primer_tubes)
    if CFX_choice:
        df = to_idot.plate_template_gen(path)
        to_idot.generate_csv_file(target_path_plate, df, idot_header=False)
    
