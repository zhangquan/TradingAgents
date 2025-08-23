import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Annotated, Optional
from polygon import RESTClient
import logging
from .config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolygonUtils:
    """Utility class for Polygon.io API operations"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Polygon.io client
        
        Args:
            api_key (str): Polygon.io API key. If not provided, will try to get from environment variable POLYGON_API_KEY
        """
        self.api_key = api_key or os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            raise ValueError("Polygon.io API key is required. Set POLYGON_API_KEY environment variable or pass api_key parameter.")
        
        self.client = RESTClient(self.api_key)
    
    def get_stock_data_online(
        self,
        symbol: Annotated[str, "ticker symbol"],
        start_date: Annotated[str, "start date for retrieving stock price data, YYYY-mm-dd"],
        end_date: Annotated[str, "end date for retrieving stock price data, YYYY-mm-dd"],
    ) -> pd.DataFrame:
        """
        Retrieve stock price data for designated ticker symbol using Polygon.io
        
        Args:
            symbol (str): Stock ticker symbol (e.g., 'AAPL', 'TSLA')
            start_date (str): Start date in YYYY-mm-dd format
            end_date (str): End date in YYYY-mm-dd format
            
        Returns:
            pd.DataFrame: Stock price data with columns: Open, High, Low, Close, Volume, VWAP, Transactions
        """
        try:
            # Convert dates to datetime objects
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Get daily aggregates
            aggs = []
            for agg in self.client.list_aggs(
                ticker=symbol.upper(),
                multiplier=1,
                timespan="day",
                from_=start_date,
                to=end_date,
                limit=50000,
            ):
                aggs.append({
                    'Date': datetime.fromtimestamp(agg.timestamp / 1000).strftime('%Y-%m-%d'),
                    'Open': agg.open,
                    'High': agg.high,
                    'Low': agg.low,
                    'Close': agg.close,
                    'Volume': agg.volume,
                    'VWAP': agg.vwap,
                    'Transactions': agg.transactions
                })
            
            if not aggs:
                logger.warning(f"No data found for symbol '{symbol}' between {start_date} and {end_date}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(aggs)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            
            # Round numerical values to 2 decimal places
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'VWAP']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].round(2)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
            raise
    
    def get_stock_data_window_online(
        self,
        symbol: Annotated[str, "ticker symbol of the company"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        look_back_days: Annotated[int, "how many days to look back"],
    ) -> pd.DataFrame:
        """
        Retrieve stock price data for a window of days from current date
        
        Args:
            symbol (str): Stock ticker symbol
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): Number of days to look back
            
        Returns:
            pd.DataFrame: Stock price data for the specified window
        """
        # Calculate start date
        curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_dt = curr_dt - timedelta(days=look_back_days)
        
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = curr_date
        
        return self.get_stock_data(symbol, start_date, end_date)
    def get_stock_data_cached(
        self,
        symbol: Annotated[str, "ticker symbol"],
        start_date: Annotated[str, "start date for retrieving stock price data, YYYY-mm-dd"],
        end_date: Annotated[str, "end date for retrieving stock price data, YYYY-mm-dd"],
        extend_cache: Annotated[bool, "whether to extend cache with additional historical data"] = True,
        max_cache_age_days: Annotated[int, "maximum age of cached data in days"] = 7,
    ) -> pd.DataFrame:
        """
        Retrieve stock price data with intelligent caching and incremental fetching
        
        Args:
            symbol (str): Stock ticker symbol (e.g., 'AAPL', 'TSLA')
            start_date (str): Start date in YYYY-mm-dd format
            end_date (str): End date in YYYY-mm-dd format
            extend_cache (bool): Whether to extend cache with additional historical data
            max_cache_age_days (int): Maximum age of cached data in days
            
        Returns:
            pd.DataFrame: Stock price data with columns: Open, High, Low, Close, Volume, VWAP, Transactions
        """
        try:
            cache_file_path = self._get_cache_file_path(symbol)
            cached_data = self._load_cached_data(cache_file_path)
            
            # Calculate required date range
            requested_start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            requested_end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Determine what data we need to fetch (avoid loading existing data)
            fetch_ranges = []
            final_data = cached_data.copy() if cached_data is not None and not cached_data.empty else pd.DataFrame()
            
            if cached_data is None or cached_data.empty:
                # No cache exists, need to fetch everything
                if extend_cache:
                    # Extend the date range to cache more data for future requests
                    extended_start = requested_start_dt - timedelta(days=365)  # Get 1 year of historical data
                    extended_end = datetime.now()  # Get up to current date
                    fetch_ranges.append((extended_start, extended_end))
                else:
                    fetch_ranges.append((requested_start_dt, requested_end_dt))
                logger.info(f"No cache found for {symbol}, will fetch new data")
            else:
                cached_start = cached_data.index.min()
                cached_end = cached_data.index.max()
                
                # Check if cache covers requested range and is not too old
                cache_valid = self._is_cache_valid(cached_data, start_date, end_date, max_cache_age_days)
                
                if cache_valid:
                    logger.info(f"Using cached data for {symbol}")
                else:
                    # Determine missing ranges
                    logger.info(f"Cache partially covers the range or is stale for {symbol}, fetching missing data")
                    
                    # Calculate what ranges we need to fetch
                    target_start = requested_start_dt
                    target_end = requested_end_dt
                    
                    if extend_cache:
                        # Extend range for better future coverage
                        target_start = min(requested_start_dt, requested_start_dt - timedelta(days=365))
                        target_end = max(requested_end_dt, datetime.now())
                    
                    # Add ranges that are missing from cache
                    if target_start < cached_start:
                        # Need data before cached range
                        fetch_ranges.append((target_start, cached_start - timedelta(days=1)))
                    
                    if target_end > cached_end:
                        # Need data after cached range
                        fetch_ranges.append((cached_end + timedelta(days=1), target_end))
                    
                    # Check if cached data is too old (need to refresh recent data)
                    if (datetime.now() - cached_end).days > max_cache_age_days:
                        # Refresh the last few days
                        refresh_start = max(cached_end - timedelta(days=max_cache_age_days), cached_start)
                        refresh_end = datetime.now()
                        fetch_ranges.append((refresh_start, refresh_end))
            
            # Fetch missing data ranges
            for fetch_start, fetch_end in fetch_ranges:
                fetch_start_str = fetch_start.strftime("%Y-%m-%d")
                fetch_end_str = fetch_end.strftime("%Y-%m-%d")
                
                logger.info(f"Fetching data for {symbol} from {fetch_start_str} to {fetch_end_str}")
                api_data = self.get_stock_data_online(symbol, fetch_start_str, fetch_end_str)
                
                if not api_data.empty:
                    if final_data.empty:
                        final_data = api_data
                    else:
                        # Merge new data with existing cache, removing duplicates
                        combined_data = pd.concat([final_data, api_data])
                        # Remove duplicates by keeping the latest version
                        final_data = combined_data[~combined_data.index.duplicated(keep='last')].sort_index()
                else:
                    logger.warning(f"No data returned for {symbol} from {fetch_start_str} to {fetch_end_str}")
            
            # Save updated cache if we fetched any new data
            if fetch_ranges and not final_data.empty:
                self._save_cached_data(final_data, cache_file_path)
                logger.info(f"Updated cache for {symbol} with new data")
            
            # Filter data for the requested date range
            if final_data.empty:
                logger.warning(f"No data available for symbol '{symbol}' between {start_date} and {end_date}")
                return pd.DataFrame()
            
            filtered_data = final_data[
                (final_data.index >= requested_start_dt) & (final_data.index <= requested_end_dt)
            ]
            
            if filtered_data.empty:
                logger.warning(f"No data found for symbol '{symbol}' between {start_date} and {end_date}")
                return pd.DataFrame()
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error fetching cached stock data for {symbol}: {str(e)}")
            raise
    def get_stock_data_window_cached(
        self,
        symbol: Annotated[str, "ticker symbol of the company"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        look_back_days: Annotated[int, "how many days to look back"],
        extend_cache: Annotated[bool, "whether to extend cache with additional historical data"] = True,
        max_cache_age_days: Annotated[int, "maximum age of cached data in days"] = 7,
    ) -> pd.DataFrame:
        """
        Retrieve stock price data for a window of days from current date with caching
        
        Args:
            symbol (str): Stock ticker symbol
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): Number of days to look back
            extend_cache (bool): Whether to extend cache with additional historical data
            max_cache_age_days (int): Maximum age of cached data in days
            
        Returns:
            pd.DataFrame: Stock price data for the specified window
        """
        # Calculate start date
        curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_dt = curr_dt - timedelta(days=look_back_days)
        
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = curr_date
        
        return self.get_stock_data_cached(
            symbol, start_date, end_date, extend_cache, max_cache_age_days
        )
    
    def get_stock_info(
        self,
        symbol: Annotated[str, "ticker symbol"],
    ) -> dict:
        """
        Fetch and return latest stock information
        
        Args:
            symbol (str): Stock ticker symbol
            
        Returns:
            dict: Stock information including company details
        """
        try:
            # Get ticker details
            ticker_details = self.client.get_ticker_details(symbol.upper())
            
            info = {
                "Company Name": getattr(ticker_details, 'name', 'N/A'),
                "Industry": getattr(ticker_details, 'market_cap', 'N/A'),
                "Sector": getattr(ticker_details, 'sector', 'N/A'),
                "Country": getattr(ticker_details, 'locale', 'N/A'),
                "Website": getattr(ticker_details, 'homepage_url', 'N/A'),
                "Market Cap": getattr(ticker_details, 'market_cap', 'N/A'),
                "Employees": getattr(ticker_details, 'total_employees', 'N/A'),
                "Description": getattr(ticker_details, 'description', 'N/A'),
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
            return {
                "Company Name": "N/A",
                "Industry": "N/A", 
                "Sector": "N/A",
                "Country": "N/A",
                "Website": "N/A",
                "Market Cap": "N/A",
                "Employees": "N/A",
                "Description": "N/A",
            }
    
    def get_company_info(
        self,
        symbol: Annotated[str, "ticker symbol"],
        save_path: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch and return company information as a DataFrame
        
        Args:
            symbol (str): Stock ticker symbol
            save_path (str, optional): Path to save the data
            
        Returns:
            pd.DataFrame: Company information
        """
        info = self.get_stock_info(symbol)
        company_info_df = pd.DataFrame([info])
        
        if save_path:
            company_info_df.to_csv(save_path)
            logger.info(f"Company info for {symbol} saved to {save_path}")
        
        return company_info_df
    
  
    def _get_cache_file_path(self, symbol: str) -> str:
        """
        Get the cache file path for a given symbol
        
        Args:
            symbol (str): Stock ticker symbol
            
        Returns:
            str: Cache file path
        """
        try:
            config = get_config()
            cache_dir = config["data_cache_dir"]
            os.makedirs(cache_dir, exist_ok=True)
            return os.path.join(cache_dir, f"{symbol.upper()}-Polygon-data.csv")
        except Exception as e:
            logger.error(f"Error getting cache file path: {str(e)}")
            # Fallback to default directory
            cache_dir = "tradingagents/dataflows/data_cache"
            os.makedirs(cache_dir, exist_ok=True)
            return os.path.join(cache_dir, f"{symbol.upper()}-Polygon-data.csv")
    
    def _load_cached_data(self, cache_file_path: str) -> Optional[pd.DataFrame]:
        """
        Load cached data from file
        
        Args:
            cache_file_path (str): Path to cache file
            
        Returns:
            pd.DataFrame or None: Cached data if available and valid
        """
        if not os.path.exists(cache_file_path):
            return None
            
        try:
            cached_data = pd.read_csv(cache_file_path)
            cached_data["Date"] = pd.to_datetime(cached_data["Date"])
            cached_data = cached_data.set_index("Date")
            return cached_data
        except Exception as e:
            logger.warning(f"Could not load cached data from {cache_file_path}: {e}")
            return None
    
    def _save_cached_data(self, data: pd.DataFrame, cache_file_path: str) -> None:
        """
        Save data to cache file
        
        Args:
            data (pd.DataFrame): Data to save
            cache_file_path (str): Path to cache file
        """
        try:
            # Reset index to make Date a column for CSV storage
            data_to_save = data.reset_index()
            data_to_save.to_csv(cache_file_path, index=False)
            logger.info(f"Data saved to cache: {cache_file_path}")
        except Exception as e:
            logger.error(f"Error saving data to cache {cache_file_path}: {str(e)}")
    
    def _is_cache_valid(self, cached_data: pd.DataFrame, start_date: str, end_date: str, max_age_days: int = 7) -> bool:
        """
        Check if cached data is valid for the requested date range
        
        Args:
            cached_data (pd.DataFrame): Cached data
            start_date (str): Start date in YYYY-mm-dd format
            end_date (str): End date in YYYY-mm-dd format
            max_age_days (int): Maximum age of cached data in days
            
        Returns:
            bool: True if cache is valid
        """
        if cached_data is None or cached_data.empty:
            return False
            
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Check if cached data covers the requested date range
        cached_start = cached_data.index.min()
        cached_end = cached_data.index.max()
        
        if cached_start > start_dt or cached_end < end_dt:
            return False
            
        # Check if data is recent enough (within max_age_days for end date)
        if (datetime.now() - cached_end).days > max_age_days:
            return False
            
        return True
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear cache files
        
        Args:
            symbol (str, optional): Specific symbol to clear cache for. If None, clears all cache files.
        """
        try:
            if symbol:
                cache_file_path = self._get_cache_file_path(symbol)
                if os.path.exists(cache_file_path):
                    os.remove(cache_file_path)
                    logger.info(f"Cache cleared for {symbol}")
            else:
                config = get_config()
                cache_dir = config["data_cache_dir"]
                if os.path.exists(cache_dir):
                    for file in os.listdir(cache_dir):
                        if file.endswith("-Polygon-data.csv"):
                            os.remove(os.path.join(cache_dir, file))
                    logger.info("All Polygon cache files cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
    
    def get_cache_info(self, symbol: str) -> dict:
        """
        Get information about cached data for a symbol
        
        Args:
            symbol (str): Stock ticker symbol
            
        Returns:
            dict: Cache information including date range and file size
        """
        try:
            cache_file_path = self._get_cache_file_path(symbol)
            
            if not os.path.exists(cache_file_path):
                return {"exists": False, "path": cache_file_path}
            
            cached_data = self._load_cached_data(cache_file_path)
            if cached_data is None or cached_data.empty:
                return {"exists": False, "path": cache_file_path}
            
            file_stats = os.stat(cache_file_path)
            
            return {
                "exists": True,
                "path": cache_file_path,
                "start_date": cached_data.index.min().strftime("%Y-%m-%d"),
                "end_date": cached_data.index.max().strftime("%Y-%m-%d"),
                "record_count": len(cached_data),
                "file_size_bytes": file_stats.st_size,
                "last_modified": datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
            
        except Exception as e:
            logger.error(f"Error getting cache info for {symbol}: {str(e)}")
            return {"exists": False, "error": str(e)}