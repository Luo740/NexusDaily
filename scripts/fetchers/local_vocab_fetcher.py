"""
获取层模块：本地词库抓取器（顺序推进）
"""
import logging
from scripts.core import IFetcher, DailyData, Article, RunContext
from scripts.settings import ASSETS_DIR

logger = logging.getLogger(__name__)


class LocalVocabFetcher(IFetcher):
    DAILY_WORD_COUNT = 5

    def fetch(self, context: RunContext) -> DailyData:
        data = DailyData()

        shuffled_path = ASSETS_DIR / "vocabulary_shuffled.txt"
        if not shuffled_path.exists():
            logger.warning(f"打乱词书缺失: {shuffled_path}")
            return data

        with open(shuffled_path, "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip()]

        if not words:
            return data

        cursor = context.progress_cursor
        daily_words = words[cursor : cursor + self.DAILY_WORD_COUNT]

        if not daily_words:
            # 一轮学完，从头开始
            cursor = 0
            context.progress_cursor = 0
            daily_words = words[cursor : cursor + self.DAILY_WORD_COUNT]
            logger.info("    🎉 词书一轮完成，重新开始")

        content = "\n".join(daily_words)
        data.articles.append(Article(
            title=f"今日单词池 ({context.date_str})",
            content=content,
            source="local_assets"
        ))
        logger.info(
            f"    📖 词书游标 {cursor}→{cursor + len(daily_words)}，"
            f"已学 {cursor + len(daily_words)}/{len(words)}"
        )
        return data
