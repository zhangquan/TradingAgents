#!/usr/bin/env python3
"""
Polygon 缓存管理工具

这个工具提供了完整的缓存管理功能，包括：
- 查看所有缓存状态
- 预加载数据
- 清理过期缓存
- 缓存统计信息
"""

import os
import argparse
from datetime import datetime, timedelta
from tradingagents.dataflows.stockstats_polygon_utils import StockstatsPolygonUtils
from tradingagents.dataflows.polygon_interface import get_polygon_cache_info, clear_polygon_cache
from tradingagents.dataflows.config import get_config

def list_all_caches():
    """列出所有缓存文件"""
    try:
        config = get_config()
        cache_dir = config["data_cache_dir"]
        
        if not os.path.exists(cache_dir):
            print("缓存目录不存在")
            return
        
        print(f"缓存目录: {cache_dir}")
        print("-" * 80)
        print(f"{'股票代码':<10} {'开始日期':<12} {'结束日期':<12} {'记录数':<8} {'文件大小':<10} {'最后修改':<20}")
        print("-" * 80)
        
        cache_files = [f for f in os.listdir(cache_dir) if f.endswith("-Polygon-data.csv")]
        
        if not cache_files:
            print("未找到缓存文件")
            return
        
        total_size = 0
        total_records = 0
        
        for cache_file in sorted(cache_files):
            symbol = cache_file.replace("-Polygon-data.csv", "")
            cache_info = StockstatsPolygonUtils.get_cache_info(symbol)
            
            if cache_info.get("exists"):
                size_mb = cache_info["file_size_bytes"] / (1024 * 1024)
                total_size += cache_info["file_size_bytes"]
                total_records += cache_info["record_count"]
                
                print(f"{symbol:<10} {cache_info['start_date']:<12} {cache_info['end_date']:<12} "
                      f"{cache_info['record_count']:<8} {size_mb:.1f}MB{'':<4} {cache_info['last_modified']:<20}")
        
        print("-" * 80)
        print(f"总计: {len(cache_files)} 个缓存文件, {total_records} 条记录, {total_size/(1024*1024):.1f}MB")
        
    except Exception as e:
        print(f"列出缓存时发生错误: {e}")

def preload_symbols(symbols, years_back=5):
    """预加载指定股票的数据"""
    print(f"预加载 {len(symbols)} 个股票的数据 (回溯 {years_back} 年)...")
    print("-" * 50)
    
    success_count = 0
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] 正在处理 {symbol}...", end=" ")
        try:
            success = StockstatsPolygonUtils.preload_data(symbol, years_back)
            if success:
                print("✓ 成功")
                success_count += 1
            else:
                print("✗ 失败")
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    print("-" * 50)
    print(f"完成! 成功: {success_count}/{len(symbols)}")

def clean_old_caches(days_old=30):
    """清理超过指定天数的缓存"""
    try:
        config = get_config()
        cache_dir = config["data_cache_dir"]
        
        if not os.path.exists(cache_dir):
            print("缓存目录不存在")
            return
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        removed_count = 0
        removed_size = 0
        
        print(f"清理超过 {days_old} 天的缓存文件...")
        print("-" * 50)
        
        cache_files = [f for f in os.listdir(cache_dir) if f.endswith("-Polygon-data.csv")]
        
        for cache_file in cache_files:
            file_path = os.path.join(cache_dir, cache_file)
            file_stat = os.stat(file_path)
            file_modified = datetime.fromtimestamp(file_stat.st_mtime)
            
            if file_modified < cutoff_date:
                symbol = cache_file.replace("-Polygon-data.csv", "")
                print(f"删除 {symbol} 的缓存 (修改于 {file_modified.strftime('%Y-%m-%d %H:%M:%S')})")
                
                removed_size += file_stat.st_size
                os.remove(file_path)
                removed_count += 1
        
        print("-" * 50)
        if removed_count > 0:
            print(f"已删除 {removed_count} 个缓存文件, 释放空间 {removed_size/(1024*1024):.1f}MB")
        else:
            print("没有找到需要清理的缓存文件")
            
    except Exception as e:
        print(f"清理缓存时发生错误: {e}")

