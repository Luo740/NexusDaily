"""
Europe PMC 论文抓取器
API: https://www.ebi.ac.uk/europepmc/webservices/rest/
无需鉴权
"""
import logging
import requests
from typing import List

from scripts.core.models import PaperDocument
from scripts.fetchers.papers.base import BasePlatformFetcher

logger = logging.getLogger(__name__)

EPMC_API = "https://www.ebi.ac.uk/europepmc/webservices/rest"


class EuropePMCFetcher(BasePlatformFetcher):
    PLATFORM_NAME = "europe_pmc"

    def search(self, keywords: List[str], max_results: int = 5,
               deep_mode: bool = False) -> List[PaperDocument]:
        papers = []
        for kw in keywords:
            try:
                papers.extend(self._search_one(kw, max_results))
            except Exception as e:
                logger.error(f"Europe PMC '{kw}' 抓取失败: {e}")
        return papers

    def _search_one(self, query: str, limit: int) -> List[PaperDocument]:
        params = {
            "query": query,
            "resultType": "core",
            "pageSize": limit,
            "format": "json",
            "sort": "FIRST_PUBLICATION_DATE:desc",
        }
        resp = requests.get(f"{EPMC_API}/search", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        papers = []
        for item in data.get("resultList", {}).get("result", []):
            title = item.get("title", "")
            abstract = item.get("abstractText", "")
            author_str = item.get("authorString", "")
            authors = [a.strip() for a in author_str.split(",") if a.strip()]

            pdf_url = None
            pmid = item.get("pmid", "")
            pmcid = item.get("pmcid", "")
            doi = item.get("doi", "")
            if pmcid:
                pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
            elif pmid:
                pdf_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            elif doi:
                pdf_url = f"https://doi.org/{doi}"

            papers.append(PaperDocument(
                title=title, abstract=abstract, authors=authors,
                pdf_url=pdf_url, source_platform=self.PLATFORM_NAME
            ))
        return papers
