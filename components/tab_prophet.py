import streamlit as st
from .gsheets.sheets_connector import CoinApiSheetsConnector
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly


def show_prophet_tab():
    # get raw data
    spreadsheet = CoinApiSheetsConnector("coinapigsheets")
    df = spreadsheet.get_data_from_sheet("raw_data")

    st.selectbox("Select Coin to Predict Price:", df.columns[1:], index=0, key="coin_to_predict")

    # select data
    coin_to_predict = st.session_state.coin_to_predict
    print(coin_to_predict)
    btc_df = df[["datetime", coin_to_predict]].copy()
    
    # modify df
    btc_df.rename(columns={'datetime': 'ds'}, inplace=True)
    btc_df["ds"] = btc_df["ds"].dt.tz_convert(None)
    btc_df["y"] = btc_df[coin_to_predict].shift(-12)
    btc_df.dropna(inplace=True)

    # instantiating a new Prophet object
    m = Prophet()
    m.fit(btc_df)

    # make future df
    future = m.make_future_dataframe(periods=20, freq='H')

    # predict future prices
    forecast = m.predict(future)

    # draw the forecast
    fig = plot_plotly(m, forecast)
    st.subheader(f"*Forecast {coin_to_predict} Data*")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"*{coin_to_predict} Forecast Components*")
    fig2 = plot_components_plotly(m, forecast)
    st.plotly_chart(fig2, use_container_width=True)
