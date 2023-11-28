import pandas as pd
import streamlit as st

@st.cache_data
def calculate_strategy_stats(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate strategy statistics based on the 'Profit / Loss %' column in the provided DataFrame.

    Parameters:
    - data (pd.DataFrame): DataFrame containing trading data, including a 'Profit / Loss %' column.

    Returns:
    pd.DataFrame: A DataFrame with calculated trading statistics, including the percentage of profits, losses, and HODL.
    The DataFrame has three rows: 'Profit', 'Loss', and 'HODL', with corresponding percentages.
    """    
    return (data['Profit / Loss %'].apply(lambda x: 'profit' if x > 0 else 'loss' if x < 0 else 'hodl')
                                      .value_counts(normalize=True)
                                      .rename(index={'profit': 'PROFIT', 'loss': 'LOSS', 'hodl': 'HODL'})
                                      .to_frame())

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
