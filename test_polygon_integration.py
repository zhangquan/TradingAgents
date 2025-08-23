#!/usr/bin/env python3
"""
测试 Polygon.io 集成
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_polygon_utils():
    """测试 PolygonUtils 类"""
    print("=== 测试 PolygonUtils 类 ===")
    load_dotenv()
    
    try:
        from tradingagents.dataflows.polygon_utils import PolygonUtils
        
        # 检查 API 密钥
        api_key = os.getenv("POLYGON_API_KEY")
        if not api_key:
            print("❌ POLYGON_API_KEY 环境变量未设置")
            return False
        
        print(f"✅ API 密钥已设置: {api_key[:10]}...")
        
        # 创建工具实例
        polygon_utils = PolygonUtils()
        print("✅ PolygonUtils 实例创建成功")
        
        # 测试获取公司信息
        print("\n--- 测试获取公司信息 ---")
        info = polygon_utils.get_stock_info("AAPL")
        print(f"公司信息: {info}")
        
        return True
        
    except Exception as e:
        print(f"❌ PolygonUtils 测试失败: {e}")
        return False

def test_polygon_interface():
    """测试 Polygon 接口函数"""
    print("\n=== 测试 Polygon 接口函数 ===")
    
    try:
        from tradingagents.dataflows.polygon_interface import get_polygon_company_info
        
        # 测试获取公司信息
        print("--- 测试获取公司信息 ---")
        info = get_polygon_company_info("AAPL")
        print(f"公司信息: {info[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Polygon 接口测试失败: {e}")
        return False

def test_polygon_toolkit():
    """测试 PolygonToolkit 类"""
    print("\n=== 测试 PolygonToolkit 类 ===")
    
    try:
        from tradingagents.agents.utils.agent_polygon_util import PolygonToolkit
        
        # 创建工具包实例
        toolkit = PolygonToolkit()
        print("✅ PolygonToolkit 实例创建成功")
        
        # 测试获取公司信息
        print("--- 测试获取公司信息 ---")
        info = toolkit.get_polygon_company_info("AAPL")
        print(f"公司信息: {info[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ PolygonToolkit 测试失败: {e}")
        return False

def test_data_retrieval():
    """测试数据获取功能"""
    print("\n=== 测试数据获取功能 ===")
    
    try:
        from tradingagents.dataflows.polygon_interface import get_polygon_data
        
        # 计算日期范围（最近7天）
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        print(f"获取 {start_date} 到 {end_date} 的 AAPL 数据...")
        
        # 测试获取股票数据
        data = get_polygon_data("AAPL", start_date, end_date)
        print(f"数据获取成功，长度: {len(data)} 字符")
        print(f"数据预览: {data[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据获取测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试 Polygon.io 集成...")
    print(f"当前时间: {datetime.now()}")
    print(f"Python 版本: {sys.version}")
    print()
    
    tests = [
        test_polygon_utils,
        test_polygon_interface,
        test_polygon_toolkit,
        test_data_retrieval,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Polygon.io 集成成功。")
        return True
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 