"""
Semantic Scholar 论文抓取器
API: https://api.semanticscholar.org/graph/v1
"""
import os
import logging
import requests
from typing import List

from scripts.core.models import PaperDocument
from scripts.fetchers.papers.base import BasePlatformFetcher

logger = logging.getLogger(__name__)

S2_API = "https://api.semanticscholar.org/graph/v1"


class SemanticScholarFetcher(BasePlatformFetcher):
    PLATFORM_NAME = "semantic_scholar"

    def __init__(self):
        self.api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["x-api-key"] = self.api_key

    def search(self, keywords: List[str], max_results: int = 5,
               deep_mode: bool = False) -> List[PaperDocument]:
        papers = []
        for kw in keywords:
            try:
                papers.extend(self._search_one(kw, max_results))
            except Exception as e:
                logger.error(f"Semantic Scholar '{kw}' 抓取失败: {e}")
        return papers

    def _search_one(self, query: str, limit: int) -> List[PaperDocument]:
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,abstract,authors,externalIds,url,year,publicationVenue"
        }
        resp = requests.get(f"{S2_API}/paper/search", params=params,
                            headers=self.headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data.get("data", []):
            title = item.get("title", "")
            abstract = item.get("abstract") or ""
            authors = [a.get("name", "") for a in item.get("authors", [])]

            pdf_url = None
            ext_ids = item.get("externalIds", {})
            arxiv_id = ext_ids.get("ArXiv")
            if arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            else:
                url = item.get("url", "")
                if url:
                    pdf_url = url

            papers.append(PaperDocument(
                title=title, abstract=abstract, authors=authors,
                pdf_url=pdf_url, source_platform=self.PLATFORM_NAME
            ))
        return papers
