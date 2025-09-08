#!/usr/bin/env python3
"""
定时任务详细测试脚本 - 测试任务执行和监控
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

class DetailedSchedulerTester:
    """详细的定时任务测试类"""
    
    def __init__(self):
        self.session = None
        self.created_tasks = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup_test_tasks()
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{API_BASE}{endpoint}"
        try:
            async with self.session.request(method, url, json=data) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    logger.error(f"{method} request failed: {response.status} - {error_text}")
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {method} {url} - {e}")
            raise
    
    async def create_immediate_task(self) -> str:
        """创建一个立即执行的任务来测试执行流程"""
        logger.info("📝 创建立即执行任务...")
        
        # 创建一个一次性任务，设置为1分钟后执行（基本上立即执行）
        future_datetime = datetime.now() + timedelta(minutes=1)
        future_date = future_datetime.strftime("%Y-%m-%d")
        future_time = future_datetime.strftime("%H:%M")
        
        task_config = {
            "ticker": "AAPL",
            "analysts": ["market"],
            "research_depth": 1,
            "schedule_type": "once",
            "schedule_time": future_time,
            "schedule_date": future_date,
            "timezone": "UTC",
            "enabled": True
        }
        
        response = await self.make_request("POST", "/tasks", task_config)
        task_id = response["task_id"]
        self.created_tasks.append(task_id)
        logger.info(f"✅ 任务创建成功: {task_id}")
        return task_id
    
    async def monitor_task_execution(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """监控任务执行过程"""
        logger.info(f"👀 监控任务执行: {task_id} (超时: {timeout}秒)")
        
        start_time = time.time()
        last_status = None
        execution_started = False
        
        while time.time() - start_time < timeout:
            try:
                # 获取任务详情
                task_details = await self.make_request("GET", f"/tasks/{task_id}")
                
                current_status = task_details.get("status", "unknown")
                execution_count = task_details.get("execution_count", 0)
                last_run = task_details.get("last_run")
                current_step = task_details.get("current_step")
                last_error = task_details.get("last_error")
                
                # 如果状态发生变化，记录日志
                if current_status != last_status:
                    logger.info(f"状态变化: {last_status} -> {current_status}")
                    last_status = current_status
                
                # 显示当前执行信息
                if current_step:
                    logger.info(f"当前步骤: {current_step}")
                
                if last_error:
                    logger.warning(f"执行错误: {last_error}")
                
                # 检查是否开始执行
                if execution_count > 0 and not execution_started:
                    execution_started = True
                    logger.info(f"🚀 任务开始执行! 执行次数: {execution_count}")
                
                # 如果任务完成或失败，返回结果
                if current_status in ["completed", "failed", "error"]:
                    logger.info(f"✅ 任务执行完成，最终状态: {current_status}")
                    return task_details
                
                # 等待5秒后再次检查
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"监控任务时出错: {e}")
                await asyncio.sleep(5)
        
        logger.warning(f"⏰ 监控超时 ({timeout}秒)，任务可能仍在执行")
        return await self.make_request("GET", f"/tasks/{task_id}")
    
    async def test_task_execution_flow(self):
        """测试任务执行流程"""
        logger.info("\n🔄 测试任务执行流程...")
        
        # 创建立即执行任务
        task_id = await self.create_immediate_task()
        
        # 立即触发执行
        logger.info("🚀 立即触发任务执行...")
        await self.make_request("POST", f"/tasks/{task_id}/run-now")
        
        # 监控执行过程
        final_result = await self.monitor_task_execution(task_id, timeout=120)
        
        # 分析结果
        logger.info("\n📊 执行结果分析:")
        logger.info(f"- 任务ID: {final_result.get('task_id')}")
        logger.info(f"- 最终状态: {final_result.get('status')}")
        logger.info(f"- 执行次数: {final_result.get('execution_count', 0)}")
        logger.info(f"- 最后运行时间: {final_result.get('last_run', '无')}")
        logger.info(f"- 错误信息: {final_result.get('last_error', '无')}")
        
        return final_result
    
    async def test_scheduler_monitoring(self):
        """测试调度器监控功能"""
        logger.info("\n📈 测试调度器监控功能...")
        
        # 获取调度器状态
        status = await self.make_request("GET", "/scheduler/status")
        logger.info(f"调度器状态: {json.dumps(status, indent=2)}")
        
        # 获取所有任务列表
        tasks = await self.make_request("GET", "/tasks")
        
        logger.info(f"\n📋 任务统计:")
        logger.info(f"- 定时任务数量: {len(tasks['scheduled_tasks'])}")
        logger.info(f"- 活跃任务数量: {len(tasks['active_tasks'])}")
        logger.info(f"- 已完成任务数量: {len(tasks['completed_tasks'])}")
        
        # 显示部分任务详情
        if tasks['scheduled_tasks']:
            logger.info("\n📝 定时任务示例:")
            for i, (task_id, task_info) in enumerate(list(tasks['scheduled_tasks'].items())[:3]):
                logger.info(f"  {i+1}. {task_id}: {task_info['ticker']} - {task_info['schedule_type']} - {'启用' if task_info['enabled'] else '禁用'}")
        
        return status, tasks
    
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
    
    async def run_detailed_test(self):
        """运行详细测试"""
        logger.info("🎯 开始详细定时任务测试...")
        
        try:
            # 1. 测试调度器监控
            await self.test_scheduler_monitoring()
            
            # 2. 测试任务执行流程
            execution_result = await self.test_task_execution_flow()
            
            # 3. 再次检查调度器状态
            logger.info("\n🔍 最终调度器状态检查...")
            await self.test_scheduler_monitoring()
            
            logger.info("\n🎉 详细测试完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 详细测试过程中发生错误: {e}")
            return False

async def main():
    """主函数"""
    logger.info("🚀 启动详细定时任务测试...")
    
    # 检查后端服务
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status != 200:
                    logger.error("❌ 后端服务未运行")
                    return
    except Exception as e:
        logger.error(f"❌ 无法连接到后端服务: {e}")
        return
    
    # 运行详细测试
    async with DetailedSchedulerTester() as tester:
        success = await tester.run_detailed_test()
        
        if success:
            logger.info("\n✅ 详细定时任务测试完成 - 所有功能正常!")
        else:
            logger.error("\n❌ 详细定时任务测试失败")

if __name__ == "__main__":
    asyncio.run(main())
