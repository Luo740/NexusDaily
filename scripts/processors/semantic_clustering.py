"""
处理层模块：语义聚类去重 (过滤器模式)
基于标题 Jaccard 相似度进行多源信息去重。
"""
import logging
from scripts.core.models import DailyData

logger = logging.getLogger(__name__)


class SemanticClusteringFilter:
    SIMILARITY_THRESHOLD = 0.7

    def process(self, data: DailyData) -> DailyData:
        if not data.articles:
            return data

        original_count = len(data.articles)
        data.articles = self._dedup(data.articles)
        removed = original_count - len(data.articles)
        if removed:
            logger.info(f"    [去重] 移除 {removed} 篇重复/相似文章，保留 {len(data.articles)} 篇")
        return data

    @staticmethod
    def _jaccard(title_a: str, title_b: str) -> float:
        set_a = set(title_a.lower().split())
        set_b = set(title_b.lower().split())
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    def _dedup(self, articles):
        kept = []
        for article in articles:
            if not any(
                self._jaccard(article.title, k.title) > self.SIMILARITY_THRESHOLD
                for k in kept
            ):
                kept.append(article)
        return kept
