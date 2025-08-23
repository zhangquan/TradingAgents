#!/usr/bin/env python3
"""
示例脚本：演示如何使用 Polygon 缓存数据接口

这个脚本展示了如何使用增强的缓存功能来高效地获取股票数据和技术指标。
"""

import os
from datetime import datetime, timedelta
from tradingagents.dataflows.stockstats_polygon_utils import StockstatsPolygonUtils
from tradingagents.dataflows.polygon_interface import get_polygon_cache_info, clear_polygon_cache

def demonstrate_cached_interface():
    """演示缓存数据接口的使用"""
    
    # 设置测试参数
    symbol = "AAPL"  # 苹果股票
    curr_date = "2024-01-15"  # 示例日期
    data_dir = "tradingagents/dataflows/data_cache"  # 数据目录
    
    print("=" * 60)
    print("Polygon 缓存数据接口演示")
    print("=" * 60)
    
    # 1. 检查缓存状态
    print(f"\n1. 检查 {symbol} 的缓存状态:")
    cache_info = get_polygon_cache_info(symbol)
    print(cache_info)
    
    # 2. 预加载数据（如果需要）
    print(f"\n2. 预加载 {symbol} 的历史数据:")
    success = StockstatsPolygonUtils.preload_data(symbol, years_back=5)
    print(f"预加载{'成功' if success else '失败'}")
    
    # 3. 获取单个技术指标
    print(f"\n3. 获取 {symbol} 在 {curr_date} 的 RSI 指标:")
    try:
        rsi = StockstatsPolygonUtils.get_stock_stats(
            symbol=symbol,
            indicator="rsi_14",  # 14天RSI
            curr_date=curr_date,
            data_dir=data_dir,
            online=True  # 使用缓存接口
        )
        print(f"RSI (14天): {rsi}")
    except Exception as e:
        print(f"获取RSI失败: {e}")
    
    # 4. 获取移动平均线
    print(f"\n4. 获取 {symbol} 在 {curr_date} 的移动平均线:")
    try:
        ma_20 = StockstatsPolygonUtils.get_stock_stats(
            symbol=symbol,
            indicator="close_20_sma",  # 20天简单移动平均
            curr_date=curr_date,
            data_dir=data_dir,
            online=True
        )
        print(f"SMA (20天): {ma_20}")
        
        ma_50 = StockstatsPolygonUtils.get_stock_stats(
            symbol=symbol,
            indicator="close_50_sma",  # 50天简单移动平均
            curr_date=curr_date,
            data_dir=data_dir,
            online=True
        )
        print(f"SMA (50天): {ma_50}")
    except Exception as e:
        print(f"获取移动平均线失败: {e}")
    
    # 5. 获取时间窗口数据
    print(f"\n5. 获取 {symbol} 过去30天的RSI数据:")
    try:
        rsi_window = StockstatsPolygonUtils.get_stock_stats_window(
            symbol=symbol,
            indicator="rsi_14",
            curr_date=curr_date,
            look_back_days=30,
            data_dir=data_dir,
            online=True
        )
        print(f"获取到 {len(rsi_window)} 条RSI数据")
        if not rsi_window.empty:
            print("最近5天的RSI值:")
            print(rsi_window.tail())
    except Exception as e:
        print(f"获取RSI窗口数据失败: {e}")
    
    # 6. 再次检查缓存状态
    print(f"\n6. 操作后的缓存状态:")
    cache_info_after = get_polygon_cache_info(symbol)
    print(cache_info_after)
    
    print(f"\n7. 缓存管理示例:")
    cache_details = StockstatsPolygonUtils.get_cache_info(symbol)
    if cache_details.get("exists"):
        print(f"缓存文件: {cache_details['path']}")
        print(f"数据范围: {cache_details['start_date']} 到 {cache_details['end_date']}")
        print(f"记录数量: {cache_details['record_count']}")
        print(f"文件大小: {cache_details['file_size_bytes']} 字节")
    else:
        print("没有找到缓存文件")

def demonstrate_multiple_symbols():
    """演示多个股票的批量处理"""
    
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    curr_date = "2024-01-15"
    
    print("\n" + "=" * 60)
    print("多股票批量处理演示")
    print("=" * 60)
    
    for symbol in symbols:
        print(f"\n处理 {symbol}:")
        try:
            # 预加载数据
            success = StockstatsPolygonUtils.preload_data(symbol, years_back=3)
            if success:
                # 获取一些关键指标
                rsi = StockstatsPolygonUtils.get_stock_stats(
                    symbol=symbol,
                    indicator="rsi_14",
                    curr_date=curr_date,
                    data_dir="tradingagents/dataflows/data_cache",
                    online=True
                )
                
                ma_20 = StockstatsPolygonUtils.get_stock_stats(
                    symbol=symbol,
                    indicator="close_20_sma",
                    curr_date=curr_date,
                    data_dir="tradingagents/dataflows/data_cache",
                    online=True
                )
                
                print(f"  RSI: {rsi}")
                print(f"  SMA(20): {ma_20}")
            else:
                print(f"  数据预加载失败")
                
        except Exception as e:
            print(f"  处理失败: {e}")

def cache_management_demo():
    """演示缓存管理功能"""
    
    print("\n" + "=" * 60)
    print("缓存管理功能演示")
    print("=" * 60)
    
    symbol = "AAPL"
    
    # 获取缓存信息
    print("1. 获取缓存信息:")
    cache_info = StockstatsPolygonUtils.get_cache_info(symbol)
    print(f"   缓存存在: {cache_info.get('exists', False)}")
    
    if cache_info.get('exists'):
        print(f"   数据范围: {cache_info.get('start_date')} 到 {cache_info.get('end_date')}")
        print(f"   记录数量: {cache_info.get('record_count')}")
        
        # 演示清除特定符号的缓存
        print(f"\n2. 清除 {symbol} 的缓存...")
        StockstatsPolygonUtils.clear_cache(symbol)
        print("   缓存已清除")
        
        # 验证缓存已被清除
        cache_info_after = StockstatsPolygonUtils.get_cache_info(symbol)
        print(f"   清除后缓存存在: {cache_info_after.get('exists', False)}")

if __name__ == "__main__":
    # 设置环境变量（如果还没有设置）
    if not os.getenv("POLYGON_API_KEY"):
        print("警告: 未设置 POLYGON_API_KEY 环境变量")
        print("请设置您的 Polygon.io API 密钥:")
        print("export POLYGON_API_KEY='your_api_key_here'")
        exit(1)
    
    try:
        # 运行演示
        demonstrate_cached_interface()
        demonstrate_multiple_symbols()
        cache_management_demo()
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()