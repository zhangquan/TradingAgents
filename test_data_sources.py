#!/usr/bin/env python3
"""
数据源测试脚本
测试Yahoo Finance和Polygon API数据源的功能
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

def test_environment_config():
    """测试环境配置"""
    print("=== 测试环境配置 ===")
    
    from tradingagents.dataflows.environment_config import get_environment_config
    
    # 测试默认配置
    config = get_environment_config()
    print(f"当前环境: {config.environment.value}")
    print(f"当前数据源: {config.data_source.value}")
    print(f"是否为正式环境: {config.is_production}")
    print(f"是否为开发环境: {config.is_development}")
    print(f"使用Yahoo Finance: {config.use_yahoo_finance}")
    print(f"使用Polygon API: {config.use_polygon}")
    print(f"完整配置: {config.get_config()}")
    print()

def test_data_source_manager():
    """测试数据源管理器"""
    print("=== 测试数据源管理器 ===")
    
    from tradingagents.dataflows.data_source_manager import DataSourceManager
    
    try:
        # 初始化数据源管理器
        manager = DataSourceManager(require_api_key=False)
        
        print(f"当前数据源: {manager.current_data_source.value}")
        print(f"使用Polygon: {manager.is_using_polygon}")
        print(f"使用Yahoo Finance: {manager.is_using_yahoo_finance}")
        print(f"状态信息: {manager.get_status()}")
        print()
        
        return manager
    except Exception as e:
        print(f"数据源管理器初始化失败: {e}")
        return None

def test_stock_data_fetch(manager):
    """测试股票数据获取"""
    print("=== 测试股票数据获取 ===")
    
    if not manager:
        print("数据源管理器未初始化，跳过测试")
        return
    
    # 测试股票代码
    test_symbol = "AAPL"
    curr_date = datetime.now().strftime("%Y-%m-%d")
    look_back_days = 5
    
    print(f"测试股票: {test_symbol}")
    print(f"当前日期: {curr_date}")
    print(f"回看天数: {look_back_days}")
    print()
    
    try:
        # 测试获取股票数据
        print("正在获取股票数据...")
        data = manager.get_stock_data_window_cached(
            symbol=test_symbol,
            curr_date=curr_date,
            look_back_days=look_back_days,
            extend_cache=False  # 仅使用缓存，不联网
        )
        
        if not data.empty:
            print(f"成功获取数据，共 {len(data)} 条记录")
            print(f"数据列: {list(data.columns)}")
            print(f"日期范围: {data.index.min()} 到 {data.index.max()}")
            print("\n最近5条数据:")
            print(data.tail().round(2))
        else:
            print("未获取到数据")
        
        print()
        
        # 测试获取股票信息
        print("正在获取股票信息...")
        info = manager.get_stock_info(test_symbol)
        print(f"股票信息: {info}")
        print()
        
    except Exception as e:
        print(f"获取股票数据失败: {e}")
        print()

def test_data_services():
    """测试数据服务"""
    print("=== 测试数据服务 ===")
    
    from backend.services.data_services import DataServices
    
    try:
        # 初始化数据服务
        data_service = DataServices(require_api_key=False)
        
        print("数据服务初始化成功")
        
        # 获取数据源状态
        status = data_service.get_data_source_status()
        print(f"数据源状态: {status}")
        print()
        
        # 测试获取可用股票
        stocks = data_service.get_available_stocks()
        print(f"可用股票: {stocks}")
        print()
        
        # 测试获取股票数据
        test_symbol = "AAPL"
        curr_date = datetime.now().strftime("%Y-%m-%d")
        look_back_days = 5
        
        print(f"测试获取 {test_symbol} 的股票数据...")
        data = data_service.get_stock_data_window(test_symbol, curr_date, look_back_days)
        
        if not data.empty:
            print(f"成功获取数据，共 {len(data)} 条记录")
            print(f"数据列: {list(data.columns)}")
            print("\n最近3条数据:")
            print(data.tail(3).round(2))
        else:
            print("未获取到数据")
        
        print()
        
    except Exception as e:
        print(f"数据服务测试失败: {e}")
        print()

def main():
    """主函数"""
    print("数据源功能测试")
    print("=" * 50)
    print()
    
    # 测试环境配置
    test_environment_config()
    
    # 测试数据源管理器
    manager = test_data_source_manager()
    
    # 测试股票数据获取
    test_stock_data_fetch(manager)
    
    # 测试数据服务
    test_data_services()
    
    print("测试完成！")

if __name__ == "__main__":
    main()