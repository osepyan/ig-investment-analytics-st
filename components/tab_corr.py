from typing import Dict
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from .gsheets.sheets_connector import CoinApiSheetsConnector


st.cache_data(ttl=600)
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

st.cache_data(ttl=600)
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

st.cache_data(ttl=600)
def visualize_negative_correlations(coins_with_negative_corr: Dict[str, Dict[str, float]]):
    """
    Visualizes coins with negative correlation.

    Parameters:
    - coins_with_negative_corr (Dict[str, Dict[str, float]]): Dictionary of coins with negative correlation.
    - correlation_threshold (float): Correlation threshold.
    - selected_base_coins (Optional[List[str]]): List of selected base coins.
    """
    fig = go.Figure()

    selected_base_coins = st.session_state.selected_base_coins
    for base_coin, negative_corr_coins in coins_with_negative_corr.items():
        if selected_base_coins and base_coin not in selected_base_coins:
            continue

        for coin, correlation_value in negative_corr_coins.items():
            if correlation_value < st.session_state.correlation_threshold:
                fig.add_trace(go.Scatter(
                    x=[base_coin, coin],
                    y=[0, correlation_value],
                    mode='lines+markers',
                    name=f'{base_coin} to {coin}',
                    text=f'Correlation: {correlation_value:.2f}'
                ))

    fig.update_layout(
        title = f'Negative Correlations (Base Coins: {", ".join(selected_base_coins) if selected_base_coins else "All"})',
        xaxis_title='Coins',
        yaxis_title='Correlation',
        showlegend=True,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

st.cache_data(ttl=600)
def visualize_line_chart(coins_with_negative_corr, coin_api_data):
    fig = go.Figure()
    
    selected_base_coins = st.session_state.selected_base_coins
    y = []
    for base_coin in selected_base_coins:
        if base_coin not in y:
            y.append(base_coin)
        for corr_coin, corr_value in coins_with_negative_corr[base_coin].items():
            if corr_coin not in y and corr_value < st.session_state.correlation_threshold:
                y.append(corr_coin)
    
    fig = px.line(coin_api_data, x="datetime", y=y)

    fig.update_layout(
        title="Price Percentage Change Over Time",
        xaxis_title='datetime',
        yaxis_title='usd price',
        showlegend=True,
        height=600
    )

    fig.update_layout({"uirevision": "foo"}, overwrite=True)
    fig.for_each_trace(lambda trace: trace.update(visible="legendonly") 
                   if trace.name not in selected_base_coins else ())
    
    if st.session_state.use_log_scale:
        fig.update_layout(yaxis_type="log")
    
    st.plotly_chart(fig, use_container_width=True)

st.cache_data(ttl=600)
def drop_duplicates(data: pd.DataFrame, condition_column: str) -> pd.DataFrame:
    duplicate_indexes = data[data.duplicated(condition_column)].index
    return data.drop(duplicate_indexes)

def show_params_container(base_coins_list) -> None:
    params_container = st.container()
    with params_container:
        col1, col2 = st.columns(2)
        with col1:
            st.slider("Select Correlation Threshold:", min_value=-1.0, max_value=0.0, value=0.0, step=0.1, key="correlation_threshold")
            st.toggle("hide graph", value=False, key="hide_corr_graph")
        with col2:
            st.multiselect("Select Base Coins:", base_coins_list, key="selected_base_coins")
            st.toggle("use log scale", value=False, key="use_log_scale")

st.cache_data(ttl=600)
def show_charts_container(correlation_structure: Dict[str, Dict[str, float]], coin_pct_change: pd.DataFrame) -> None:
    charts_container = st.container()
    selected_base_coins = st.session_state.selected_base_coins

    if st.session_state.hide_corr_graph:
        with charts_container:
            if selected_base_coins:
                visualize_line_chart(correlation_structure, coin_pct_change)
    else:
        with charts_container:
            corr_chart_col, line_chart_col = st.columns(2)
            with corr_chart_col:
                visualize_negative_correlations(correlation_structure)
            with line_chart_col:
                if selected_base_coins:
                    visualize_line_chart(correlation_structure, coin_pct_change)

st.cache_data(ttl=600)
def show_corr_data():
    coin_api_data = retrieve_coin_api_data('coinapigsheets', 'raw_data')
    coin_api_data_cleaned = drop_duplicates(coin_api_data, 'datetime')

    coin_pct_change = coin_api_data_cleaned.select_dtypes(include=['number']).pct_change()
    coin_pct_change['datetime'] = coin_api_data_cleaned['datetime']

    correlation_matrix = coin_api_data_cleaned.corr(numeric_only=True)

    st.subheader('*Correlation Visualization*')
    correlation_structure = find_negative_correlation_coins(correlation_matrix)
    show_params_container(list(correlation_structure.keys()))
    show_charts_container(correlation_structure, coin_pct_change)

    st.subheader('*Correlation Matrix*')
    with st.expander('See Correlation Matrix'):
        st.dataframe(correlation_matrix)

    st.subheader('*Coin Api Raw Data*')
    with st.expander('See Strategy Raw Data'):
        st.dataframe(coin_api_data_cleaned, use_container_width=True)
