import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


@st.cache_resource
class DatabaseConnector:
    """
    A class for connecting to and querying a Google Sheets database.

    Attributes:
    - conn (GSheetsConnection): Connection to the Google Sheets database.
    """
    def __init__(self):
        """
        Initialize the DatabaseConnector class.
        """        
        self.conn = st.connection('gsheets', type=GSheetsConnection)

    def execute_query(self, sql: str):
        """
        Execute a SQL query on the Google Sheets database and return the result.

        Parameters:
        - sql (str): The SQL query to be executed.

        Returns:
        pd.DataFrame: A Pandas DataFrame representing the result set of the query.
        """   
        return pd.DataFrame(self.conn.query(sql=sql))

    def get_momentum_strategy_data(self):
        """
        Retrieve strategy data from the Google Sheets database.

        Returns:
        pd.DataFrame: A Pandas DataFrame containing strategy data.
        """        
        sql = '''
            SELECT *
            FROM
                streamlit            
        '''        
        placeholder = st.empty()
        status = placeholder.status("Downloading Momentum strategy data...  :new_moon:")
        with status:        
            df = self.execute_query(sql)
            df.dropna(inplace=True)
            df['Purchase date'] = pd.to_datetime(df['Purchase date'], format='%d.%m.%Y')
            df['Sale date'] = pd.to_datetime(df['Sale date'], format='%d.%m.%Y')
            df['Portfolio'] = df['Portfolio'].apply(lambda x: round(x, 2))
            df['Hodl BTC'] = df['Hodl BTC'].apply(lambda x: round(x, 2))
            status.update(label="Download complete!", state="complete")
        placeholder.empty()
        return df

    def get_hodl_btc_strategy_data(self):
        """
        Retrieve strategy data from the Google Sheets database.

        Returns:
        pd.DataFrame: A Pandas DataFrame containing strategy data.
        """        
        sql = '''
            SELECT *
            FROM
                hodl_btc            
        '''        
        placeholder = st.empty()
        status = placeholder.status("Downloading HODL BTC strategy data...  :new_moon:")
        with status:        
            df = self.execute_query(sql)
            df.dropna(inplace=True)
            df['Purchase date'] = pd.to_datetime(df['Purchase date'], format='%d.%m.%Y')
            df['Sale date'] = pd.to_datetime(df['Sale date'], format='%d.%m.%Y')
            df['Portfolio'] = df['Portfolio'].apply(lambda x: round(x, 2))
            status.update(label="Download complete!", state="complete")
        placeholder.empty()
        return df
