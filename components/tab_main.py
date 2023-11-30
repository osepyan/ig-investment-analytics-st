import streamlit as st
import pandas as pd
import numpy as np
from typing import Union
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json


def get_coinmarketcap_price(symbol):
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'

    parameters = {
        'symbol': symbol,
        'convert':'USD'
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': st.secrets['coinmarketcap']['api_key'],
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        return data['data'][symbol][0]['quote']['USD']['price']
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0, normalization_factor: float = 1) -> float:
    """
    Calculate Sharpe Ratio for a given series of returns.

    The Sharpe Ratio is a measure of the risk-adjusted performance of an investment or a trading strategy.
    It is calculated as the average return earned in excess of the risk-free rate per unit of volatility or total risk.

    Parameters:
    - returns (pd.Series): Series of returns.
    - risk_free_rate (float): Annual risk-free rate (default is 0).
    - normalization_factor (float): Normalization factor (default is 1).

    Returns:
    float: Sharpe Ratio.
    """
    excess_returns = returns - risk_free_rate
    sharpe_ratio = excess_returns.mean() / excess_returns.std() / np.sqrt(len(returns) / normalization_factor) if excess_returns.std() != 0 else 0

    return sharpe_ratio

def calculate_sortino_ratio(returns: pd.Series, target_return: Union[float, int]=0, normalization_factor: float=1) -> float:
    """
    Calculate Sortino Ratio for a given series of returns.

    The Sortino Ratio is a variation of the Sharpe Ratio that focuses on the downside risk.
    It is calculated as the average return earned in excess of the target return per unit of downside volatility.

    Parameters:
    - returns (pd.Series): Series of returns.
    - target_return (float or int): Target return rate (default is 0).
    - normalization_factor (float): Normalization factor (default is 1).

    Returns:
    float: Sortino Ratio.
    """
    downside_returns = returns[returns < target_return]
    downside_std_dev = downside_returns.std()
    
    mean_return = returns.mean()
    
    sortino_ratio = (mean_return - target_return) / downside_std_dev / np.sqrt(len(returns)) * normalization_factor if downside_std_dev != 0 else 0
    
    return sortino_ratio

def calculate_max_drawdown(returns: pd.Series) -> float:
    """
    Calculate the Maximum Drawdown, which measures the maximum loss from a peak to a trough.

    Parameters:
    - returns (pd.Series): Series of returns.

    Returns:
    float: Maximum Drawdown.
    """
    wealth_index = (1 + returns).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks) / previous_peaks
    max_drawdown = drawdowns.min()

    return max_drawdown

def calculate_duration_of_losses(returns: pd.Series) -> int:
    """
    Calculate the Duration of Losses, which represents the cumulative time the strategy is in a loss.

    Parameters:
    - returns (pd.Series): Series of returns.

    Returns:
    int: Duration of Losses.
    """
    consecutive_losses = (returns < 0).astype(int)
    periods_in_loss = consecutive_losses.groupby((consecutive_losses != consecutive_losses.shift()).cumsum()).cumsum()
    max_periods_in_loss = periods_in_loss.max()

    return max_periods_in_loss

