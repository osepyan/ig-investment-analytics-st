import streamlit as st
from components.tab_main import show_main_tab
from components.about import about_text
from components.tab_corr import show_corr_data
from components.tab_prophet import show_prophet_tab


st.set_page_config(
    page_title='IG Statistics Dashboard', 
    layout="wide",
    menu_items={
        'Get Help': 'https://www.somelink.com/help',
        'Report a bug': "https://www.somelink.com/bug",
        'About': about_text
    }
)

st.header("IG Strategies Analytics")    
main_tab, corr_tab, prophet = st.tabs(['main', 'corr', 'prophet'])
with main_tab:
    show_main_tab()
with corr_tab:
    show_corr_data()
with prophet:
    show_prophet_tab()
