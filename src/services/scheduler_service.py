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
        try:
            self.scheduler.remove_all_jobs()
            print(f"  -> 已移除所有现有定时任务")

            enabled_tasks = [task for task in tasks if task.enabled and task.cron]
            print(f"  -> 共发现 {len(enabled_tasks)} 个已启用的定时任务")

            for i, task in enumerate(enabled_tasks, 1):
                print(f"  -> 处理任务 {i}/{len(enabled_tasks)}: '{task.task_name}'")
                try:
                    if not task.cron or not task.cron.strip():
                        print(f"     [警告] 任务 '{task.task_name}' 的 Cron 表达式为空，跳过")
                        continue
                    
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
                        print(f"     [调试] 解析为6字段Cron表达式: 秒={second}, 分={minute}, 时={hour}, 日={day}, 月={month}, 周={day_of_week}")
                    else:
                        # 标准5字段格式：分 时 日 月 周
                        trigger = CronTrigger.from_crontab(task.cron)
                        print(f"     [调试] 解析为5字段Cron表达式: {task.cron}")
                        
                    self.scheduler.add_job(
                        self._run_task,
                        trigger=trigger,
                        args=[task.id, task.task_name],
                        id=f"task_{task.id}",
                        name=f"Scheduled: {task.task_name}",
                        replace_existing=True,
                        # 添加任务执行超时保护
                        max_instances=1,
                        misfire_grace_time=30  # 任务错过执行的宽限期延长到5分钟
                    )
                    print(f"     ✓ 已为任务 '{task.task_name}' 添加定时规则: '{task.cron}'")
                except ValueError as e:
                    print(f"     ✗ [警告] 任务 '{task.task_name}' 的 Cron 表达式无效: {e}")
                except Exception as e:
                    print(f"     ✗ [错误] 添加任务 '{task.task_name}' 失败: {str(e)}")
                    import traceback
                    traceback.print_exc()

            # 验证已添加的任务数量
            jobs = self.scheduler.get_jobs()
            print(f"  -> 成功加载 {len(jobs)} 个定时任务")
            for job in jobs:
                print(f"     - {job.name} (ID: {job.id}, 下次执行: {job.next_run_time})")
        except Exception as e:
            print(f"[错误] 重新加载定时任务失败: {str(e)}")
            import traceback
            traceback.print_exc()

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
        
        # 安全地构建作业信息，避免AttributeError
        job_info_parts = []
        if hasattr(event, 'job_id'):
            job_info_parts.append(f"作业ID: {event.job_id}")
        if hasattr(event, 'job_name'):
            job_info_parts.append(f"作业名称: {event.job_name}")
        if hasattr(event, 'job') and event.job:
            job_info_parts.append(f"作业对象: {event.job}")
        job_info = f" ({', '.join(job_info_parts)})" if job_info_parts else ""
        
        print(f"[调度器事件] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {event_name}{job_info}")

    async def _run_task(self, task_id: int, task_name: str):
        """执行定时任务"""
        print(f"[任务执行] 定时任务触发: 正在为任务 '{task_name}' (ID: {task_id}) 启动爬虫...")
        try:
            # 检查进程服务状态，确保可以执行任务
            if not self.process_service:
                print(f"[任务执行] 警告: process_service 未初始化，无法执行任务 '{task_name}'")
                return
            
            await self.process_service.start_task(task_id, task_name)
            print(f"[任务执行] 任务 '{task_name}' (ID: {task_id}) 执行完成")
        except Exception as e:
            print(f"[任务执行] 错误: 任务 '{task_name}' (ID: {task_id}) 执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 简单的重试机制，只重试一次
            try:
                print(f"[任务执行] 尝试重试任务 '{task_name}' (ID: {task_id})...")
                await self.process_service.start_task(task_id, task_name)
                print(f"[任务执行] 任务 '{task_name}' (ID: {task_id}) 重试成功")
            except Exception as retry_e:
                print(f"[任务执行] 重试失败: 任务 '{task_name}' (ID: {task_id}) 再次失败: {str(retry_e)}")
