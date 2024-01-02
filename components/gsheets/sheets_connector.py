import streamlit as st
import pandas as pd

from streamlit_gsheets import GSheetsConnection
from abc import ABC, abstractmethod
from typing import Optional, Union, Iterable
from datetime import timezone, timedelta


class DatabaseConnector(ABC):
    """
    Abstract class for connecting to and querying a Google Sheets database.

    Attributes:
    - conn (GSheetsConnection): Connection to the Google Sheets database.
    """
    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize the DatabaseConnector class.

        Parameters:
        - table_name (Optional[str]): Name of the table to connect to. Can be None.
        """
        self.table_name = table_name
        self.conn = self._create_connection()

    @abstractmethod
    def _create_connection(self) -> st.connection:
        """
        Abstract method to create a connection to the database.
        This method must be implemented in child classes.

        Returns:
        st.connection: Connection to the Google Sheets database.
        """
        pass

    @abstractmethod
    def execute_query(self, sql: str) -> pd.DataFrame:
        """
        Execute an SQL query on the Google Sheets database and return the result.

        Parameters:
        - sql (str): The SQL query to be executed.

        Returns:
        pd.DataFrame: Result of the query in the pandas dataframe.
        """
        pass

    @abstractmethod
    def get_data_from_sheet(self, sheet_name: str) -> pd.DataFrame:
        """
        Retrieve data from a specific sheet in the Google Sheets database.

        Parameters:
        - sheet_name (str): Name of the sheet.

        Returns:
        pd.DataFrame: Result of the query in the pandas dataframe.
        """
        pass

    @abstractmethod
    def rename_columns(self, df: pd.DataFrame, old_column_name: str, new_column_name: str) -> pd.DataFrame:
        """
        Abstract method to rename columns in a Pandas DataFrame.

        Parameters:
        - df (pd.DataFrame): Input DataFrame.
        - old_column_name (str): Old column name to be renamed.
        - new_column_name (str): New column name.

        Returns:
        pd.DataFrame: DataFrame with renamed columns.
        """
        pass

    @abstractmethod
    def convert_timezone(self, df: pd.DataFrame, timestamp_col: Union[str, Iterable[str]], tz_offset: int, time_format: str = '%Y-%m-%dT%H:%M:%S.%fZ') -> pd.DataFrame:
        """
        Abstract method to convert the timezone of a timestamp column(s) in a Pandas DataFrame.

        Parameters:
        - df (pd.DataFrame): Input DataFrame.
        - timestamp_col (Union[str, List[str]]): Name of the timestamp column or a list of column names.
        - tz_offset (int): Timezone offset in hours.
        - time_format (str): Format of the timestamp column.

        Returns:
        pd.DataFrame: DataFrame with converted timezone.
        """
        pass

    @abstractmethod
    def remove_na(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Abstract method to remove NaN values from a Pandas DataFrame.

        Parameters:
        - df (pd.DataFrame): Input DataFrame.

        Returns:
        pd.DataFrame: DataFrame with NaN values removed.
        """
        pass


