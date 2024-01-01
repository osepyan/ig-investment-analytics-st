import streamlit as st
import pandas as pd
import numpy as np
import itertools

from typing import Union, Tuple
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects


@st.cache_data(ttl=600)
def get_coinmarketcap_price(symbol: str) -> Union[float, None]:
    """
    Get the current price of a cryptocurrency from CoinMarketCap.

    Parameters:
    - symbol (str): The symbol of the cryptocurrency (e.g., 'BTC').

    Returns:
    float: The current price of the cryptocurrency in USD. Returns None in case of errors.

    Raises:
    - ConnectionError: If there is a problem with the network connection.
    - Timeout: If the request to CoinMarketCap times out.
    - TooManyRedirects: If there are too many redirects in the request.
    """
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'

    parameters = {
        'symbol': symbol,
        'convert': 'USD'
    }

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': st.secrets['coinmarketcap']['api_key'],
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = response.json()
        return data['data'][symbol][0]['quote']['USD']['price']
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        st.error(f"Unable to fetch data from CoinMarketCap. Please check your internet connection and try again.")
        return None

@st.cache_data(ttl=3600)
def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, normalization_factor: int = 1) -> float:
    """
    Calculate Sharpe Ratio for a given series of returns.

    The Sharpe Ratio is a measure of the risk-adjusted performance of an investment or a trading strategy.
    It is calculated as the average return earned in excess of the risk-free rate per unit of volatility or total risk.

    Parameters:
    - returns (pd.Series): Series of returns.
    - risk_free_rate (float): Annual risk-free rate (default is 0).
    - normalization_factor (int): Number of periods over which returns are measured (e.g., number of days).
      If returns represent daily returns, normalization_factor should be the total number of days.

    Returns:
    float: Sharpe Ratio. A higher Sharpe Ratio indicates better risk-adjusted performance.
    """
    if returns.std() > 0:
        sharpe_ratio = (returns.mean() - risk_free_rate) / (returns.std() * np.sqrt(normalization_factor))
    else:
        sharpe_ratio = 0.0

    return sharpe_ratio

@st.cache_data(ttl=3600)
def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0, normalization_factor: float=1) -> float:
    """
    Calculate Sortino Ratio for a given series of returns.

    The Sortino Ratio is a variation of the Sharpe Ratio that focuses on the downside risk.
    It is calculated as the average return earned in excess of the target return per unit of downside volatility.

    Parameters:
    - returns (pd.Series): Series of returns.
    - risk_free_rate (float): Annual risk-free rate (default is 0).
    - normalization_factor (float): Number of periods over which returns are measured (e.g., number of days).
      If returns represent daily returns, normalization_factor should be the total number of days.

    Returns:
    float: Sortino Ratio. A higher Sortino Ratio indicates better risk-adjusted performance.
    """
    downside_returns = returns[returns < 0]
    downside_std_dev = downside_returns.std()
    
    if downside_std_dev > 0:
        sortino_ratio = (returns.mean() - risk_free_rate) / (downside_std_dev * np.sqrt(normalization_factor))
    else:
        sortino_ratio = 0
    
    return sortino_ratio

@st.cache_data(ttl=3600)
def calculate_max_drawdown(returns: pd.Series) -> float:
    """
    Calculate the Maximum Drawdown, which measures the maximum loss from a peak to a trough.

    Parameters:
    - returns (pd.Series): Series of returns.

    Returns:
    float: Maximum Drawdown. A measure of the maximum loss from a peak to a trough.
    """
    wealth_index = (1 + returns).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdowns = (wealth_index - previous_peaks) / previous_peaks
    max_drawdown = drawdowns.min()

    return max_drawdown

@st.cache_data(ttl=3600)
def calculate_duration_of_losses(returns: pd.Series) -> int:
    """
    Calculate the Duration of Losses, which represents the cumulative time the strategy is in a loss.

    Parameters:
    - returns (pd.Series): Series of returns.

    Returns:
    int: Duration of Losses. Cumulative time the strategy is in a loss.
    """
    consecutive_losses = (returns < 0).astype(int)
    periods_in_loss = consecutive_losses.groupby((consecutive_losses != consecutive_losses.shift()).cumsum()).cumsum()
    max_periods_in_loss = periods_in_loss.max()

    return max_periods_in_loss

