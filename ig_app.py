import streamlit as st
from components.tab_main import show_main_tab
from components.tab_exchange import show_prices
from components.about import about_text
from components.auth import auth
from components.sidebar import show_sidebar
from components.gsheets_connector import DatabaseConnector


# Configures the default settings of the page
st.set_page_config(
    page_title='IG Statistics Dashboard', 
    layout="wide",
    menu_items={
        'Get Help': 'https://www.somelink.com/help',
        'Report a bug': "https://www.somelink.com/bug",
        'About': about_text
    }
)

authenticator = auth()
authenticator.login('Login', 'sidebar')

if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'sidebar', key='unique_key')
    show_sidebar()

    st.header("IG Strategies Analytics")

    conn = DatabaseConnector()
    momentum_data = conn.get_strategy_data()

    tab1, tab2 = st.tabs(['main', 'exchange'])
    with tab1:    
        show_main_tab(momentum_data)
    with tab2:
        show_prices("LINKUSDT")

elif st.session_state["authentication_status"] is False:
    st.sidebar.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.sidebar.warning('Please enter your username and password')
