"""
论文平台抓取器包：统一注册表和导出
"""
from scripts.fetchers.papers.base import BasePlatformFetcher
from scripts.fetchers.papers.arxiv_fetcher import ArxivFetcher
from scripts.fetchers.papers.semantic_scholar import SemanticScholarFetcher
from scripts.fetchers.papers.pubmed_fetcher import PubMedFetcher
from scripts.fetchers.papers.openalex_fetcher import OpenAlexFetcher
from scripts.fetchers.papers.core_fetcher import COREFetcher
from scripts.fetchers.papers.europe_pmc_fetcher import EuropePMCFetcher

# 平台名 → 抓取器类的映射
PLATFORM_REGISTRY = {
    "arxiv": ArxivFetcher,
    "semantic_scholar": SemanticScholarFetcher,
    "pubmed": PubMedFetcher,
    "openalex": OpenAlexFetcher,
    "core": COREFetcher,
    "europe_pmc": EuropePMCFetcher,
}


def get_platform_fetcher(name: str) -> BasePlatformFetcher | None:
    """根据平台名获取抓取器实例（懒初始化，每个类只创建一次）"""
    cls = PLATFORM_REGISTRY.get(name)
    if cls is None:
        return None
    return cls()
