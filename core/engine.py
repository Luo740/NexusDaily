"""
核心层：重构后的多租户多任务驱动引擎
集成状态管理与多态抓取路由
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict
from dataclasses import asdict

from core.interfaces import IFetcher, IProcessor, IPusher
from core.models import RunContext, UserSubscription, TaskConfig
from core.state_manager import StateManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PipelineEngine")

class PipelineEngine:
    def __init__(self, fetchers: Dict[str, IFetcher], processor: IProcessor, pusher: IPusher):
        """
        :param fetchers: 抓取器映射表，Key 为 task_type (如 'literature', 'vocabulary')
        """
        self.fetchers = fetchers
        self.processor = processor
        self.pusher = pusher

        # 集成状态管理器，路径固定在项目根目录的 data/state
        state_dir = os.path.join(os.getcwd(), "data", "state")
        self.state_manager = StateManager(state_dir)

    def _create_task_workspace(self, user: UserSubscription, task: TaskConfig) -> RunContext:
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_task_name = "".join(x for x in task.task_name if x.isalnum() or x in "._- ")

        base_dir = os.path.join(os.getcwd(), "data", date_str, user.wechat_id, safe_task_name)
        papers_dir = os.path.join(base_dir, "papers")

        # 自动创建五级生命周期目录
        for sub in ["01_raw", "02_standardized", "03_processed", "04_rendered", "papers"]:
            os.makedirs(os.path.join(base_dir, sub), exist_ok=True)

        return RunContext(
            date_str=date_str,
            workspace_dir=base_dir,
            papers_dir=papers_dir,
            current_user=user,
            current_task=task
        )

    def run(self):
        logger.info("=== 🚀 星枢重构版引擎启动 ===")
        config_path = os.path.join(os.getcwd(), "config", "subscriptions.json")

        if not os.path.exists(config_path):
            logger.error(f"配置文件缺失: {config_path}")
            return

        with open(config_path, "r", encoding="utf-8") as f:
            users_data = json.load(f)

        for u_data in users_data:
            user = UserSubscription(**u_data)
            logger.info(f"\n👤 开始处理用户: {user.user_name}")

            for task in user.tasks:
                logger.info(f"  [频道] {task.task_name} ({task.task_type})")

                # 枢纽 1：多态抓取器路由
                fetcher = self.fetchers.get(task.task_type)
                if not fetcher:
                    logger.warning(f"  ⚠️ 未找到类型为 {task.task_type} 的抓取器，跳过任务。")
                    continue

                context = self._create_task_workspace(user, task)

                try:
                    # 枢纽 2：集成进度获取 (为后续词库抓取做准备)
                    current_progress = self.state_manager.get_progress(user.wechat_id, task.task_type)
                    logger.info(f"  [状态] 当前进度游标: {current_progress}")

                    # 1. Fetch
                    data = fetcher.fetch(context)

                    # 2. Process
                    report = self.processor.process(data, context)

                    # 3. Push
                    success = self.pusher.push(report, context)

                    if success:
                        logger.info(f"  ✅ 任务完成")
                        # 枢纽 3：后续可在此根据业务逻辑调用 advance_progress

                except Exception as e:
                    logger.error(f"  ❌ 任务流水线崩溃: {e}")