# @st.cache_data
def calculate_strategy_stats(strategy_data: pd.DataFrame) -> pd.Series:
    """
    Calculate various performance metrics for a given trading strategy based on historical data.

    Parameters:
    - strategy_data (pd.DataFrame): DataFrame containing historical data for the trading strategy.
        It should include the following columns:
            - 'Coin' (str): Tickers of coins (uppercase), for example, 'BTC'.
            - 'Purchase price' (float): Price of coin (Coin).
            - 'Portfolio' (float): Portfolio value at a given date.
            - 'Quantity' (float): Amount of purchased coins (Coin).
            - 'Profit / Loss %' (float): Profitability as Month-over-Month return for each period.

    Returns:
    pd.Series: A series containing calculated performance metrics for the trading strategy.

    Metrics:
    - Life Period: Number of periods (rows) in the strategy data.
    - Profit Count: Number of profitable trades.
    - Loss Count: Number of losing trades.
    - MoM (Month-over-Month): Percentage change in the latest coin price compared to the purchase price.
    - ROI (Return on Investment): Percentage return on investment from the start to the latest period.
    - Monthly Return with Compound Interest: Compound monthly return of the strategy.
    - Mean Profit: Average profit percentage per trade.
    - Mean Loss: Average loss percentage per trade.
    - Median Profit: Median profit percentage per trade.
    - Median Loss: Median loss percentage per trade.
    - Std Profit: Standard deviation of profit percentages.
    - Std Loss: Standard deviation of loss percentages.
    - Maximum Profit: Maximum profit percentage in a single trade.
    - Maximum Loss: Maximum loss percentage in a single trade.
    - Minimum Profit: Minimum profit percentage in a single trade.
    - Minimum Loss: Minimum loss percentage in a single trade.
    - Sharpe Ratio: Risk-adjusted return metric.
    - Sortino Ratio: Risk-adjusted return metric focusing on downside volatility.
    - Max Drawdown: Maximum loss from a peak to a trough.
    - Max Periods in Loss: Cumulative time the strategy is in a loss.

    Note:
    - The function uses additional functions like calculate_sharpe_ratio, calculate_sortino_ratio,
      calculate_max_drawdown, and calculate_duration_of_losses for specific metric calculations.
    """

    # Get latest portfolio coin and load data from Binance exchange
    latest_coin = strategy_data['Coin'].iloc[-1]
    try:
        current_price = get_coinmarketcap_price(f'{latest_coin}')
    except Exception as err:
        st.warning(f'Current price for {latest_coin} is not downloaded!')
        current_price = strategy_data['Sell price'].iloc[-1]

    # Get purchase price
    purchase_price = strategy_data['Purchase price'].iloc[-1]

    # Get start and current portfolio balances
    start_portfolio_balance = strategy_data['Portfolio'].iloc[0]
    current_portfolio_balance = strategy_data['Quantity'].iloc[-1] * current_price

    # Calculate MoM, ROI, and Monthly return with compound interest
    mom = (current_price - purchase_price) / purchase_price
    roi = (current_portfolio_balance - start_portfolio_balance) / start_portfolio_balance
    return_with_compound_interest = (current_portfolio_balance / start_portfolio_balance) ** (1/strategy_data.shape[0]) - 1

    # get all yields of the strategy
    yields = strategy_data['Profit / Loss %'].copy()
    yields.iloc[-1] = mom

    # calculate basic metrics
    profit_metrics = yields[yields > 0].agg({
        'Total': 'sum',
        'Mean': 'mean',
        'Count': 'count',
        'Standard Deviation': 'std',
        'Minimum': 'min',
        'Maximum': 'max',
        'Median': 'median'
    })

    loss_metrics = yields[yields < 0].agg({
        'Total': 'sum',
        'Mean': 'mean',
        'Count': 'count',
        'Standard Deviation': 'std',
        'Minimum': 'min',
        'Maximum': 'max',
        'Median': 'median'
    })

    # Calculate Sharpe Ratio, Sortino Ratio, Max Drawdown, and Duration of Losses
    sharpe_ratio = calculate_sharpe_ratio(yields, normalization_factor=np.sqrt(yields.count()))
    sortino_ratio = calculate_sortino_ratio(yields, normalization_factor=np.sqrt(yields.count()))
    max_drawdown = calculate_max_drawdown(yields)
    duration_of_losses = calculate_duration_of_losses(yields)

    metrics = {
        'Life Period': strategy_data.shape[0],
        'Profit Count': profit_metrics['Count'],
        'Loss Count': loss_metrics['Count'],
        'MoM': mom,
        'ROI': roi,
        'Monthly Return with Compound Interest': return_with_compound_interest,
        'Mean Profit': profit_metrics['Mean'],
        'Mean Loss': loss_metrics['Mean'],
        'Median Profit': profit_metrics['Median'],
        'Median Loss': loss_metrics['Median'],
        'Std Profit': profit_metrics['Standard Deviation'],
        'Std Loss': loss_metrics['Standard Deviation'],
        'Maximum Profit': profit_metrics['Maximum'],
        'Maximum Loss': loss_metrics['Minimum'],
        'Minimum Profit': profit_metrics['Minimum'],
        'Minimum Loss': loss_metrics['Maximum'],
        'Sharpe Ratio': sharpe_ratio,
        'Sortino Ratio': sortino_ratio,
        'Max Drawdown': max_drawdown,
        'Max Periods in Loss': duration_of_losses
    }
    metrics_series = pd.Series(metrics, name='Value')
    metrics_series.index.name = 'Metric'
    
    return metrics_series
    # return pd.DataFrame(metrics, index=[0])

