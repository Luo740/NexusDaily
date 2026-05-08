"""
处理层模块：周期性记忆回溯引擎
负责聚合一周内的 DailyData 生成周报摘要。
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from scripts.settings import DATA_DIR

logger = logging.getLogger(__name__)


@dataclass
class WeeklyDigest:
    week_label: str
    article_count: int
    paper_count: int
    top_titles: List[str] = field(default_factory=list)
    summary_text: str = ""


class WeeklyDigestEngine:

    def generate(self, user_id: str, week_num: int | None = None) -> WeeklyDigest | None:
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        if week_num:
            monday = today - timedelta(weeks=week_num)

        articles = []
        papers = []

        for i in range(7):
            day = monday + timedelta(days=i)
            date_str = day.strftime("%Y-%m-%d")
            day_dir = Path(DATA_DIR) / date_str

            if not day_dir.exists():
                continue

            for user_dir in day_dir.glob("*"):
                if user_dir.name != user_id:
                    continue
                for task_dir in user_dir.iterdir():
                    if not task_dir.is_dir():
                        continue
                    report_path = task_dir / "03_processed" / "report.md"
                    if report_path.exists():
                        with open(report_path, "r", encoding="utf-8") as f:
                            articles.append(f.read()[:500])

        if not articles:
            logger.info(f"用户 {user_id} 本周无日报数据，跳过周报生成")
            return None

        week_label = f"{monday.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')}"
        digest = WeeklyDigest(
            week_label=week_label,
            article_count=len(articles),
            paper_count=len(papers),
            top_titles=[],
            summary_text=f"本周共推送 {len(articles)} 条日报。"
        )
        logger.info(f"[周报] {user_id} 的 {week_label} 周报已生成：{digest.article_count} 篇日报")
        return digest
