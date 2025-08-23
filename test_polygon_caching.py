#!/usr/bin/env python3
"""
Test script for Polygon.io caching functionality
This script demonstrates the new caching features in PolygonUtils
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.polygon_utils import PolygonUtils
from tradingagents.dataflows.polygon_interface import (
    get_polygon_data,
    get_polygon_data_window,
    get_polygon_cache_info,
    clear_polygon_cache
)


def test_polygon_caching():
    """Test the Polygon.io caching functionality"""
    
    print("=" * 60)
    print("Testing Polygon.io Caching Functionality")
    print("=" * 60)
    
    # Test symbol
    symbol = "AAPL"
    
    # Test dates
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"\nTesting with symbol: {symbol}")
    print(f"Date range: {start_date} to {end_date}")
    
    try:
        # Initialize PolygonUtils
        print("\n1. Testing PolygonUtils directly...")
        polygon_utils = PolygonUtils()
        
        # Test cache info before any data fetch
        print("\n2. Checking initial cache status...")
        cache_info = polygon_utils.get_cache_info(symbol)
        print(f"Cache exists: {cache_info['exists']}")
        
        # Test cached data retrieval (first call - should fetch from API)
        print("\n3. First data fetch (should use API)...")
        data1 = polygon_utils.get_stock_data_cached(symbol, start_date, end_date)
        print(f"Retrieved {len(data1)} records")
        print(f"Date range: {data1.index.min()} to {data1.index.max()}")
        
        # Test cache info after data fetch
        print("\n4. Checking cache status after fetch...")
        cache_info = polygon_utils.get_cache_info(symbol)
        print(f"Cache exists: {cache_info['exists']}")
        if cache_info['exists']:
            print(f"Cached date range: {cache_info['start_date']} to {cache_info['end_date']}")
            print(f"Cached records: {cache_info['record_count']}")
            print(f"File size: {cache_info['file_size_bytes']} bytes")
        
        # Test cached data retrieval (second call - should use cache)
        print("\n5. Second data fetch (should use cache)...")
        data2 = polygon_utils.get_stock_data_cached(symbol, start_date, end_date)
        print(f"Retrieved {len(data2)} records")
        
        # Verify data consistency
        print("\n6. Verifying data consistency...")
        if data1.equals(data2):
            print("✅ Data consistency verified - both calls returned identical data")
        else:
            print("❌ Data inconsistency detected")
        
        # Test window method
        print("\n7. Testing window-based retrieval...")
        window_data = polygon_utils.get_stock_data_window_cached(symbol, end_date, 10)
        print(f"Window data: {len(window_data)} records for last 10 days")
        
        # Test interface functions
        print("\n8. Testing interface functions...")
        
        # Test get_polygon_data
        interface_result = get_polygon_data(symbol, start_date, end_date)
        print(f"Interface result length: {len(interface_result)} characters")
        
        # Test get_polygon_data_window  
        window_result = get_polygon_data_window(symbol, end_date, 5)
        print(f"Window result length: {len(window_result)} characters")
        
        # Test cache info through interface
        cache_info_result = get_polygon_cache_info(symbol)
        print("\n9. Cache info through interface:")
        print(cache_info_result)
        
        print("\n10. Testing cache clearing...")
        clear_result = clear_polygon_cache(symbol)
        print(clear_result)
        
        # Verify cache is cleared
        cache_info_after_clear = polygon_utils.get_cache_info(symbol)
        print(f"Cache exists after clear: {cache_info_after_clear['exists']}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Make sure POLYGON_API_KEY is set
    if not os.getenv("POLYGON_API_KEY"):
        print("❌ Please set POLYGON_API_KEY environment variable")
        print("You can get a free API key from https://polygon.io/")
        sys.exit(1)
    
    test_polygon_caching()