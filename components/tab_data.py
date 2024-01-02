from typing import Optional, Dict, List
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from .gsheets.sheets_connector import CoinApiSheetsConnector

def retrieve_coin_api_data(gsheet_connection: str, sheet: str) -> pd.DataFrame:
    """
    Retrieves coin API data from a Google Sheet.

    Parameters:
    - gsheet_connection (str): Google Sheets connection string.
    - sheet (str): Name of the sheet.

    Returns:
    pd.DataFrame: Coin API data.
    """
    placeholder = st.empty()
    status = placeholder.status("Downloading strategy data...  :new_moon:")

    with status:
        spreadsheet = CoinApiSheetsConnector(gsheet_connection)
        status.update(label="Download complete!", state="complete")
    placeholder.empty()

    df = spreadsheet.get_data_from_sheet(sheet)
    return df

def find_negative_correlation_coins(correlation_matrix: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Finds coins with negative correlation.

    Parameters:
    - correlation_matrix (pd.DataFrame): Correlation matrix.

    Returns:
    Dict[str, Dict[str, float]]: Dictionary of coins with negative correlation.
    """
    coins_with_negative_corr = {}

    for base_coin in correlation_matrix.index:
        negative_corr_coins = {}

        for coin in correlation_matrix.columns:
            if base_coin != coin and correlation_matrix.loc[base_coin, coin] < 0:
                correlation_value = correlation_matrix.loc[base_coin, coin]
                negative_corr_coins[coin] = correlation_value

        coins_with_negative_corr[base_coin] = negative_corr_coins

    return coins_with_negative_corr

def visualize_negative_correlations(coins_with_negative_corr: Dict[str, Dict[str, float]],
                                    correlation_threshold: float = -0.5,
                                    selected_base_coins: Optional[List[str]] = None):
    """
    Visualizes coins with negative correlation.

    Parameters:
    - coins_with_negative_corr (Dict[str, Dict[str, float]]): Dictionary of coins with negative correlation.
    - correlation_threshold (float): Correlation threshold.
    - selected_base_coins (Optional[List[str]]): List of selected base coins.
    """
    fig = go.Figure()

    for base_coin, negative_corr_coins in coins_with_negative_corr.items():
        if selected_base_coins and base_coin not in selected_base_coins:
            continue

        for coin, correlation_value in negative_corr_coins.items():
            if correlation_value < correlation_threshold:
                fig.add_trace(go.Scatter(
                    x=[base_coin, coin],
                    y=[0, correlation_value],
                    mode='lines+markers',
                    name=f'{base_coin} to {coin}',
                    text=f'Correlation: {correlation_value:.2f}'
                ))

    fig.update_layout(
        title=f'Negative Correlations (Base Coins: {selected_base_coins if selected_base_coins else "All"})',
        xaxis_title='Coins',
        yaxis_title='Correlation',
        showlegend=True,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

def show_coin_api_data():
    coin_api_data = retrieve_coin_api_data('coinapigsheets', 'raw_data')
    correlation_matrix = coin_api_data.corr(numeric_only=True)

    st.subheader('*Correlation Visualization*')
    correlation_structure = find_negative_correlation_coins(correlation_matrix)

    corr_container = st.container()
    with corr_container:
        col1, col2 = st.columns(2)
        with col1:
            correlation_threshold = st.slider('Select Correlation Threshold:', min_value=-1.0, max_value=0.0, value=-0.5, step=0.1)
        with col2:
            base_coin_options = list(correlation_structure.keys())
            selected_base_coins = st.multiselect('Select Base Coins:', base_coin_options)

    visualize_negative_correlations(correlation_structure, correlation_threshold=correlation_threshold, selected_base_coins=selected_base_coins)

    st.subheader('*Correlation Matrix*')
    with st.expander('See Correlation Matrix'):
        st.dataframe(correlation_matrix)

    st.subheader('*Coin Api Raw Data*')
    with st.expander('See Strategy Raw Data'):
        st.dataframe(coin_api_data, use_container_width=True)
