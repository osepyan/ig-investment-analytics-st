import streamlit as st
from components.about import about_text
from components.auth import auth
from components.sidebar import show_sidebar
from components.gsheets_connector import DatabaseConnector
from components.basic_metrics import calculate_strategy_stats, describe_profit_loss


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

    if st.checkbox('Show raw data'):
        st.dataframe(momentum_data, use_container_width=True)

    st.subheader('*Momentum Strategy vc HODL BTC*')
    st.line_chart(data=momentum_data, x='Purchase date', y=['Momentum', 'Hodl BTC'])

    st.subheader('*Profit / Loss Desciption*')
    if st.checkbox('Exclude outliers', help='Whether to exclude outliers beyond the range [-500%, 500%]'):
        st.dataframe(describe_profit_loss(momentum_data, True), use_container_width=True)
    else:
        st.dataframe(describe_profit_loss(momentum_data), use_container_width=True)

    st.subheader('*Profit / Loss / Hodl shares*')
    st.bar_chart(calculate_strategy_stats(momentum_data), height=200)

elif st.session_state["authentication_status"] is False:
    st.sidebar.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.sidebar.warning('Please enter your username and password')
