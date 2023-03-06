import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

import plotly.express as px

st.set_page_config(layout="wide")

# Add a title and intro text
st.title('CEC Application')
st.text('This is a web app to allow exploration of CEC Statistics')

# Sidebar setup
st.sidebar.title('Sidebar')
upload_file = st.sidebar.file_uploader('Upload a file containing CEC data')

# Check if file has been uploaded
if upload_file is not None:
    CEC = pd.read_excel(upload_file)
    CEC_Courbe = pd.read_excel(upload_file, sheet_name=1)
    st.session_state['CEC'] = CEC
    st.session_state['CEC_Courbe'] = CEC_Courbe