class MomentumSheetsConnector(DatabaseConnector):
    def __init__(self, table_name: Optional[str] = None):
        super().__init__(table_name)

    def _create_connection(self) -> st.connection:
        """
        Create a connection to the Google Sheets database.

        Returns:
        st.connection: Connection to the Google Sheets database.
        """
        return st.connection(self.table_name, type=GSheetsConnection)

    def execute_query(self, sql: str) -> pd.DataFrame:
        """
        Execute an SQL query for the Google Sheets database.

        Parameters:
        - sql (str): SQL query to execute.

        Returns:
        pd.DataFrame: Result of the query in the pandas dataframe.
        """
        try:
            df = self.conn.query(sql=sql)
            return (
                df
                .pipe(self.convert_timezone, ['Purchase date', 'Sale date'], 0, '%d.%m.%Y')
                .pipe(self.remove_na)
            )
        except Exception as e:
            st.error(f"Error executing query: {e}")
            return {}

    def get_data_from_sheet(self, sheet_name: str) -> pd.DataFrame:
        """
        Retrieve data from a specific sheet in the Google Sheets database.

        Parameters:
        - sheet_name (str): Name of the sheet.

        Returns:
        pd.DataFrame: Result of the query in the pandas dataframe.
        """
        full_query = f"SELECT * FROM {sheet_name}"
        return self.execute_query(full_query)

    def rename_columns(self, df: pd.DataFrame, old_column_name: str, new_column_name: str) -> pd.DataFrame:
        """
        Rename columns in a Pandas DataFrame.

        Parameters:
        - df (pd.DataFrame): Input DataFrame.
        - old_column_name (str): Old column name to be renamed.
        - new_column_name (str): New column name.

        Returns:
        pd.DataFrame: DataFrame with renamed columns.
        """
        return df.rename(columns={old_column_name: new_column_name})

    def convert_timezone(self, 
                         df: pd.DataFrame, 
                         timestamp_col: Union[str, Iterable[str]], 
                         tz_offset: int, 
                         time_format: str = '%Y-%m-%dT%H:%M:%S.%fZ') -> pd.DataFrame:
        """
        Convert the timezone of a timestamp column(s) in a Pandas DataFrame.

        Parameters:
        - df (pd.DataFrame): Input DataFrame.
        - timestamp_col (Union[str, List[str]]): Name of the timestamp column or a list of column names.
        - tz_offset (int): Timezone offset in hours.
        - time_format (str): Format of the timestamp column.

        Returns:
        pd.DataFrame: DataFrame with converted timezone.
        """
        df = df.copy()

        if isinstance(timestamp_col, str):
            # If timestamp_col is a single string, convert it to a list for consistency
            timestamp_col = [timestamp_col]

        for col in timestamp_col:
            df[col] = pd.to_datetime(df[col], format=time_format)
            df[col] = df[col].dt.tz_localize(timezone.utc)
            df[col] = df[col].dt.tz_convert(timezone(timedelta(hours=tz_offset)))

        return df

    def remove_na(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove NaN values from a Pandas DataFrame.

        Parameters:
        - df (pd.DataFrame): Input DataFrame.

        Returns:
        pd.DataFrame: DataFrame with NaN values removed.
        """
        return df.dropna()
    

class CoinApiSheetsConnector(DatabaseConnector):
    def __init__(self, table_name: Optional[str] = None):
        super().__init__(table_name)

    def _create_connection(self) -> st.connection:
        """
        Create a connection to the Google Sheets database.

        Returns:
        st.connection: Connection to the Google Sheets database.
        """
        return st.connection(self.table_name, type=GSheetsConnection)

    def execute_query(self, sql: str) -> pd.DataFrame:
        """
        Execute an SQL query for the Google Sheets database.

        Parameters:
        - sql (str): SQL query to execute.

        Returns:
        pd.DataFrame: Result of the query in the pandas dataframe.
        """
        try:
            df = self.conn.query(sql=sql)
            return (
                df
                .pipe(self.convert_timezone, 'Date in GMT / Coin Ticker', 0)
                .pipe(self.rename_columns, 'Date in GMT / Coin Ticker', 'datetime')
            )
        except Exception as e:
            st.error(f"Error executing query: {e}")
            return {}

    def get_data_from_sheet(self, sheet_name: str) -> pd.DataFrame:
        """
        Retrieve data from a specific sheet in the Google Sheets database.

        Parameters:
        - sheet_name (str): Name of the sheet.

        Returns:
        pd.DataFrame: Result of the query in the pandas dataframe.
        """
        full_query = f"SELECT * FROM {sheet_name}"
        return self.execute_query(full_query)

    def rename_columns(self, df: pd.DataFrame, old_column_name: str, new_column_name: str) -> pd.DataFrame:
        """
        Rename columns in a Pandas DataFrame.

        Parameters:
        - df (pd.DataFrame): Input DataFrame.
        - old_column_name (str): Old column name to be renamed.
        - new_column_name (str): New column name.

        Returns:
        pd.DataFrame: DataFrame with renamed columns.
        """
        return df.rename(columns={old_column_name: new_column_name})

    def convert_timezone(self, 
                         df: pd.DataFrame, 
                         timestamp_col: Union[str, Iterable[str]], 
                         tz_offset: int, 
                         time_format: str = '%Y-%m-%dT%H:%M:%S.%fZ') -> pd.DataFrame:
        """
        Convert the timezone of a timestamp column(s) in a Pandas DataFrame.

        Parameters:
        - df (pd.DataFrame): Input DataFrame.
        - timestamp_col (Union[str, List[str]]): Name of the timestamp column or a list of column names.
        - tz_offset (int): Timezone offset in hours.
        - time_format (str): Format of the timestamp column.

        Returns:
        pd.DataFrame: DataFrame with converted timezone.
        """
        df = df.copy()

        if isinstance(timestamp_col, str):
            # If timestamp_col is a single string, convert it to a list for consistency
            timestamp_col = [timestamp_col]

        for col in timestamp_col:
            df[col] = pd.to_datetime(df[col], format=time_format)
            df[col] = df[col].dt.tz_localize(timezone.utc)
            df[col] = df[col].dt.tz_convert(timezone(timedelta(hours=tz_offset)))

        return df

    def remove_na(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove NaN values from a Pandas DataFrame.

        Parameters:
        - df (pd.DataFrame): Input DataFrame.

        Returns:
        pd.DataFrame: DataFrame with NaN values removed.
        """
        return df.dropna(axis=1, inplace=True)
    