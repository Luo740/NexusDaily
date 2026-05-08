"""
LiteratureFetcher：多平台论文聚合协调器
根据用户配置并行抓取多个论文平台，去重后返回统一 DailyData
"""
import logging
from typing import List

from scripts.core import IFetcher, DailyData, PaperDocument, RunContext, FetchError
from scripts.fetchers.papers import get_platform_fetcher

logger = logging.getLogger(__name__)

TITLE_SIMILARITY_THRESHOLD = 0.8  # 跨平台去重阈值


class LiteratureFetcher(IFetcher):
    """多平台论文聚合抓取器"""

    def fetch(self, context: RunContext) -> DailyData:
        task = context.current_task
        platforms = task.paper_sources if hasattr(task, 'paper_sources') and task.paper_sources else ["arxiv"]
        max_papers = task.max_papers if hasattr(task, 'max_papers') and task.max_papers else 5
        deep_mode = context.reading_mode == "deep"

        logger.info(f"    论文平台: {platforms}, 模式: {'精读' if deep_mode else '粗读'}, 上限: {max_papers}")

        all_papers: List[PaperDocument] = []
        for platform_name in platforms:
            fetcher = get_platform_fetcher(platform_name)
            if fetcher is None:
                logger.warning(f"    未知论文平台: {platform_name}，跳过")
                continue

            try:
                if platform_name == "arxiv" and deep_mode:
                    # arXiv 需要 papers_dir 来下载 PDF
                    papers = fetcher.search(
                        task.keywords, max_results=max_papers,
                        deep_mode=deep_mode
                    )
                    # arxiv_fetcher's search doesn't accept papers_dir directly,
                    # but the _fetch method does. We patch it post-hoc.
                    # For now, PDF download happens inside arxiv_fetcher._download_and_extract
                    # which needs papers_dir. Let's pass it through...
                else:
                    papers = fetcher.search(task.keywords, max_results=max_papers,
                                           deep_mode=deep_mode)
                if papers:
                    logger.info(f"      [{platform_name}] 返回 {len(papers)} 篇")
                    all_papers.extend(papers)
            except Exception as e:
                logger.error(f"      [{platform_name}] 抓取异常: {e}")

        # 跨平台去重
        all_papers = _deduplicate(all_papers)
        # 截取 max_papers
        all_papers = all_papers[:max_papers]

        if not all_papers:
            raise FetchError(f"论文频道 '{task.task_name}' 所有平台抓取失败。")

        # 精读模式：为 arxiv 平台下载 PDF 并提取全文
        if deep_mode:
            _fetch_full_text(all_papers, context.papers_dir)

        data = DailyData(papers=all_papers)
        logger.info(f"    聚合后共 {len(all_papers)} 篇论文（去重）")
        return data


def _fetch_full_text(papers: List[PaperDocument], papers_dir: str):
    """为支持 PDF 下载的论文提取全文"""
    from scripts.fetchers.papers.arxiv_fetcher import ArxivFetcher
    arxiv = ArxivFetcher()
    for paper in papers:
        if paper.full_text:
            continue  # 已有全文
        if paper.source_platform == "arxiv" and paper.pdf_url:
            arxiv._download_and_extract(paper, papers_dir)
        elif paper.pdf_url:
            # 尝试下载其他平台的 PDF
            import requests
            from scripts.processors.pdf_extractor import PDFExtractor
            import os
            try:
                resp = requests.get(paper.pdf_url, timeout=30,
                                    headers={'User-Agent': 'NexusDaily/1.0'})
                resp.raise_for_status()
                safe = "".join(c for c in paper.title[:50] if c.isalnum() or c == ' ').rstrip()
                local = os.path.join(papers_dir, f"{safe}.pdf")
                with open(local, 'wb') as f:
                    f.write(resp.content)
                paper.pdf_local_path = local
                paper.full_text = PDFExtractor.extract(local)
            except Exception as e:
                logger.warning(f"    PDF 下载失败 [{paper.source_platform}]: {e}")


def _jaccard_similarity(text_a: str, text_b: str) -> float:
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def _deduplicate(papers: List[PaperDocument]) -> List[PaperDocument]:
    kept = []
    for p in papers:
        if not any(_jaccard_similarity(p.title, k.title) > TITLE_SIMILARITY_THRESHOLD
                   for k in kept):
            kept.append(p)
    if len(kept) < len(papers):
        logger.info(f"    跨平台去重: {len(papers)} → {len(kept)}")
    return kept
