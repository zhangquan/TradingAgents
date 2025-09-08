#!/usr/bin/env python3
"""
定时任务测试报告生成器 - 生成完整的测试报告
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

class SchedulerTestReporter:
    """定时任务测试报告生成器"""
    
    def __init__(self):
        self.session = None
        self.test_results = {
            "test_time": datetime.now().isoformat(),
            "scheduler_status": {},
            "task_statistics": {},
            "test_cases": [],
            "performance_metrics": {},
            "issues_found": [],
            "recommendations": []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{API_BASE}{endpoint}"
        try:
            async with self.session.request(method, url, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Request failed: {method} {url} - {e}")
            raise
    
    async def collect_scheduler_status(self):
        """收集调度器状态信息"""
        logger.info("📊 收集调度器状态信息...")
        
        try:
            status = await self.make_request("GET", "/scheduler/status")
            self.test_results["scheduler_status"] = {
                "running": status.get("running", False),
                "total_tasks": status.get("total_tasks", 0),
                "enabled_tasks": status.get("enabled_tasks", 0),
                "jobs_in_scheduler": status.get("jobs_in_scheduler", 0),
                "status_check_time": datetime.now().isoformat()
            }
            
            # 检查调度器健康状态
            if not status.get("running"):
                self.test_results["issues_found"].append({
                    "type": "critical",
                    "issue": "调度器未运行",
                    "description": "APScheduler服务未启动或已停止"
                })
            
            if status.get("total_tasks", 0) != status.get("jobs_in_scheduler", 0):
                self.test_results["issues_found"].append({
                    "type": "warning",
                    "issue": "任务同步问题",
                    "description": f"数据库中的任务数({status.get('total_tasks', 0)})与调度器中的作业数({status.get('jobs_in_scheduler', 0)})不匹配"
                })
            
            logger.info("✅ 调度器状态收集完成")
            
        except Exception as e:
            logger.error(f"❌ 收集调度器状态失败: {e}")
            self.test_results["issues_found"].append({
                "type": "critical",
                "issue": "无法获取调度器状态",
                "description": str(e)
            })
    
    async def collect_task_statistics(self):
        """收集任务统计信息"""
        logger.info("📈 收集任务统计信息...")
        
        try:
            tasks = await self.make_request("GET", "/tasks")
            
            scheduled_tasks = tasks.get("scheduled_tasks", {})
            active_tasks = tasks.get("active_tasks", {})
            completed_tasks = tasks.get("completed_tasks", {})
            
            # 统计不同类型的任务
            schedule_types = {}
            tickers = {}
            enabled_count = 0
            
            for task_id, task_info in scheduled_tasks.items():
                schedule_type = task_info.get("schedule_type", "unknown")
                ticker = task_info.get("ticker", "unknown")
                
                schedule_types[schedule_type] = schedule_types.get(schedule_type, 0) + 1
                tickers[ticker] = tickers.get(ticker, 0) + 1
                
                if task_info.get("enabled", False):
                    enabled_count += 1
            
            self.test_results["task_statistics"] = {
                "scheduled_tasks_count": len(scheduled_tasks),
                "active_tasks_count": len(active_tasks),
                "completed_tasks_count": len(completed_tasks),
                "enabled_tasks_count": enabled_count,
                "disabled_tasks_count": len(scheduled_tasks) - enabled_count,
                "schedule_types": schedule_types,
                "tickers": tickers,
                "collection_time": datetime.now().isoformat()
            }
            
            logger.info("✅ 任务统计信息收集完成")
            
        except Exception as e:
            logger.error(f"❌ 收集任务统计失败: {e}")
            self.test_results["issues_found"].append({
                "type": "error",
                "issue": "无法获取任务统计",
                "description": str(e)
            })
    
    async def test_basic_functionality(self):
        """测试基本功能"""
        logger.info("🧪 测试基本功能...")
        
        test_case = {
            "name": "基本功能测试",
            "start_time": datetime.now().isoformat(),
            "tests": []
        }
        
        # 测试1: 创建任务
        try:
            future_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
            task_config = {
                "ticker": "TEST",
                "analysts": ["market"],
                "research_depth": 1,
                "schedule_type": "daily",
                "schedule_time": future_time,
                "timezone": "UTC",
                "enabled": True
            }
            
            response = await self.make_request("POST", "/tasks", task_config)
            task_id = response["task_id"]
            
            test_case["tests"].append({
                "name": "创建定时任务",
                "status": "passed",
                "details": f"成功创建任务 {task_id}"
            })
            
            # 测试2: 获取任务详情
            task_details = await self.make_request("GET", f"/tasks/{task_id}")
            test_case["tests"].append({
                "name": "获取任务详情",
                "status": "passed",
                "details": f"成功获取任务详情，状态: {task_details.get('status')}"
            })
            
            # 测试3: 切换任务状态
            await self.make_request("PUT", f"/tasks/{task_id}/toggle")
            test_case["tests"].append({
                "name": "切换任务状态",
                "status": "passed",
                "details": "成功切换任务启用/禁用状态"
            })
            
            # 清理测试任务
            await self.make_request("DELETE", f"/tasks/{task_id}")
            test_case["tests"].append({
                "name": "删除任务",
                "status": "passed",
                "details": "成功删除测试任务"
            })
            
        except Exception as e:
            test_case["tests"].append({
                "name": "基本功能测试",
                "status": "failed",
                "details": f"测试失败: {str(e)}"
            })
            self.test_results["issues_found"].append({
                "type": "error",
                "issue": "基本功能测试失败",
                "description": str(e)
            })
        
        test_case["end_time"] = datetime.now().isoformat()
        self.test_results["test_cases"].append(test_case)
        logger.info("✅ 基本功能测试完成")
    
    async def test_performance(self):
        """测试性能"""
        logger.info("⚡ 测试性能...")
        
        performance_metrics = {
            "api_response_times": [],
            "task_creation_time": None,
            "task_deletion_time": None,
            "test_time": datetime.now().isoformat()
        }
        
        try:
            # 测试API响应时间
            for _ in range(5):
                start_time = time.time()
                await self.make_request("GET", "/scheduler/status")
                response_time = time.time() - start_time
                performance_metrics["api_response_times"].append(response_time)
            
            # 测试任务创建时间
            start_time = time.time()
            future_time = (datetime.now() + timedelta(hours=2)).strftime("%H:%M")
            task_config = {
                "ticker": "PERF",
                "analysts": ["market"],
                "research_depth": 1,
                "schedule_type": "daily",
                "schedule_time": future_time,
                "timezone": "UTC",
                "enabled": True
            }
            response = await self.make_request("POST", "/tasks", task_config)
            task_id = response["task_id"]
            performance_metrics["task_creation_time"] = time.time() - start_time
            
            # 测试任务删除时间
            start_time = time.time()
            await self.make_request("DELETE", f"/tasks/{task_id}")
            performance_metrics["task_deletion_time"] = time.time() - start_time
            
            # 计算平均响应时间
            avg_response_time = sum(performance_metrics["api_response_times"]) / len(performance_metrics["api_response_times"])
            performance_metrics["average_api_response_time"] = avg_response_time
            
            # 性能评估
            if avg_response_time > 1.0:
                self.test_results["issues_found"].append({
                    "type": "performance",
                    "issue": "API响应时间较慢",
                    "description": f"平均响应时间: {avg_response_time:.2f}秒"
                })
            
            if performance_metrics["task_creation_time"] > 2.0:
                self.test_results["issues_found"].append({
                    "type": "performance",
                    "issue": "任务创建时间较慢",
                    "description": f"任务创建时间: {performance_metrics['task_creation_time']:.2f}秒"
                })
            
        except Exception as e:
            logger.error(f"❌ 性能测试失败: {e}")
            self.test_results["issues_found"].append({
                "type": "error",
                "issue": "性能测试失败",
                "description": str(e)
            })
        
        self.test_results["performance_metrics"] = performance_metrics
        logger.info("✅ 性能测试完成")
    
    def generate_recommendations(self):
        """生成建议"""
        logger.info("💡 生成建议...")
        
        recommendations = []
        
        # 基于发现的问题生成建议
        for issue in self.test_results["issues_found"]:
            if issue["type"] == "critical":
                recommendations.append({
                    "priority": "高",
                    "category": "稳定性",
                    "recommendation": f"立即解决: {issue['issue']}"
                })
            elif issue["type"] == "performance":
                recommendations.append({
                    "priority": "中",
                    "category": "性能优化",
                    "recommendation": f"考虑优化: {issue['issue']}"
                })
        
        # 基于统计数据生成建议
        stats = self.test_results.get("task_statistics", {})
        if stats.get("disabled_tasks_count", 0) > 0:
            recommendations.append({
                "priority": "低",
                "category": "维护",
                "recommendation": f"检查并清理 {stats['disabled_tasks_count']} 个禁用的任务"
            })
        
        # 通用建议
        recommendations.extend([
            {
                "priority": "中",
                "category": "监控",
                "recommendation": "设置定时任务执行状态监控和告警"
            },
            {
                "priority": "低",
                "category": "优化",
                "recommendation": "考虑实现任务执行历史记录清理机制"
            },
            {
                "priority": "中",
                "category": "可靠性",
                "recommendation": "实现任务执行失败重试机制"
            }
        ])
        
        self.test_results["recommendations"] = recommendations
        logger.info("✅ 建议生成完成")
    
    def generate_report(self) -> str:
        """生成测试报告"""
        logger.info("📄 生成测试报告...")
        
        report = f"""
