#!/usr/bin/env python3
"""
多数据源使用示例
演示如何在不同环境下使用不同的数据源
"""

import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.append('.')

def example_development_environment():
    """开发环境示例 - 使用 Polygon API"""
    print("=== 开发环境示例 (使用 Polygon API) ===")
    
    # 设置开发环境
    os.environ['ENVIRONMENT'] = 'development'
    os.environ['POLYGON_API_KEY'] = 'your_polygon_api_key_here'  # 实际使用时替换为真实密钥
    
    from tradingagents.dataflows.environment_config import get_environment_config
    from tradingagents.dataflows.data_source_manager import DataSourceManager
    
    # 获取环境配置
    config = get_environment_config()
    print(f"环境: {config.environment.value}")
    print(f"数据源: {config.data_source.value}")
    print(f"使用Polygon: {config.use_polygon}")
    print()
    
    # 初始化数据源管理器
    try:
        manager = DataSourceManager(require_api_key=True)
        print(f"数据源管理器初始化成功: {manager.current_data_source.value}")
        
        # 获取状态信息
        status = manager.get_status()
        print(f"状态信息: {status}")
        
    except Exception as e:
        print(f"数据源管理器初始化失败: {e}")
    
    print()

def example_production_environment():
    """正式环境示例 - 使用 Yahoo Finance"""
    print("=== 正式环境示例 (使用 Yahoo Finance) ===")
    
    # 设置正式环境
    os.environ['ENVIRONMENT'] = 'production'
    
    from tradingagents.dataflows.environment_config import get_environment_config
    from tradingagents.dataflows.data_source_manager import DataSourceManager
    
    # 获取环境配置
    config = get_environment_config()
    print(f"环境: {config.environment.value}")
    print(f"数据源: {config.data_source.value}")
    print(f"使用Yahoo Finance: {config.use_yahoo_finance}")
    print()
    
    # 初始化数据源管理器
    try:
        manager = DataSourceManager(require_api_key=False)  # Yahoo Finance不需要API密钥
        print(f"数据源管理器初始化成功: {manager.current_data_source.value}")
        
        # 获取状态信息
        status = manager.get_status()
        print(f"状态信息: {status}")
        
    except Exception as e:
        print(f"数据源管理器初始化失败: {e}")
    
    print()

def example_manual_override():
    """手动覆盖示例 - 强制使用特定数据源"""
    print("=== 手动覆盖示例 (强制使用 Yahoo Finance) ===")
    
    # 强制使用 Yahoo Finance
    os.environ['DATA_SOURCE'] = 'yahoo_finance'
    
    from tradingagents.dataflows.environment_config import get_environment_config
    from tradingagents.dataflows.data_source_manager import DataSourceManager
    
    # 获取环境配置
    config = get_environment_config()
    print(f"环境: {config.environment.value}")
    print(f"数据源: {config.data_source.value}")
    print(f"使用Yahoo Finance: {config.use_yahoo_finance}")
    print(f"使用Polygon: {config.use_polygon}")
    print()
    
    # 初始化数据源管理器
    try:
        manager = DataSourceManager(require_api_key=False)
        print(f"数据源管理器初始化成功: {manager.current_data_source.value}")
        
    except Exception as e:
        print(f"数据源管理器初始化失败: {e}")
    
    print()

def example_data_services():
    """数据服务示例"""
    print("=== 数据服务示例 ===")
    
    # 设置环境
    os.environ['ENVIRONMENT'] = 'development'
    
    try:
        from backend.services.data_services import DataServices
        
        # 初始化数据服务
        data_service = DataServices(require_api_key=False)
        print("数据服务初始化成功")
        
        # 获取数据源状态
        status = data_service.get_data_source_status()
        print(f"数据源状态: {status}")
        
        # 获取可用股票
        stocks = data_service.get_available_stocks()
        print(f"可用股票: {stocks}")
        
    except Exception as e:
        print(f"数据服务初始化失败: {e}")
    
    print()

def main():
    """主函数"""
    print("多数据源使用示例")
    print("=" * 50)
    print()
    
    # 开发环境示例
    example_development_environment()
    
    # 正式环境示例
    example_production_environment()
    
    # 手动覆盖示例
    example_manual_override()
    
    # 数据服务示例
    example_data_services()
    
    print("示例完成！")
    print()
    print("使用说明:")
    print("1. 开发环境: 设置 ENVIRONMENT=development，使用 Polygon API")
    print("2. 正式环境: 设置 ENVIRONMENT=production，使用 Yahoo Finance")
    print("3. 手动覆盖: 设置 DATA_SOURCE=yahoo_finance 或 polygon")
    print("4. API 密钥: 开发环境需要设置 POLYGON_API_KEY")

if __name__ == "__main__":
    main()