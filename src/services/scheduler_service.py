"""
调度服务
负责管理定时任务的调度
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import List
from src.domain.models.task import Task
from src.services.process_service import ProcessService


class SchedulerService:
    """调度服务"""

    def __init__(self, process_service: ProcessService):
        import os
        import time
        print(f"[调度器初始化] RUNNING_IN_DOCKER: {os.getenv('RUNNING_IN_DOCKER')}")
        print(f"[调度器初始化] TZ环境变量: {os.getenv('TZ')}")
        print(f"[调度器初始化] 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        print(f"[调度器初始化] 创建调度器，时区: Asia/Shanghai")
        self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        self.process_service = process_service
        # 配置日志记录器，捕获所有调度器事件
        self.scheduler.add_listener(self._scheduler_listener)
        self.scheduler.configure(job_defaults={'misfire_grace_time': 30})

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            print("调度器已启动")

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("调度器已停止")

    async def reload_jobs(self, tasks: List[Task]):
        """重新加载所有定时任务"""
        print("正在重新加载定时任务...")
        self.scheduler.remove_all_jobs()

        for task in tasks:
            if task.enabled and task.cron:
                try:
                    # 解析cron表达式，支持6字段格式（秒 分 时 日 月 周）
                    cron_parts = task.cron.strip().split()
                    if len(cron_parts) == 6:
                        # 6字段格式：秒 分 时 日 月 周
                        second, minute, hour, day, month, day_of_week = cron_parts
                        trigger = CronTrigger(
                            second=second,
                            minute=minute,
                            hour=hour,
                            day=day,
                            month=month,
                            day_of_week=day_of_week,
                            timezone="Asia/Shanghai"
                        )
                    else:
                        # 标准5字段格式：分 时 日 月 周
                        trigger = CronTrigger.from_crontab(task.cron)
                        
                    self.scheduler.add_job(
                        self._run_task,
                        trigger=trigger,
                        args=[task.id, task.task_name],
                        id=f"task_{task.id}",
                        name=f"Scheduled: {task.task_name}",
                        replace_existing=True
                    )
                    print(f"  -> 已为任务 '{task.task_name}' 添加定时规则: '{task.cron}'")
                except ValueError as e:
                    print(f"  -> [警告] 任务 '{task.task_name}' 的 Cron 表达式无效: {e}")

        print("定时任务加载完成")

    def _scheduler_listener(self, event):
        """调度器事件监听器"""
        import datetime
        event_type = event.code
        event_map = {
            1: "调度器启动",
            2: "调度器停止",
            3: "作业添加",
            4: "作业移除",
            5: "作业修改",
            6: "作业执行",
            7: "作业执行成功",
            8: "作业执行失败",
            9: "作业执行错过",
            10: "作业执行暂停",
            11: "作业执行恢复"
        }
        event_name = event_map.get(event_type, f"未知事件 ({event_type})")
        job_info = f" 作业ID: {event.job_id}, 作业名称: {event.job_name}" if hasattr(event, 'job_id') else ""
        print(f"[调度器事件] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {event_name}{job_info}")

    async def _run_task(self, task_id: int, task_name: str):
        """执行定时任务"""
        print(f"[任务执行] 定时任务触发: 正在为任务 '{task_name}' (ID: {task_id}) 启动爬虫...")
        await self.process_service.start_task(task_id, task_name)
