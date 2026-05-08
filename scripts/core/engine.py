"""
核心层：重构后的多租户多任务驱动引擎
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING, Dict, Optional

from scripts.core.interfaces import IFetcher, IProcessor, IPusher
from scripts.core.models import RunContext, UserSubscription, TaskConfig
from scripts.core.state_manager import StateManager
from scripts.settings import DATA_DIR, CONFIG_DIR

if TYPE_CHECKING:
    from scripts.processors.semantic_clustering import SemanticClusteringFilter
    from scripts.processors.weekly_digest_engine import WeeklyDigestEngine

LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

file_handler = RotatingFileHandler(
    LOG_DIR / "pipeline.log", maxBytes=5 * 1024 * 1024, backupCount=7, encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), file_handler]
)
logger = logging.getLogger("PipelineEngine")

class PipelineEngine:
    def __init__(
        self,
        fetchers: Dict[str, IFetcher],
        processor: IProcessor,
        pusher: IPusher,
        clustering_filter: Optional[SemanticClusteringFilter] = None,
        weekly_digest: Optional[WeeklyDigestEngine] = None,
    ):
        self.fetchers = fetchers
        self.processor = processor
        self.pusher = pusher

        if clustering_filter is None:
            from scripts.processors.semantic_clustering import SemanticClusteringFilter
            clustering_filter = SemanticClusteringFilter()
        self.clustering_filter = clustering_filter
        self.weekly_digest = weekly_digest

        state_dir = DATA_DIR / "state"
        self.state_manager = StateManager(str(state_dir))

    def _create_task_workspace(self, user: UserSubscription, task: TaskConfig) -> RunContext:
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_task_name = "".join(x for x in task.task_name if x.isalnum() or x in "._- ")

        # 使用 / 符号进行路径拼接
        base_dir = DATA_DIR / date_str / user.wechat_id / safe_task_name
        papers_dir = base_dir / "papers"

        # 预建子目录
        for sub in ["01_raw", "02_standardized", "03_processed", "04_rendered", "papers"]:
            (base_dir / sub).mkdir(parents=True, exist_ok=True)

        return RunContext(
            date_str=date_str,
            workspace_dir=str(base_dir),
            papers_dir=str(papers_dir),
            current_user=user,
            current_task=task
        )

    def run(self):
        logger.info("=== 🚀 星枢重构版引擎启动 ===")
        # 直接使用全局 CONFIG_DIR
        config_path = CONFIG_DIR / "subscriptions.json"

        if not config_path.exists():
            logger.error(f"配置文件缺失: {config_path}")
            return

        # pathlib 的对象可以直接作为 open 的参数
        with open(config_path, "r", encoding="utf-8") as f:
            users_data = json.load(f)

        for u_data in users_data:
            user = UserSubscription(**u_data)
            logger.info(f"\n👤 开始处理用户: {user.user_name}")

            for task in user.tasks:
                logger.info(f"  [频道] {task.task_name} ({task.task_type})")

                fetcher = self.fetchers.get(task.task_type)
                if not fetcher:
                    logger.warning(f"  ⚠️ 未找到类型为 {task.task_type} 的抓取器，跳过任务。")
                    continue

                context = self._create_task_workspace(user, task)
                context.progress_cursor = self.state_manager.get_progress(
                    user.wechat_id, task.task_type
                )
                context.reading_mode = getattr(task, 'reading_mode', 'skim')

                try:
                    logger.info(f"  [状态] 当前进度游标: {context.progress_cursor}")

                    data = fetcher.fetch(context)
                    data = self.clustering_filter.process(data)
                    report = self.processor.process(data, context)
                    success = self.pusher.push(report, context)

                    if success:
                        step = 10 if task.task_type == "vocabulary" else 1
                        self.state_manager.advance_progress(
                            user.wechat_id, step=step, task_type=task.task_type
                        )
                        logger.info(f"  ✅ 任务完成")

                except Exception as e:
                    logger.error(f"  ❌ 任务流水线崩溃: {e}")

        # 所有用户任务完成后，生成周报
        if self.weekly_digest:
            processed_users = {u_data.get("wechat_id") for u_data in users_data if u_data.get("wechat_id")}
            for uid in processed_users:
                try:
                    digest = self.weekly_digest.generate(uid)
                    if digest:
                        logger.info(f"[周报] {uid}: {digest.summary_text}")
                except Exception as e:
                    logger.warning(f"[周报] {uid} 生成失败: {e}")