"""
CORE 论文抓取器
API: https://api.core.ac.uk/api-v2
需要 CORE_API_KEY 环境变量
"""
import os
import logging
import requests
from typing import List

from scripts.core.models import PaperDocument
from scripts.fetchers.papers.base import BasePlatformFetcher

logger = logging.getLogger(__name__)

CORE_API = "https://api.core.ac.uk/api-v2"


class COREFetcher(BasePlatformFetcher):
    PLATFORM_NAME = "core"

    def __init__(self):
        self.api_key = os.getenv("CORE_API_KEY", "")
        if not self.api_key:
            logger.warning("CORE_API_KEY 未配置，CORE 平台将不可用")

    def search(self, keywords: List[str], max_results: int = 5,
               deep_mode: bool = False) -> List[PaperDocument]:
        if not self.api_key:
            return []
        papers = []
        for kw in keywords:
            try:
                papers.extend(self._search_one(kw, max_results, deep_mode))
            except Exception as e:
                logger.error(f"CORE '{kw}' 抓取失败: {e}")
        return papers

    def _search_one(self, query: str, limit: int, deep_mode: bool) -> List[PaperDocument]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"q": query, "limit": min(limit, 10)}
        resp = requests.get(f"{CORE_API}/articles/search", params=params,
                            headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data.get("results", []):
            title = item.get("title", "")
            abstract = item.get("abstract") or item.get("description") or ""
            authors = [a.get("name", "") for a in item.get("authors", [])]

            pdf_url = item.get("downloadUrl") or item.get("sourceUrl") or ""

            paper = PaperDocument(
                title=title, abstract=abstract, authors=authors,
                pdf_url=pdf_url if pdf_url else None,
                source_platform=self.PLATFORM_NAME
            )

            if deep_mode and pdf_url:
                self._download_and_extract(paper)

            papers.append(paper)
        return papers

    def _download_and_extract(self, paper: PaperDocument):
        from scripts.processors.pdf_extractor import PDFExtractor
        import tempfile
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.get(paper.pdf_url, headers=headers, timeout=30)
            resp.raise_for_status()

            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(resp.content)
                paper.full_text = PDFExtractor.extract(tmp.name)
                paper.pdf_local_path = tmp.name
            logger.info(f"    CORE 全文提取: {len(paper.full_text)} 字符")
        except Exception as e:
            logger.warning(f"    CORE PDF 下载/提取失败: {e}")
