import streamlit as st
import print_src

st.set_page_config(page_title="Printing", page_icon="🖨️")
st.title("Label printing")

with st.form(key="print_form", clear_on_submit=True):
    printing_input = st.text_area(label="Enter your IDs here:", placeholder="...")
    submit = st.form_submit_button(label="Print", help="Sends the IDs above to the printer", type="primary")

    if submit:
        with st.spinner("Printing...", ):
            print_src.app_print_driver(app_input=printing_input)
        st.success("Job done.")

with st.expander("Instructions", expanded=False):
    st.markdown("""Enter an ID or range of IDs in the text box below.
+ You can copy and paste from Opvia.
+ To specify multiple, separate individual ID's with commas, and specify a range using a hyphen. 
+ You can specify repeats using * or x.
+ Only enter one type of ID at a time.
+ For **S**terile or **N**ot **S**terile labels, enter S or NS respectively.

Then press the Print button, and your labels will be magically printed.

**Examples:**""")
    st.markdown("""
| Input                    | Output                                                       |
|--------------------------|--------------------------------------------------------------|
| CB100001                 | 1x CB100001 label                                            |
| CB100001, CB100003       | 1x CB100001 label and 1x CB100003 label.                     |
| CB100001-CB100003        | 1x CB100001, 1xCB100002, 1xCB100003 labels (range)           |
| CB100001*5 or CB100001x5 | 5x CB100001. Multiplication can be performed on a range too. |
""")