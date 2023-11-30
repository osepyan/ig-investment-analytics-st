import requests
import streamlit as st


def show_prices(your_coin):

    btc = 'BTCUSDT'
    
    btc_response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={btc}')
    btc_data = btc_response.json()

    your_coin_response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={your_coin}')
    your_coin_data = your_coin_response.json()

    if 'btc_price' not in st.session_state:
        st.session_state.btc_price = btc_data['price']
    if 'your_coin_price' not in st.session_state:
        st.session_state.your_coin_price = your_coin_data['price']    

    col1, col2 = st.columns(2)
    with col1:
        st.metric(your_coin_data['symbol'], st.session_state.your_coin_price)
    with col2:
        st.metric(btc_data['symbol'], st.session_state.btc_price)

    st.button('Update prices', on_click=update_prices)
        

def update_prices():
    btc = 'BTCUSDT'
    your_coin = 'LINKUSDT'
    btc_response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={btc}')
    btc_data = btc_response.json()

    your_coin_response = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={your_coin}')
    your_coin_data = your_coin_response.json()
    st.session_state.btc_price = btc_data['price']
    st.session_state.your_coin_price = your_coin_data['price']
