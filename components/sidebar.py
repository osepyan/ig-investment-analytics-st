import streamlit as st


def show_sidebar():
    st.sidebar.write(f'Welcome {st.session_state["name"]}')