def cache_statistics():
    """显示缓存统计信息"""
    try:
        config = get_config()
        cache_dir = config["data_cache_dir"]
        
        if not os.path.exists(cache_dir):
            print("缓存目录不存在")
            return
        
        cache_files = [f for f in os.listdir(cache_dir) if f.endswith("-Polygon-data.csv")]
        
        if not cache_files:
            print("未找到缓存文件")
            return
        
        total_size = 0
        total_records = 0
        oldest_date = None
        newest_date = None
        file_ages = []
        
        print("缓存统计信息")
        print("=" * 40)
        
        for cache_file in cache_files:
            symbol = cache_file.replace("-Polygon-data.csv", "")
            cache_info = StockstatsPolygonUtils.get_cache_info(symbol)
            
            if cache_info.get("exists"):
                total_size += cache_info["file_size_bytes"]
                total_records += cache_info["record_count"]
                
                start_date = datetime.strptime(cache_info["start_date"], "%Y-%m-%d")
                end_date = datetime.strptime(cache_info["end_date"], "%Y-%m-%d")
                
                if oldest_date is None or start_date < oldest_date:
                    oldest_date = start_date
                if newest_date is None or end_date > newest_date:
                    newest_date = end_date
                
                # 计算文件年龄
                modified_time = datetime.strptime(cache_info["last_modified"], "%Y-%m-%d %H:%M:%S")
                age_days = (datetime.now() - modified_time).days
                file_ages.append(age_days)
        
        print(f"缓存文件数量: {len(cache_files)}")
        print(f"总记录数量: {total_records:,}")
        print(f"总文件大小: {total_size/(1024*1024):.1f} MB")
        print(f"数据时间范围: {oldest_date.strftime('%Y-%m-%d')} 到 {newest_date.strftime('%Y-%m-%d')}")
        
        if file_ages:
            avg_age = sum(file_ages) / len(file_ages)
            max_age = max(file_ages)
            min_age = min(file_ages)
            
            print(f"缓存文件年龄: 平均 {avg_age:.1f} 天, 最新 {min_age} 天, 最老 {max_age} 天")
        
        # 存储空间利用率
        if total_size > 0:
            avg_file_size = total_size / len(cache_files) / (1024 * 1024)
            print(f"平均文件大小: {avg_file_size:.1f} MB")
        
    except Exception as e:
        print(f"获取统计信息时发生错误: {e}")

def validate_caches():
    """验证缓存文件的完整性"""
    try:
        config = get_config()
        cache_dir = config["data_cache_dir"]
        
        if not os.path.exists(cache_dir):
            print("缓存目录不存在")
            return
        
        cache_files = [f for f in os.listdir(cache_dir) if f.endswith("-Polygon-data.csv")]
        
        if not cache_files:
            print("未找到缓存文件")
            return
        
        print("验证缓存文件完整性...")
        print("-" * 50)
        
        valid_count = 0
        invalid_files = []
        
        for cache_file in cache_files:
            symbol = cache_file.replace("-Polygon-data.csv", "")
            print(f"验证 {symbol}...", end=" ")
            
            try:
                cache_info = StockstatsPolygonUtils.get_cache_info(symbol)
                if cache_info.get("exists") and cache_info.get("record_count", 0) > 0:
                    print("✓ 有效")
                    valid_count += 1
                else:
                    print("✗ 无效或为空")
                    invalid_files.append(symbol)
            except Exception as e:
                print(f"✗ 错误: {e}")
                invalid_files.append(symbol)
        
        print("-" * 50)
        print(f"验证完成: {valid_count}/{len(cache_files)} 个文件有效")
        
        if invalid_files:
            print(f"无效文件: {', '.join(invalid_files)}")
        
    except Exception as e:
        print(f"验证缓存时发生错误: {e}")

def main():
    parser = argparse.ArgumentParser(description="Polygon 缓存管理工具")
    parser.add_argument("action", choices=["list", "preload", "clean", "stats", "validate", "clear"],
                       help="要执行的操作")
    parser.add_argument("--symbols", nargs="+", help="股票代码列表 (用于预加载)")
    parser.add_argument("--years", type=int, default=5, help="预加载数据的年数 (默认5年)")
    parser.add_argument("--days", type=int, default=30, help="清理多少天前的缓存 (默认30天)")
    parser.add_argument("--symbol", help="特定股票代码 (用于清除)")
    
    args = parser.parse_args()
    
    if args.action == "list":
        list_all_caches()
    
    elif args.action == "preload":
        if not args.symbols:
            print("错误: 预加载需要指定股票代码")
            print("使用示例: python cache_management_tool.py preload --symbols AAPL GOOGL MSFT")
            return
        preload_symbols(args.symbols, args.years)
    
    elif args.action == "clean":
        clean_old_caches(args.days)
    
    elif args.action == "stats":
        cache_statistics()
    
    elif args.action == "validate":
        validate_caches()
    
    elif args.action == "clear":
        if args.symbol:
            print(f"清除 {args.symbol} 的缓存...")
            StockstatsPolygonUtils.clear_cache(args.symbol)
            print("完成!")
        else:
            response = input("确认要清除所有缓存吗? (y/N): ")
            if response.lower() == 'y':
                print("清除所有缓存...")
                StockstatsPolygonUtils.clear_cache()
                print("完成!")
            else:
                print("操作已取消")

if __name__ == "__main__":
    main()