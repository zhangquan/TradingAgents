from typing import Annotated
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .polygon_utils import PolygonUtils
from .stockstats_polygon_utils import StockstatsPolygonUtils
from .config import DATA_DIR


def get_polygon_data_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    """
    Retrieve stock price data for a window of days from current date using Polygon.io with file caching.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        curr_date (str): Current date in yyyy-mm-dd format
        look_back_days (int): Number of days to look back
    Returns:
        str: A formatted dataframe containing the stock price data for the specified window.
    """
    try:
        # Use the cached window method from PolygonUtils
       
        curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_dt = curr_dt - timedelta(days=look_back_days)
        
        start_date = start_dt.strftime("%Y-%m-%d")
        end_date = curr_date
        polygon_utils = PolygonUtils()
        data = polygon_utils.get_stock_data_cached(symbol, start_date, end_date)
        
        if data.empty:
            return f"No data found for symbol '{symbol}' for {look_back_days} days back from {curr_date}"
        
        # Reset index to make Date a column and format the output
        formatted_data = data.reset_index()
        
        # Convert DataFrame to CSV string
        csv_string = formatted_data.to_csv(index=False)
        
        # Calculate start date for header
        
        # Add header information
        header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date} ({look_back_days} days)\n"
        header += f"# Total records: {len(formatted_data)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"# Data source: Polygon.io (cached)\n\n"
        
        return header + csv_string
        
    except Exception as e:
        return f"Error retrieving data for {symbol}: {str(e)}"


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
    try:
        polygon_utils = PolygonUtils()
        info = polygon_utils.get_stock_info(symbol)
        
        if not info or all(value == 'N/A' for value in info.values()):
            return f"No company information found for symbol '{symbol}'"
        
        # Format the information
        result = f"# Company Information for {symbol.upper()}\n"
        result += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"# Data source: Polygon.io\n\n"
        
        for key, value in info.items():
            result += f"{key}: {value}\n"
        
        return result
        
    except Exception as e:
        return f"Error retrieving company information for {symbol}: {str(e)}"




def get_polygon_stock_stats_indicators_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    """
    Retrieve technical indicator values over a window of days using Polygon data.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        indicator (str): Technical indicator to calculate
        curr_date (str): Current trading date in YYYY-mm-dd format
        look_back_days (int): Number of days to look back
        online (bool): Whether to use online data fetching or cached data
    Returns:
        str: A formatted report with indicator values over the specified window.
    """
    
    best_ind_params = {
        # Moving Averages
        "close_50_sma": (
            "50 SMA: A medium-term trend indicator. "
            "Usage: Identify trend direction and serve as dynamic support/resistance. "
            "Tips: It lags price; combine with faster indicators for timely signals."
        ),
        "close_200_sma": (
            "200 SMA: A long-term trend benchmark. "
            "Usage: Confirm overall market trend and identify golden/death cross setups. "
            "Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries."
        ),
        "close_10_ema": (
            "10 EMA: A responsive short-term average. "
            "Usage: Capture quick shifts in momentum and potential entry points. "
            "Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals."
        ),
        # MACD Related
        "macd": (
            "MACD: Computes momentum via differences of EMAs. "
            "Usage: Look for crossovers and divergence as signals of trend changes. "
            "Tips: Confirm with other indicators in low-volatility or sideways markets."
        ),
        "macds": (
            "MACD Signal: An EMA smoothing of the MACD line. "
            "Usage: Use crossovers with the MACD line to trigger trades. "
            "Tips: Should be part of a broader strategy to avoid false positives."
        ),
        "macdh": (
            "MACD Histogram: Shows the gap between the MACD line and its signal. "
            "Usage: Visualize momentum strength and spot divergence early. "
            "Tips: Can be volatile; complement with additional filters in fast-moving markets."
        ),
        # Momentum Indicators
        "rsi": (
            "RSI: Measures momentum to flag overbought/oversold conditions. "
            "Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. "
            "Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis."
        ),
        # Volatility Indicators
        "boll": (
            "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. "
            "Usage: Acts as a dynamic benchmark for price movement. "
            "Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals."
        ),
        "boll_ub": (
            "Bollinger Upper Band: Typically 2 standard deviations above the middle line. "
            "Usage: Signals potential overbought conditions and breakout zones. "
            "Tips: Confirm signals with other tools; prices may ride the band in strong trends."
        ),
        "boll_lb": (
            "Bollinger Lower Band: Typically 2 standard deviations below the middle line. "
            "Usage: Indicates potential oversold conditions. "
            "Tips: Use additional analysis to avoid false reversal signals."
        ),
        "atr": (
            "ATR: Averages true range to measure volatility. "
            "Usage: Set stop-loss levels and adjust position sizes based on current market volatility. "
            "Tips: It's a reactive measure, so use it as part of a broader risk management strategy."
        ),
        # Volume-Based Indicators
        "vwma": (
            "VWMA: A moving average weighted by volume. "
            "Usage: Confirm trends by integrating price action with volume data. "
            "Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
        ),
        "mfi": (
            "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. "
            "Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. "
            "Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals."
        ),
    }

    if indicator not in best_ind_params:
        return f"Error: Indicator '{indicator}' is not supported. Please choose from: {list(best_ind_params.keys())}"
    
    try:
        # Get indicator data using StockstatsPolygonUtils
        result_df = StockstatsPolygonUtils.get_stock_stats_window(
            symbol=symbol,
            indicator=indicator,
            curr_date=curr_date,
            look_back_days=look_back_days
        )
        
        if result_df.empty:
            return f"No data found for symbol '{symbol}' and indicator '{indicator}' for the specified date range"
        
        # Format the results
        curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        start_date_dt = curr_date_dt - timedelta(days=look_back_days)
        start_date = start_date_dt.strftime("%Y-%m-%d")
        
        # Build the indicator values string
        ind_string = ""
        for _, row in result_df.iterrows():
            ind_string += f"{row['Date']}: {row[indicator]}\n"
        
        # Create the result with header and description
        result_str = (
            f"# {indicator.upper()} values for {symbol.upper()} from {start_date} to {curr_date} ({look_back_days} days)\n"
            f"# Total records: {len(result_df)}\n"
            f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"# Data source: Polygon.io (cached)\n\n"
            f"## {indicator} values:\n\n"
            + ind_string
            + "\n"
            + best_ind_params.get(indicator, "No description available.")
        )
        
        return result_str
        
    except Exception as e:
        return f"Error calculating {indicator} for {symbol}: {str(e)}"

