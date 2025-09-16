"""
Data Provider Interface and Factory
Provides a unified interface for different stock data providers (Polygon, Yahoo Finance, etc.)
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Annotated, Optional, Protocol, Dict, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class DataProviderInterface(Protocol):
    """Protocol defining the interface for stock data providers"""
    
    def get_stock_data_window(
        self,
        symbol: Annotated[str, "Stock ticker symbol"],
        curr_date: Annotated[str, "Current date YYYY-MM-DD"],
        look_back_days: Annotated[int, "Number of days to look back"],
        extend_cache: bool = False
    ) -> pd.DataFrame:
        """Get stock data for a specific window period"""
        ...
    
    def get_stock_data_window_cached(
        self,
        symbol: Annotated[str, "Stock ticker symbol"],
        curr_date: Annotated[str, "Current date YYYY-MM-DD"],
        look_back_days: Annotated[int, "Number of days to look back"],
        extend_cache: bool = False
    ) -> pd.DataFrame:
        """Get cached stock data for a specific window period"""
        ...
    
    def is_available(self) -> bool:
        """Check if the data provider is available/configured"""
        ...


class PolygonDataProvider:
    """Polygon.io data provider implementation"""
    
    def __init__(self, require_api_key: bool = False):
        from .polygon_utils import PolygonUtils
        try:
            self.provider = PolygonUtils(require_api_key=require_api_key)
            self._available = True
        except Exception as e:
            logger.warning(f"Failed to initialize Polygon provider: {e}")
            self.provider = None
            self._available = False
    
    def get_stock_data_window(
        self,
        symbol: str,
        curr_date: str,
        look_back_days: int,
        extend_cache: bool = False
    ) -> pd.DataFrame:
        if not self.provider:
            return pd.DataFrame()
        return self.provider.get_stock_data_window_cached(
            symbol, curr_date, look_back_days, extend_cache
        )
    
    def get_stock_data_window_cached(
        self,
        symbol: str,
        curr_date: str,
        look_back_days: int,
        extend_cache: bool = False
    ) -> pd.DataFrame:
        if not self.provider:
            return pd.DataFrame()
        return self.provider.get_stock_data_window_cached(
            symbol, curr_date, look_back_days, extend_cache
        )
    
    def is_available(self) -> bool:
        return self._available and self.provider is not None


class YahooFinanceDataProvider:
    """Yahoo Finance data provider implementation"""
    
    def __init__(self):
        try:
            import yfinance as yf
            self.yf = yf
            self._available = True
        except ImportError as e:
            logger.warning(f"Yahoo Finance not available: {e}")
            self.yf = None
            self._available = False
    
    def get_stock_data_window(
        self,
        symbol: str,
        curr_date: str,
        look_back_days: int,
        extend_cache: bool = False
    ) -> pd.DataFrame:
        """Get Yahoo Finance data for the specified window"""
        if not self._available:
            return pd.DataFrame()
        
        try:
            # Calculate date range
            end_date = datetime.strptime(curr_date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=look_back_days)
            
            # Get ticker data
            ticker = self.yf.Ticker(symbol.upper())
            data = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d")  # Add 1 day to include end date
            )
            
            if data.empty:
                logger.warning(f"No Yahoo Finance data found for {symbol}")
                return pd.DataFrame()
            
            # Standardize column names to match Polygon format
            if not data.empty:
                data = data.rename(columns={
                    'Open': 'Open',
                    'High': 'High', 
                    'Low': 'Low',
                    'Close': 'Close',
                    'Volume': 'Volume'
                })
                
                # Ensure we have the required columns
                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                for col in required_cols:
                    if col not in data.columns:
                        logger.warning(f"Missing column {col} in Yahoo Finance data for {symbol}")
                        return pd.DataFrame()
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_stock_data_window_cached(
        self,
        symbol: str,
        curr_date: str,
        look_back_days: int,
        extend_cache: bool = False
    ) -> pd.DataFrame:
        """Yahoo Finance doesn't have built-in caching, so this calls the regular method"""
        return self.get_stock_data_window(symbol, curr_date, look_back_days, extend_cache)
    
    def is_available(self) -> bool:
        return self._available


class FinnhubDataProvider:
    """Finnhub data provider implementation (placeholder for future implementation)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self._available = bool(self.api_key)
    
    def get_stock_data_window(
        self,
        symbol: str,
        curr_date: str,
        look_back_days: int,
        extend_cache: bool = False
    ) -> pd.DataFrame:
        # TODO: Implement Finnhub data fetching
        logger.warning("Finnhub provider not yet implemented")
        return pd.DataFrame()
    
    def get_stock_data_window_cached(
        self,
        symbol: str,
        curr_date: str,
        look_back_days: int,
        extend_cache: bool = False
    ) -> pd.DataFrame:
        return self.get_stock_data_window(symbol, curr_date, look_back_days, extend_cache)
    
    def is_available(self) -> bool:
        return self._available


class DataProviderFactory:
    """Factory class to create data provider instances based on configuration"""
    
    _providers = {
        "polygon": PolygonDataProvider,
        "yahoo": YahooFinanceDataProvider,
        "finnhub": FinnhubDataProvider,
    }
    
    @classmethod
    def create_provider(
        cls, 
        provider_name: str, 
        require_api_key: bool = False,
        **kwargs
    ) -> DataProviderInterface:
        """
        Create a data provider instance
        
        Args:
            provider_name: Name of the provider (polygon, yahoo, finnhub)
            require_api_key: Whether to require API key for the provider
            **kwargs: Additional arguments passed to the provider constructor
            
        Returns:
            DataProviderInterface: Instance of the requested provider
            
        Raises:
            ValueError: If the provider name is not supported
        """
        if provider_name not in cls._providers:
            raise ValueError(
                f"Unsupported data provider: {provider_name}. "
                f"Available providers: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_name]
        
        # Handle different constructor signatures
        if provider_name == "polygon":
            return provider_class(require_api_key=require_api_key, **kwargs)
        elif provider_name == "yahoo":
            return provider_class(**kwargs)
        elif provider_name == "finnhub":
            return provider_class(**kwargs)
        else:
            return provider_class(**kwargs)
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, bool]:
        """Get a dict of provider names and their availability status"""
        availability = {}
        for name in cls._providers:
            try:
                provider = cls.create_provider(name, require_api_key=False)
                availability[name] = provider.is_available()
            except Exception as e:
                logger.debug(f"Provider {name} not available: {e}")
                availability[name] = False
        return availability
    
    @classmethod
    def get_default_provider_for_environment(cls, environment: str = None) -> str:
        """Get the default provider for the given environment"""
        from ..default_config import get_data_provider_for_environment
        return get_data_provider_for_environment(environment)