@st.cache_data
def calculate_strategy_share(yields: pd.Series) -> pd.DataFrame:
    """
    Calculate the share of profit, loss, and hodl categories in a trading strategy based on yields.

    Parameters:
    - yields (pd.Series): A pandas Series representing the yields of a trading strategy.

    Returns:
    pd.DataFrame: A DataFrame containing the normalized shares of profit, loss, and hodl categories.
    The index represents the categories ('PROFIT', 'LOSS', 'HODL'), and the only column is the normalized share.

    Example:
    If the yields Series contains profits, losses, and hodl values, the resulting DataFrame might look like:
    ```
         Share
    PROFIT  0.5
    LOSS    0.3
    HODL    0.2
    ```
    """
    return (yields.apply(lambda x: 'profit' if x > 0 else 'loss' if x < 0 else 'hodl')
                                      .value_counts(normalize=True)
                                      .rename(index={'profit': 'PROFIT', 'loss': 'LOSS', 'hodl': 'HODL'})
                                      .to_frame())

@st.cache_data
def describe_profit_loss(data: pd.DataFrame, exclude_outliers: bool=False) -> pd.DataFrame:
    """
    Generate a summary of profit and loss percentages in the given DataFrame.

    Parameters:
    - data (pd.DataFrame): DataFrame containing trading data, including a 'Profit / Loss %' column.
    - exclude_outliers (bool, optional): Whether to exclude outliers beyond the range [-500%, 500%]. Default is False.
    
    Returns:
    pd.DataFrame: A summary DataFrame with descriptive statistics for profit and loss percentages.
    """    
    if exclude_outliers:
        data = data[data['Profit / Loss %'].between(-5, 5)]

    data = data[data['Profit / Loss %'] != 0]
    result = data.groupby(data['Profit / Loss %'] > 0)['Profit / Loss %']\
        .apply(lambda x: x.abs().describe())\
        .unstack()\
        .rename(index={True: 'Profit', False: 'Loss'})
    result.index.name = None
    return result

def show_main_tab(data: pd.DataFrame, hodl_btc_data:pd.DataFrame=None):

    st.subheader('*Raw Data*')
    with st.expander('See Strategy Raw Data'):
        st.dataframe(data, use_container_width=True)

    st.subheader('*Momentum Strategy Key Stats*')
    with st.expander('See Key Stats'):
        momentum_stats = calculate_strategy_stats(data)
        hodl_btc_stats = calculate_strategy_stats(hodl_btc_data)

        strategies_metrics = pd.concat([momentum_stats, hodl_btc_stats], axis=1, keys= ['Momentum', 'Hodl BTC'])

        st.dataframe(strategies_metrics, use_container_width=True)
    st.subheader('*Momentum Strategy vc HODL BTC*')
    st.line_chart(data=data, x='Purchase date', y=['Portfolio', 'Hodl BTC'])

    st.subheader('*Profit / Loss Desciption*')
    if st.checkbox('Exclude outliers', help='Whether to exclude outliers beyond the range [-500%, 500%]'):
        st.dataframe(describe_profit_loss(data, True), use_container_width=True)
    else:
        st.dataframe(describe_profit_loss(data), use_container_width=True)

    st.subheader('*Profit / Loss / Hodl shares*')
    st.bar_chart(calculate_strategy_share(data['Profit / Loss %']), height=200)
