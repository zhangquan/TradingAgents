import pandas as pd
from stockstats import wrap
from typing import Annotated
import os
from .config import get_config
from .polygon_utils import PolygonUtils
from datetime import datetime, timedelta


class StockstatsPolygonUtils:

    @staticmethod
    def get_stock_stats_window(
        symbol: Annotated[str, "ticker symbol for the company"],
        indicator: Annotated[
            str, "quantitative indicators based off of the stock data for the company"
        ],
        curr_date: Annotated[
            str, "curr date for retrieving stock price data, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "number of days to look back for data"]
    ):
        """
        Get stock statistics for a window of days instead of just a single date.
        Returns a DataFrame with dates and indicator values.
        """
        df = None
        data = None

        # Use the enhanced cached data interface from PolygonUtils for window data
        polygon_utils = PolygonUtils()
        
        # Use the window cached method which handles all the caching logic
        data = polygon_utils.get_stock_data_window_cached(
            symbol=symbol,
            curr_date=curr_date,
            look_back_days=look_back_days + 90,  # Extra buffer for technical indicators
            extend_cache=True,  # Extend cache with additional historical data
            max_cache_age_days=365  # Cache is valid for 7 days
        )
        
        if data.empty:
            raise Exception(f"No data found for symbol '{symbol}'")
        
        # Reset index to make Date a column for stockstats processing
        data = data.reset_index()
        df = wrap(data)
        df["Date"] = pd.to_datetime(df["Date"])

        # Calculate the indicator (this triggers stockstats to compute it)
        df[indicator]
        
        # Filter data for the specified window
        curr_date_dt = pd.to_datetime(curr_date)
        start_date_dt = curr_date_dt - timedelta(days=look_back_days)
        
        window_data = df[
            (df["Date"] >= start_date_dt) & (df["Date"] <= curr_date_dt)
        ].copy()
        
        if not window_data.empty:
            # Return DataFrame with Date and indicator columns
            result_df = window_data[["Date", indicator]].copy()
            result_df["Date"] = result_df["Date"].dt.strftime("%Y-%m-%d")
            return result_df
        else:
            return pd.DataFrame(columns=["Date", indicator])

