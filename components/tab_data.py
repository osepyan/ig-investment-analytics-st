import streamlit as st
import pandas as pd

from .coinapi_sheets_connector import CoinApiSheetsConnector

def show_coin_api_data():

    coinapi_conn = CoinApiSheetsConnector()
    coin_api_data = coinapi_conn.load_raw_data()
    st.dataframe(coin_api_data)
    # print(coin_api_data.info())