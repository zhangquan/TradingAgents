from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from typing import List
from typing import Annotated
from langchain_core.messages import RemoveMessage
from langchain_core.tools import tool
import pandas as pd
import os
from langchain_openai import ChatOpenAI

from tradingagents.dataflows.polygon_interface import  get_polygon_data_window, get_polygon_company_info,get_polygon_stock_stats_indicators_window
from tradingagents.default_config import DEFAULT_CONFIG
from langchain_core.messages import HumanMessage


class PolygonToolkit:
    _config = DEFAULT_CONFIG.copy()

    @classmethod
    def update_config(cls, config):
        """Update the class-level configuration."""
        cls._config.update(config)

    @property
    def config(self):
        """Access the configuration."""
        return self._config

    def __init__(self, config=None):
        if config:
            self.update_config(config)


    @staticmethod
    @tool
    def get_polygon_data_window(
        symbol: Annotated[str, "ticker symbol of the company"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        look_back_days: Annotated[int, "how many days to look back"],
    ) -> str:
        """
        Retrieve stock price data for a window of days from current date using Polygon.io.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): Number of days to look back
        Returns:
            str: A formatted dataframe containing the stock price data for the specified window.
        """

        result_data = get_polygon_data_window(symbol, curr_date, look_back_days)

        return result_data

    @staticmethod
    @tool
    def get_polygon_company_info(
        symbol: Annotated[str, "ticker symbol of the company"],
    ) -> str:
        """
        Retrieve company information for a given ticker symbol from Polygon.io.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        Returns:
            str: A formatted string containing company information.
        """

        result_data = get_polygon_company_info(symbol)

        return result_data

    @staticmethod
    @tool
    def get_stockstats_indicators_report_window(
        symbol: Annotated[str, "ticker symbol of the company"],
        indicator: Annotated[
            str, "technical indicator to get the analysis and report of"
        ],
        curr_date: Annotated[
            str, "The current trading date you are trading on, YYYY-mm-dd"
        ],
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve stock stats indicators for a given ticker symbol and indicator.
        Args:
            symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
            indicator (str): Technical indicator to get the analysis and report of
            curr_date (str): The current trading date you are trading on, YYYY-mm-dd
            look_back_days (int): How many days to look back, default is 30
        Returns:
            str: A formatted dataframe containing the stock stats indicators for the specified ticker symbol and indicator.
        """

        result_stockstats = get_polygon_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days
        )

        return result_stockstats

 