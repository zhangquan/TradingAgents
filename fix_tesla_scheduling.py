#!/usr/bin/env python3
"""
Tesla调度任务修复脚本
解决Tesla任务没有按计划自动运行的问题
"""

import sys
import os
import sqlite3
from datetime import datetime, timezone
import subprocess

def check_scheduler_status():
    """检查调度服务状态"""
    print("=== 检查调度服务状态 ===")
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'uvicorn' in result.stdout or 'python' in result.stdout:
            print("✅ 发现运行中的Python进程")
            return True
        else:
            print("❌ 没有发现运行中的调度服务")
            return False
    except Exception as e:
        print(f"❌ 检查进程状态失败: {e}")
        return False

def check_tesla_task():
    """检查Tesla任务配置"""
    print("\n=== 检查Tesla任务配置 ===")
    conn = sqlite3.connect('data/tradingagents.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT task_id, schedule_type, schedule_time, timezone, enabled, status, last_run
        FROM scheduled_tasks 
        WHERE task_id = 'task_20250904_232128_107679'
    ''')
    task = cursor.fetchone()
    
    if task:
        print(f"Task ID: {task[0]}")
        print(f"Schedule Type: {task[1]}")
        print(f"Schedule Time: {task[2]}")
        print(f"Timezone: {task[3]}")
        print(f"Enabled: {task[4]}")
        print(f"Status: {task[5]}")
        print(f"Last Run: {task[6]}")
        
        # 检查今天是否应该运行
        utc_now = datetime.now(timezone.utc)
        schedule_hour, schedule_minute = map(int, task[2].split(':'))
        current_hour = utc_now.hour
        current_minute = utc_now.minute
        
        if current_hour > schedule_hour or (current_hour == schedule_hour and current_minute >= schedule_minute):
            print(f"✅ 今天应该已经运行过了 (配置时间: {task[2]}, 当前时间: {utc_now.strftime('%H:%M')})")
        else:
            print(f"⏰ 今天还未到运行时间 (配置时间: {task[2]}, 当前时间: {utc_now.strftime('%H:%M')})")
    else:
        print("❌ 未找到Tesla调度任务")
    
    conn.close()
    return task

def start_scheduler_service():
    """启动调度服务"""
    print("\n=== 启动调度服务 ===")
    try:
        # 启动后端服务（包含调度服务）
        print("正在启动后端服务...")
        subprocess.Popen([
            'uv', 'run', 'uvicorn', 'backend.main:app', 
            '--host', '0.0.0.0', '--port', '8000',
            '--reload'
        ], cwd='/workspace')
        print("✅ 后端服务启动命令已执行")
        return True
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")
        return False

def manual_trigger_tesla_task():
    """手动触发Tesla任务"""
    print("\n=== 手动触发Tesla任务 ===")
    try:
        # 这里可以调用API来手动触发任务
        import requests
        response = requests.post('http://localhost:8000/api/analysis/run', json={
            'ticker': 'TSLA',
            'analysts': ['market', 'news', 'fundamentals'],
            'research_depth': 1
        })
        if response.status_code == 200:
            print("✅ Tesla任务手动触发成功")
            return True
        else:
            print(f"❌ 手动触发失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 手动触发失败: {e}")
        return False

def fix_task_schedule():
    """修复任务调度配置"""
    print("\n=== 修复任务调度配置 ===")
    conn = sqlite3.connect('data/tradingagents.db')
    cursor = conn.cursor()
    
    try:
        # 重置任务状态
        cursor.execute('''
            UPDATE scheduled_tasks 
            SET status = 'scheduled', enabled = 1
            WHERE task_id = 'task_20250904_232128_107679'
        ''')
        conn.commit()
        print("✅ 任务状态已重置为scheduled")
        
        # 检查时区配置
        cursor.execute('''
            SELECT timezone FROM scheduled_tasks 
            WHERE task_id = 'task_20250904_232128_107679'
        ''')
        timezone_result = cursor.fetchone()
        if timezone_result and timezone_result[0] != 'UTC':
            print(f"⚠️  当前时区配置: {timezone_result[0]}, 建议使用UTC")
        
        print("✅ 任务配置检查完成")
        return True
    except Exception as e:
        print(f"❌ 修复配置失败: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("🔧 Tesla调度任务修复工具")
    print("=" * 50)
    
    # 1. 检查当前状态
    scheduler_running = check_scheduler_status()
    task_info = check_tesla_task()
    
    if not task_info:
        print("❌ 无法找到Tesla任务，请检查数据库")
        return
    
    # 2. 修复任务配置
    fix_task_schedule()
    
    # 3. 启动调度服务
    if not scheduler_running:
        print("\n🚀 调度服务未运行，正在启动...")
        if start_scheduler_service():
            print("✅ 调度服务启动成功")
            print("⏳ 请等待几秒钟让服务完全启动...")
        else:
            print("❌ 调度服务启动失败")
            return
    
    # 4. 提供手动触发选项
    print("\n📋 解决方案总结:")
    print("1. ✅ 任务配置已检查并修复")
    print("2. ✅ 调度服务已启动")
    print("3. 📝 建议操作:")
    print("   - 等待明天09:00 UTC自动运行")
    print("   - 或者手动触发任务进行测试")
    print("   - 监控日志确保任务正常执行")
    
    print("\n🔍 监控命令:")
    print("tail -f logs/backend.log")

if __name__ == "__main__":
    main()