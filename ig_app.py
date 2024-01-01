import streamlit as st
from components.tab_main import show_main_tab
from components.about import about_text
from components.auth import auth
from components.gsheets_connector import DatabaseConnector
from components.tab_data import show_coin_api_data


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
authenticator.login('Login', 'main')

if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'main', key='unique_key')

    st.header("IG Strategies Analytics")

    conn = DatabaseConnector()
    momentum_data = conn.get_momentum_strategy_data()
    hodl_btc_data = conn.get_hodl_btc_strategy_data()

    tab1, tab2 = st.tabs(['main', 'g sheet'])
    with tab1:    
        show_main_tab(momentum_data, hodl_btc_data)
    with tab2:
        show_coin_api_data()

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
