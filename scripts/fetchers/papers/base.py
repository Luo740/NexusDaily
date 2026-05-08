"""
论文平台抓取器基类
"""
from abc import ABC, abstractmethod
from typing import List
from scripts.core.models import PaperDocument


class BasePlatformFetcher(ABC):
    PLATFORM_NAME: str = "unknown"

    @abstractmethod
    def search(self, keywords: List[str], max_results: int,
               deep_mode: bool = False) -> List[PaperDocument]:
        """
        搜索论文
        Args:
            keywords: 搜索关键词列表
            max_results: 最大返回数量
            deep_mode: True=下载PDF并提取全文，False=仅获取摘要
        """
        ...