@st.cache_data(ttl=600)
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
    StrategyKeyMetrics: A NamedTuple containing calculated performance metrics for the trading strategy.

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
    # Get start and current portfolio balances
    start_portfolio_balance = strategy_data['Portfolio'].iloc[0]
    current_portfolio_balance = strategy_data['Portfolio'].iloc[-1]
    months_count = strategy_data.shape[0] - 1

    # Calculate ROI, and Monthly return with compound interest
    roi = (current_portfolio_balance - start_portfolio_balance) / start_portfolio_balance
    
    try:
        return_with_compound_interest = (current_portfolio_balance / start_portfolio_balance) ** (1/months_count) - 1
    except ZeroDivisionError:
        return_with_compound_interest = 0
        
    # get all yields of the strategy
    yields = strategy_data['Profit / Loss %'].copy()

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
    sharpe_ratio = calculate_sharpe_ratio(yields, normalization_factor=yields.count())
    sortino_ratio = calculate_sortino_ratio(yields, normalization_factor=yields.count())
    max_drawdown = calculate_max_drawdown(yields)
    duration_of_losses = calculate_duration_of_losses(yields)

    metrics = {
        'life_period': strategy_data.shape[0],
        'profit_count': profit_metrics['Count'],
        'loss_count': loss_metrics['Count'],
        'month_over_month': strategy_data['Profit / Loss %'].iloc[-1],
        'return_on_investment': roi,
        'monthly_return_with_compound_interest': return_with_compound_interest,
        'average_return': strategy_data['Profit / Loss %'].mean(),
        'volatility': strategy_data['Profit / Loss %'].std(),
        'mean_profit': profit_metrics['Mean'],
        'mean_loss': loss_metrics['Mean'],
        'median_profit': profit_metrics['Median'],
        'median_loss': loss_metrics['Median'],
        'std_profit': profit_metrics['Standard Deviation'],
        'std_loss': loss_metrics['Standard Deviation'],
        'max_profit': profit_metrics['Maximum'],
        'max_loss': loss_metrics['Minimum'],
        'min_profit': profit_metrics['Minimum'],
        'min_loss': loss_metrics['Maximum'],
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'max_drawdown': max_drawdown,
        'duration_of_losses': duration_of_losses
    }
    metrics_series = pd.Series(metrics, name='Value')
    metrics_series.index.name = 'Metric'

    return metrics_series

@st.cache_data(ttl=600)
def update_portfolio_current_balance(strategy_data: pd.DataFrame) -> pd.DataFrame:
    """
    Update the current balance of the portfolio based on the latest market data.

    Parameters:
    - strategy_data (pd.DataFrame): DataFrame containing portfolio data.

    Returns:
    pd.DataFrame: Updated DataFrame with the current balance information.
    """
    try:
        if 'Coin' not in strategy_data.columns or 'Purchase price' not in strategy_data.columns or 'Quantity' not in strategy_data.columns:
            st.warning("Missing necessary columns in strategy_data. Unable to update portfolio balance.")
            return strategy_data
        
        if strategy_data.empty:
            st.warning("Empty strategy_data. Unable to update portfolio balance.")
            return strategy_data

        latest_coin = strategy_data['Coin'].iloc[-1]

        current_price = get_coinmarketcap_price(f'{latest_coin}')
        purchase_price = strategy_data['Purchase price'].iloc[-1]

        current_rate_of_return = (current_price - purchase_price) / purchase_price
        current_portfolio_balance = strategy_data['Quantity'].iloc[-1] * current_price

        strategy_data.loc[strategy_data.index[-1], 'Sell price'] = current_price
        strategy_data.loc[strategy_data.index[-1], 'Profit / Loss %'] = current_rate_of_return
        strategy_data.loc[strategy_data.index[-1], 'Portfolio'] = current_portfolio_balance

        return strategy_data
    
    except (KeyError, IndexError) as e:
        st.warning(f'Error updating current balance for {latest_coin}: {e}')
        return strategy_data

