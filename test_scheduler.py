#!/usr/bin/env python3
"""
定时任务测试脚本 - 测试 TradingAgents 系统的定时任务功能
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API 基础配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/analysis"

class SchedulerTester:
    """定时任务测试类"""
    
    def __init__(self):
        self.session = None
        self.created_tasks = []  # 记录创建的测试任务，便于清理
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        # 清理创建的测试任务
        await self.cleanup_test_tasks()
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{API_BASE}{endpoint}"
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"GET request failed: {response.status} - {error_text}")
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"POST request failed: {response.status} - {error_text}")
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"PUT request failed: {response.status} - {error_text}")
                    response.raise_for_status()
                    return await response.json()
            elif method.upper() == "DELETE":
                async with self.session.delete(url) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"DELETE request failed: {response.status} - {error_text}")
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {method} {url} - {e}")
            raise
    
    async def test_scheduler_status(self) -> bool:
        """测试调度器状态"""
        logger.info("🔍 测试调度器状态...")
        try:
            status = await self.make_request("GET", "/scheduler/status")
            logger.info(f"调度器状态: {json.dumps(status, indent=2)}")
            
            if not status.get("running"):
                logger.error("❌ 调度器未运行!")
                return False
            
            logger.info("✅ 调度器运行正常")
            return True
        except Exception as e:
            logger.error(f"❌ 获取调度器状态失败: {e}")
            return False
    
    async def create_test_task(self, task_config: Dict[str, Any]) -> str:
        """创建测试任务"""
        logger.info(f"📝 创建测试任务: {task_config['ticker']} - {task_config['schedule_type']}")
        try:
            response = await self.make_request("POST", "/tasks", task_config)
            task_id = response["task_id"]
            self.created_tasks.append(task_id)
            logger.info(f"✅ 任务创建成功: {task_id}")
            return task_id
        except Exception as e:
            logger.error(f"❌ 任务创建失败: {e}")
            raise
    
    async def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """获取任务详情"""
        try:
            return await self.make_request("GET", f"/tasks/{task_id}")
        except Exception as e:
            logger.error(f"❌ 获取任务详情失败: {e}")
            raise
    
    async def run_task_now(self, task_id: str) -> Dict[str, Any]:
        """立即执行任务"""
        logger.info(f"🚀 立即执行任务: {task_id}")
        try:
            response = await self.make_request("POST", f"/tasks/{task_id}/run-now")
            logger.info(f"✅ 任务执行启动成功: {response['message']}")
            return response
        except Exception as e:
            logger.error(f"❌ 任务执行失败: {e}")
            raise
    
    async def toggle_task(self, task_id: str) -> Dict[str, Any]:
        """切换任务状态"""
        logger.info(f"🔄 切换任务状态: {task_id}")
        try:
            response = await self.make_request("PUT", f"/tasks/{task_id}/toggle")
            logger.info(f"✅ 任务状态切换成功: {response['message']}")
            return response
        except Exception as e:
            logger.error(f"❌ 任务状态切换失败: {e}")
            raise
    
    async def list_all_tasks(self) -> Dict[str, Any]:
        """列出所有任务"""
        try:
            return await self.make_request("GET", "/tasks")
        except Exception as e:
            logger.error(f"❌ 获取任务列表失败: {e}")
            raise
    
    async def cleanup_test_tasks(self):
        """清理测试任务"""
        if not self.created_tasks:
            return
        
        logger.info(f"🧹 清理测试任务: {len(self.created_tasks)} 个任务")
        for task_id in self.created_tasks:
            try:
                await self.make_request("DELETE", f"/tasks/{task_id}")
                logger.info(f"✅ 删除任务: {task_id}")
            except Exception as e:
                logger.warning(f"⚠️ 删除任务失败 {task_id}: {e}")
    
    async def test_create_daily_task(self) -> str:
        """测试创建每日任务"""
        logger.info("\n📅 测试创建每日定时任务...")
        
        # 计算明天的时间（避免立即执行）
        future_time = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M")
        
        task_config = {
            "ticker": "AAPL",
            "analysts": ["market", "news"],
            "research_depth": 1,
            "schedule_type": "daily",
            "schedule_time": future_time,
            "timezone": "UTC",
            "enabled": True
        }
        
        task_id = await self.create_test_task(task_config)
        
        # 验证任务创建
        task_details = await self.get_task_details(task_id)
        assert task_details["schedule_type"] == "daily"
        assert task_details["ticker"] == "AAPL"
        assert task_details["enabled"] == True
        
        logger.info("✅ 每日任务创建测试通过")
        return task_id
    
    async def test_create_once_task(self) -> str:
        """测试创建一次性任务"""
        logger.info("\n⏰ 测试创建一次性定时任务...")
        
        # 设置5分钟后执行
        future_datetime = datetime.now() + timedelta(minutes=5)
        future_date = future_datetime.strftime("%Y-%m-%d")
        future_time = future_datetime.strftime("%H:%M")
        
        task_config = {
            "ticker": "TSLA",
            "analysts": ["fundamentals"],
            "research_depth": 1,
            "schedule_type": "once",
            "schedule_time": future_time,
            "schedule_date": future_date,
            "timezone": "UTC",
            "enabled": True
        }
        
        task_id = await self.create_test_task(task_config)
        
        # 验证任务创建
        task_details = await self.get_task_details(task_id)
        assert task_details["schedule_type"] == "once"
        assert task_details["ticker"] == "TSLA"
        assert task_details["schedule_date"] == future_date
        
        logger.info("✅ 一次性任务创建测试通过")
        return task_id
    
    async def test_immediate_execution(self, task_id: str):
        """测试立即执行任务"""
        logger.info(f"\n🚀 测试立即执行任务: {task_id}...")
        
        # 获取执行前的任务状态
        before_details = await self.get_task_details(task_id)
        logger.info(f"执行前状态: {before_details.get('last_run', '无')}")
        
        # 立即执行任务
        result = await self.run_task_now(task_id)
        assert result["status"] == "started"
        
        # 等待一段时间让任务开始执行
        logger.info("⏳ 等待任务开始执行...")
        await asyncio.sleep(5)
        
        # 检查任务执行状态
        after_details = await self.get_task_details(task_id)
        execution_count = after_details.get("execution_count", 0)
        
        logger.info(f"执行后状态: 执行次数={execution_count}")
        logger.info("✅ 立即执行任务测试通过")
    
    async def test_task_toggle(self, task_id: str):
        """测试任务启用/禁用"""
        logger.info(f"\n🔄 测试任务启用/禁用: {task_id}...")
        
        # 获取当前状态
        details = await self.get_task_details(task_id)
        original_enabled = details["enabled"]
        logger.info(f"原始状态: enabled={original_enabled}")
        
        # 切换状态
        result = await self.toggle_task(task_id)
        new_enabled = result["enabled"]
        
        # 验证状态已改变
        assert new_enabled != original_enabled
        
        # 再次切换回原状态
        result2 = await self.toggle_task(task_id)
        final_enabled = result2["enabled"]
        
        # 验证状态已恢复
        assert final_enabled == original_enabled
        
        logger.info("✅ 任务启用/禁用测试通过")
    
    async def test_list_tasks(self):
        """测试任务列表功能"""
        logger.info("\n📋 测试任务列表功能...")
        
        tasks = await self.list_all_tasks()
        
        # 验证返回结构
        assert "scheduled_tasks" in tasks
        assert "active_tasks" in tasks
        assert "completed_tasks" in tasks
        
        scheduled_count = len(tasks["scheduled_tasks"])
        active_count = len(tasks["active_tasks"])
        completed_count = len(tasks["completed_tasks"])
        
        logger.info(f"任务统计: 定时任务={scheduled_count}, 活跃任务={active_count}, 完成任务={completed_count}")
        logger.info("✅ 任务列表功能测试通过")
        
        return tasks
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        logger.info("🎯 开始定时任务综合测试...")
        
        try:
            # 1. 测试调度器状态
            if not await self.test_scheduler_status():
                logger.error("❌ 调度器状态测试失败，停止测试")
                return False
            
            # 2. 测试任务列表（初始状态）
            await self.test_list_tasks()
            
            # 3. 创建测试任务
            daily_task_id = await self.test_create_daily_task()
            once_task_id = await self.test_create_once_task()
            
            # 4. 测试任务启用/禁用
            await self.test_task_toggle(daily_task_id)
            
            # 5. 测试立即执行
            await self.test_immediate_execution(daily_task_id)
            
            # 6. 再次检查任务列表
            final_tasks = await self.test_list_tasks()
            
            # 验证我们创建的任务存在
            scheduled_tasks = final_tasks["scheduled_tasks"]
            assert daily_task_id in scheduled_tasks
            assert once_task_id in scheduled_tasks
            
            logger.info("🎉 所有测试通过！定时任务功能运行正常")
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {e}")
            return False

async def main():
    """主函数"""
    logger.info("🚀 启动定时任务测试...")
    
    # 检查后端服务是否运行
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status != 200:
                    logger.error("❌ 后端服务未运行，请先启动后端服务")
                    return
    except Exception as e:
        logger.error(f"❌ 无法连接到后端服务: {e}")
        logger.info("💡 请确保后端服务在 http://localhost:8000 运行")
        return
    
    # 运行测试
    async with SchedulerTester() as tester:
        success = await tester.run_comprehensive_test()
        
        if success:
            logger.info("\n✅ 定时任务测试完成 - 所有功能正常!")
        else:
            logger.error("\n❌ 定时任务测试失败 - 请检查系统配置")

if __name__ == "__main__":
    asyncio.run(main())
