import streamlit as st
import pandas as pd
from base64 import b64encode
from pyDOE2 import ff2n


def create_design(n_factors, factor_levels, responses=None):
    design = ff2n(n_factors)
    design = (design + 1) / 2 * (factor_levels[1] - factor_levels[0]) + factor_levels[0]
    columns = [f"Factor {i+1}" for i in range(n_factors)]
    if responses:
        design = pd.concat([design, pd.DataFrame(responses, columns=["Response"])], axis=1)
        columns += ["Response"]
    return pd.DataFrame(design, columns=columns)


def download_csv(df):
    csv = df.to_csv(index=False)
    href = f'<a href="data:file/csv;base64,{b64encode(csv.encode()).decode()}" download="design.csv">Download CSV</a>'
    return href


st.title("Full Factorial DOE Design Generator")

n_factors = st.number_input("Number of factors", value=2, min_value=1)
factor_levels = st.text_input("Factor levels (comma-separated)", value="-1,1").split(",")
factor_levels = [float(l) for l in factor_levels]

has_responses = st.checkbox("Include responses")

if has_responses:
    response_values = st.text_input("Response values (comma-separated)").split(",")
    response_values = [float(r) for r in response_values]
else:
    response_values = None

if st.button("Generate Design"):
    design = create_design(n_factors, factor_levels, response_values)
    st.write(design)
    st.markdown(download_csv(design), unsafe_allow_html=True)
