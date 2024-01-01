import pandas as pd
import streamlit as st

from streamlit_gsheets import GSheetsConnection
from datetime import timezone, timedelta


def process_dataframe(df: pd.DataFrame):
    # Копируем датафрейм, чтобы не изменять оригинальный
    df_processed = df.copy()

    # Приводим данные в колонке 'Date in GMT / Coin Ticker' к формату datetime и конвертируем в локальное время
    df_processed['Date in GMT / Coin Ticker'] = pd.to_datetime(df_processed['Date in GMT / Coin Ticker'], format='%Y-%m-%dT%H:%M:%S.%fZ')
    df_processed['Date in GMT / Coin Ticker'] = df_processed['Date in GMT / Coin Ticker'].dt.tz_localize(timezone.utc)
    df_processed['Date in GMT / Coin Ticker'] = df_processed['Date in GMT / Coin Ticker'].dt.tz_convert(timezone(timedelta(hours=3)))
    df_processed.rename(columns={'Date in GMT / Coin Ticker': 'datetime'}, inplace=True)

    return df_processed

class CoinApiSheetsConnector:
    """
    A class for connecting to and querying a Google Sheets - CoinApi.

    Attributes:
    - conn (GSheetsConnection): Connection to the Google Sheets - CoinApi database.
    """
    def __init__(self):
        """
        Initialize the CoinApiSheetsConnector class.
        """        
        self.conn = st.connection('coinapigsheets', type=GSheetsConnection)

    def execute_query(self, sql: str):
        """
        Execute a SQL query on the Google Sheets database and return the result.

        Parameters:
        - sql (str): The SQL query to be executed.

        Returns:
        pd.DataFrame: A Pandas DataFrame representing the result set of the query.
        """   
        return pd.DataFrame(self.conn.query(sql=sql))

    def load_raw_data(self):
        """

        """        
        sql = '''
            SELECT *
            FROM
                raw_data            
        '''        
        placeholder = st.empty()
        status = placeholder.status("Downloading Raw Data...  :new_moon:")
        with status:        
            df = self.execute_query(sql)
            df.dropna(axis=1, inplace=True)
            df = process_dataframe(df)
        placeholder.empty()
        return df

