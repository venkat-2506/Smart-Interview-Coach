"""Streamlit frontend entry point."""

import streamlit as st

APP_TITLE = "Smart Interview Coach"
APP_SUBTITLE = "AI-Powered Interview Preparation Platform"
APP_VERSION = "1.0"

st.set_page_config(page_title=APP_TITLE, layout="wide")

st.title(APP_TITLE)
st.subheader(APP_SUBTITLE)

st.sidebar.header("Home")

st.write("Welcome to Smart Interview Coach.")
st.write("Current version")
st.write(f"Version {APP_VERSION}")