@st.cache_data(ttl=600)
def calculate_compound_interest_dynamics(portfolio_balance: pd.Series, dates: pd.Series) -> pd.Series:
    """
    Calculate the compound interest dynamics based on the portfolio balance over time.

    Parameters:
    - portfolio_balance (pd.Series): Series of portfolio balances.
    - dates (pd.Series): Series of dates corresponding to the portfolio balances.

    Returns:
    pd.Series: Compound interest dynamics.
    """
    start_portfolio_balance = portfolio_balance.iloc[0]
    compound_interests = pd.Series(index=dates, dtype=float)
    
    for month, current_balance in zip(itertools.count(), portfolio_balance):
        try:
            compound_interests[dates[month]] = (current_balance / start_portfolio_balance) ** (1 / month) - 1
        except ZeroDivisionError:
            compound_interests[dates[month]] = 0

    return compound_interests

def show_main_key_stats(key_stats: pd.Series) -> None:
    """
    Display the main key stats of the strategy on the screen.

    Parameters:
    - key_stats (pd.Series): Series containing key statistics of the strategy.
    """
    container = st.container()
    with container:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric('MoM', 
                      f"{round(key_stats['month_over_month']*100, 2)}%",
                      help='Month-Over-Month')
        with col2:
            st.metric('CI', 
                      f"{round(key_stats['monthly_return_with_compound_interest']*100, 2)}%", 
                      help='Return with Compound Interest')
        with col3:
            st.metric('Average return',
                      f"{round(key_stats['average_return']*100, 2)}%",
                      help='The Mean Value of the Profit / Loss for all periods ')
        with col4:
            st.metric('Volatility',
                      f"{round(key_stats['volatility']*100, 2)}%",
                      help='The Standart Deviation of the Profit / Loss for all periods ')            
        with col5:
            st.metric('Mean Profit', 
                      f"{round(key_stats['mean_profit']*100, 2)}%",
                      help='The Average Value of the Profit')
        with col6:
            st.metric('Mean Loss', 
                      f"{round(key_stats['mean_loss']*100, 2)}%",
                      help='The Average Value of the Loss')

@st.cache_data(ttl=600)
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

@st.cache_data(ttl=600)
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