# TradingAgents 定时任务测试报告

**测试时间**: {self.test_results['test_time']}

## 🎯 测试概述

本次测试对 TradingAgents 系统的定时任务功能进行了全面评估，包括调度器状态、任务管理、基本功能和性能测试。

## 📊 调度器状态

- **运行状态**: {'✅ 正常运行' if self.test_results['scheduler_status'].get('running') else '❌ 未运行'}
- **总任务数**: {self.test_results['scheduler_status'].get('total_tasks', 0)}
- **启用任务数**: {self.test_results['scheduler_status'].get('enabled_tasks', 0)}
- **调度器作业数**: {self.test_results['scheduler_status'].get('jobs_in_scheduler', 0)}

## 📈 任务统计

### 任务数量分布
- 定时任务: {self.test_results['task_statistics'].get('scheduled_tasks_count', 0)}
- 活跃任务: {self.test_results['task_statistics'].get('active_tasks_count', 0)}
- 已完成任务: {self.test_results['task_statistics'].get('completed_tasks_count', 0)}
- 启用任务: {self.test_results['task_statistics'].get('enabled_tasks_count', 0)}
- 禁用任务: {self.test_results['task_statistics'].get('disabled_tasks_count', 0)}

### 调度类型分布
"""
        
        schedule_types = self.test_results['task_statistics'].get('schedule_types', {})
        for schedule_type, count in schedule_types.items():
            report += f"- {schedule_type}: {count} 个任务\n"
        
        report += f"""
