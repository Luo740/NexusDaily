"""
OpenAlex 论文抓取器
API: https://api.openalex.org
"""
import logging
import requests
from typing import List

from scripts.core.models import PaperDocument
from scripts.fetchers.papers.base import BasePlatformFetcher

logger = logging.getLogger(__name__)

OPENALEX_API = "https://api.openalex.org"


class OpenAlexFetcher(BasePlatformFetcher):
    PLATFORM_NAME = "openalex"

    def __init__(self):
        self.email = "research@example.com"

    def search(self, keywords: List[str], max_results: int = 5,
               deep_mode: bool = False) -> List[PaperDocument]:
        papers = []
        for kw in keywords:
            try:
                papers.extend(self._search_one(kw, max_results))
            except Exception as e:
                logger.error(f"OpenAlex '{kw}' 抓取失败: {e}")
        return papers

    def _search_one(self, query: str, limit: int) -> List[PaperDocument]:
        params = {
            "search": query,
            "per_page": limit,
            "sort": "publication_date:desc",
            "mailto": self.email,
        }
        resp = requests.get(f"{OPENALEX_API}/works", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data.get("results", []):
            title = item.get("title", "")
            abstract = ""
            # OpenAlex 摘要可能在 abstract_inverted_index 中
            inv_idx = item.get("abstract_inverted_index")
            if inv_idx:
                abstract = _decode_inverted_index(inv_idx)

            authors = []
            for au in item.get("authorships", []):
                name = au.get("author", {}).get("display_name", "")
                if name:
                    authors.append(name)

            pdf_url = item.get("primary_location", {}).get("landing_page_url") or ""
            oa_url = item.get("open_access", {}).get("oa_url") or ""
            if oa_url:
                pdf_url = oa_url

            oa_id = item.get("id", "")
            paper_id = None
            if oa_id:
                oa_suffix = oa_id.rsplit("/", 1)[-1] if "/" in oa_id else oa_id
                paper_id = f"openalex:{oa_suffix}"

            papers.append(PaperDocument(
                title=title, abstract=abstract, authors=authors,
                pdf_url=pdf_url if pdf_url else None,
                source_platform=self.PLATFORM_NAME,
                paper_id=paper_id
            ))
        return papers


def _decode_inverted_index(inv_idx: dict) -> str:
    """将 OpenAlex 的 inverted index 还原为纯文本"""
    if not inv_idx:
        return ""
    max_pos = max(max(positions) for positions in inv_idx.values() if positions)
    words = [""] * (max_pos + 1)
    for word, positions in inv_idx.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words)