def exclude_outliers(strategy_data: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude outliers from the strategy data based on the 'Profit / Loss %' column.

    Parameters:
    - strategy_data (pd.DataFrame): DataFrame containing strategy data.

    Returns:
    pd.DataFrame: DataFrame with outliers excluded.
    """
    if 'Profit / Loss %' not in strategy_data.columns:
        raise ValueError("Column 'Profit / Loss %' not found in strategy_data.")
    
    filtered_data = strategy_data[strategy_data['Profit / Loss %'].between(-5, 5)].reset_index()
    return filtered_data

def update_and_exclude_outliers(momentum_data: pd.DataFrame, hodl_btc_data: pd.DataFrame = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Update current balance for both strategies and exclude outliers if chosen.

    Parameters:
    - momentum_data (pd.DataFrame): DataFrame containing the Momentum strategy data.
    - hodl_btc_data (pd.DataFrame, optional): DataFrame containing HODL BTC strategy data.

    Returns:
    Tuple[pd.DataFrame, pd.DataFrame]: Updated DataFrames for the Momentum strategy and HODL BTC.
    """
    momentum_data = update_portfolio_current_balance(momentum_data)
    hodl_btc_data = update_portfolio_current_balance(hodl_btc_data)

    if st.toggle('Exclude outliers', help='Whether to exclude outliers beyond the range [-500%, 500%]'):
        momentum_data = exclude_outliers(momentum_data)
        hodl_btc_data = exclude_outliers(hodl_btc_data)

    return momentum_data, hodl_btc_data

def display_main_key_metrics(momentum_stats: pd.Series, hodl_btc_stats: pd.Series) -> None:
    """
    Display main key metrics for trading strategies.

    Parameters:
    - momentum_stats (pd.Series): Key metrics for the momentum strategy.
    - hodl_btc_stats (pd.Series): Key metrics for the HODL BTC strategy.

    Returns:
    None
    """
    show_main_key_stats(momentum_stats)

    with st.expander('See All Key Metrics'):
        strategies_metrics = pd.concat([momentum_stats, hodl_btc_stats], axis=1, keys=['Momentum', 'Hodl BTC'])
        st.dataframe(strategies_metrics, use_container_width=True)

def display_strategy_comparison_chart(momentum_data: pd.DataFrame) -> None:
    """
    Display a comparison chart between the momentum strategy and HODL BTC.

    Parameters:
    - momentum_data (pd.DataFrame): DataFrame containing data for the momentum strategy.

    Returns:
    None
    """
    st.subheader('*Momentum Strategy vs HODL BTC*')
    st.line_chart(data=momentum_data, x='Purchase date', y=['Portfolio', 'Hodl BTC'])

def display_return_with_compound_interest(momentum_data: pd.DataFrame) -> None:
    """
    Display Return with Compound Interest metrics.

    Parameters:
    - momentum_data (pd.DataFrame): DataFrame containing data for the momentum strategy.

    Returns:
    None
    """
    st.subheader('*Return with Compound Interest*')
    compound_interests = calculate_compound_interest_dynamics(momentum_data['Portfolio'], momentum_data['Purchase date'])

    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current CI", f'{round(compound_interests.iloc[-1]*100, 2)}%')
        with col2:    
            st.metric("Mean CI", f'{round(compound_interests.mean()*100, 2)}%')
        with col3:
            st.metric("CI StDev", f'{round(compound_interests.std()*100, 2)}%')
        st.bar_chart(compound_interests)

def display_raw_data(momentum_data: pd.DataFrame) -> None:
    """
    Display raw data for the momentum strategy.

    Parameters:
    - momentum_data (pd.DataFrame): DataFrame containing data for the momentum strategy.

    Returns:
    None
    """
    st.subheader('*Raw Data*')
    with st.expander('See Strategy Raw Data'):
        st.dataframe(momentum_data, use_container_width=True)

def show_main_tab(momentum_data: pd.DataFrame, 
                  hodl_btc_data: pd.DataFrame = None, 
                  coin_api_data: pd.DataFrame = None) -> None:
    """
    Display the main tab with key metrics, comparisons, and raw data for a trading strategy.

    Parameters:
    - data (pd.DataFrame): DataFrame containing the main trading strategy data.
    - hodl_btc_data (pd.DataFrame, optional): DataFrame containing HODL BTC strategy data.

    Returns:
    None
    """
    # Check if data is not empty and contains necessary columns
    if momentum_data.empty or 'Purchase date' not in momentum_data.columns or 'Portfolio' not in momentum_data.columns:
        st.warning("Invalid or empty data provided.")
        return

    # Check if hodl_btc_data is not empty and contains necessary columns
    if hodl_btc_data is not None and (hodl_btc_data.empty or 'Purchase date' not in hodl_btc_data.columns or 'Portfolio' not in hodl_btc_data.columns):
        st.warning("Invalid or empty hodl_btc_data provided.")
        return

    min_date = min(momentum_data['Purchase date'].dt.year)
    max_date = max(momentum_data['Purchase date'].dt.year)
    st.slider('Choose date range to display', 
                min_value=min_date, 
                max_value=max_date,
                value=(min_date, max_date),
                key='tab_main_date_range_slider')

    # Update and exclude outliers for both strategies
    momentum_data, hodl_btc_data = update_and_exclude_outliers(momentum_data, hodl_btc_data)

    # Update dataframe by slider date range
    momentum_data = momentum_data[momentum_data['Purchase date'].dt.year.between(
        st.session_state.tab_main_date_range_slider[0],
        st.session_state.tab_main_date_range_slider[1]
    )].reset_index(drop=True)

    hodl_btc_data = hodl_btc_data[hodl_btc_data['Purchase date'].dt.year.between(
        st.session_state.tab_main_date_range_slider[0],
        st.session_state.tab_main_date_range_slider[1]
    )].reset_index(drop=True)

    # Calculate key metrics for both strategies
    momentum_stats = calculate_strategy_stats(momentum_data)
    hodl_btc_stats = calculate_strategy_stats(hodl_btc_data)

    # Display main key metrics
    display_main_key_metrics(momentum_stats, hodl_btc_stats)

    # Display comparison chart
    display_strategy_comparison_chart(momentum_data)

    # # Display current coin price chart
    # current_coin = momentum_data['Coin'].iloc[-1]
    # st.subheader(f'*{current_coin} Price Chart*')
    # st.line_chart(data=coin_api_data, x='datetime', y=[current_coin])

    # Display Return with Compound Interest metrics
    display_return_with_compound_interest(momentum_data)

    # Display raw data
    display_raw_data(momentum_data)