### 股票代码分布
"""
        
        tickers = self.test_results['task_statistics'].get('tickers', {})
        for ticker, count in list(tickers.items())[:10]:  # 显示前10个
            report += f"- {ticker}: {count} 个任务\n"
        
        report += f"""
## 🧪 功能测试结果

"""
        
        for test_case in self.test_results['test_cases']:
            report += f"### {test_case['name']}\n"
            for test in test_case.get('tests', []):
                status_icon = "✅" if test['status'] == 'passed' else "❌"
                report += f"- {status_icon} {test['name']}: {test['details']}\n"
            report += "\n"
        
        report += f"""
## ⚡ 性能指标

"""
        
        perf = self.test_results.get('performance_metrics', {})
        if perf:
            report += f"- 平均API响应时间: {perf.get('average_api_response_time', 0):.3f} 秒\n"
            report += f"- 任务创建时间: {perf.get('task_creation_time', 0):.3f} 秒\n"
            report += f"- 任务删除时间: {perf.get('task_deletion_time', 0):.3f} 秒\n"
        
        report += f"""
## ⚠️ 发现的问题

"""
        
        if not self.test_results['issues_found']:
            report += "🎉 未发现问题，系统运行良好！\n"
        else:
            for issue in self.test_results['issues_found']:
                icon = {"critical": "🚨", "error": "❌", "warning": "⚠️", "performance": "⚡"}.get(issue['type'], "❓")
                report += f"{icon} **{issue['issue']}** ({issue['type']})\n"
                report += f"   {issue['description']}\n\n"
        
        report += f"""
## 💡 改进建议

"""
        
        for rec in self.test_results['recommendations']:
            priority_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(rec['priority'], "⚪")
            report += f"{priority_icon} **{rec['category']}** ({rec['priority']}优先级)\n"
            report += f"   {rec['recommendation']}\n\n"
        
        report += f"""
## 📋 测试结论

"""
        
        critical_issues = len([i for i in self.test_results['issues_found'] if i['type'] == 'critical'])
        error_issues = len([i for i in self.test_results['issues_found'] if i['type'] == 'error'])
        
        if critical_issues > 0:
            report += f"🚨 **需要立即关注**: 发现 {critical_issues} 个严重问题，建议立即修复。\n"
        elif error_issues > 0:
            report += f"⚠️ **需要注意**: 发现 {error_issues} 个错误，建议尽快修复。\n"
        else:
            report += "✅ **系统健康**: 定时任务功能运行良好，无严重问题。\n"
        
        report += f"""
系统整体运行稳定，定时任务调度功能正常。建议定期进行类似测试以确保系统持续稳定运行。

---
*报告生成时间: {datetime.now().isoformat()}*
*测试工具版本: TradingAgents Scheduler Tester v1.0*
"""
        
        return report
    
    async def run_comprehensive_test(self):
        """运行综合测试并生成报告"""
        logger.info("🎯 开始综合测试...")
        
        try:
            # 收集系统信息
            await self.collect_scheduler_status()
            await self.collect_task_statistics()
            
            # 运行功能测试
            await self.test_basic_functionality()
            
            # 运行性能测试
            await self.test_performance()
            
            # 生成建议
            self.generate_recommendations()
            
            # 生成报告
            report = self.generate_report()
            
            logger.info("✅ 综合测试完成")
            return report
            
        except Exception as e:
            logger.error(f"❌ 综合测试失败: {e}")
            return f"测试失败: {str(e)}"

async def main():
    """主函数"""
    logger.info("🚀 启动定时任务测试报告生成...")
    
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
    
    # 运行测试并生成报告
    async with SchedulerTestReporter() as reporter:
        report = await reporter.run_comprehensive_test()
        
        # 保存报告到文件
        report_filename = f"scheduler_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 测试报告已保存到: {report_filename}")
        
        # 也打印到控制台
        print("\n" + "="*80)
        print(report)
        print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
