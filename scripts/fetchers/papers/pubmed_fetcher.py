"""
PubMed 论文抓取器
API: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
"""
import os
import logging
import time
import requests
import xml.etree.ElementTree as ET
from typing import List
from urllib.parse import urlencode

from scripts.core.models import PaperDocument
from scripts.fetchers.papers.base import BasePlatformFetcher

logger = logging.getLogger(__name__)

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedFetcher(BasePlatformFetcher):
    PLATFORM_NAME = "pubmed"

    def __init__(self):
        self.api_key = os.getenv("PUBMED_API_KEY")
        self.email = os.getenv("PUBMED_EMAIL", "research@example.com")
        # PubMed 速率: 3/sec 无 key, 10/sec 有 key
        self.delay = 0.15 if self.api_key else 0.4

    def search(self, keywords: List[str], max_results: int = 5,
               deep_mode: bool = False) -> List[PaperDocument]:
        papers = []
        for kw in keywords:
            try:
                papers.extend(self._search_one(kw, max_results))
            except Exception as e:
                logger.error(f"PubMed '{kw}' 抓取失败: {e}")
        return papers

    def _search_one(self, query: str, limit: int) -> List[PaperDocument]:
        # Step 1: ESearch 获取 PMID 列表
        esearch_params = {
            "db": "pubmed",
            "term": query,
            "retmax": limit,
            "retmode": "xml",
            "sort": "date",
        }
        if self.api_key:
            esearch_params["api_key"] = self.api_key
        esearch_params["email"] = self.email

        esearch_url = f"{PUBMED_BASE}/esearch.fcgi"
        resp = requests.get(esearch_url, params=esearch_params, timeout=15)
        resp.raise_for_status()
        time.sleep(self.delay)

        root = ET.fromstring(resp.content)
        pmids = [e.text for e in root.findall(".//Id") if e.text]
        if not pmids:
            return []

        # Step 2: EFetch 获取摘要
        efetch_params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }
        if self.api_key:
            efetch_params["api_key"] = self.api_key
        efetch_params["email"] = self.email

        efetch_url = f"{PUBMED_BASE}/efetch.fcgi"
        resp = requests.get(efetch_url, params=efetch_params, timeout=20)
        resp.raise_for_status()

        return self._parse_efetch(resp.content)

    def _parse_efetch(self, xml_content: bytes) -> List[PaperDocument]:
        root = ET.fromstring(xml_content)
        papers = []
        for article in root.findall(".//PubmedArticle"):
            medline = article.find(".//MedlineCitation")
            if medline is None:
                continue
            art = medline.find(".//Article")
            if art is None:
                continue

            title = art.findtext(".//ArticleTitle", default="")
            abstract_parts = art.findall(".//AbstractText")
            abstract = " ".join(
                (a.text or "") + "".join(e.tail or "" for e in a if e.tail)
                for a in abstract_parts
            )

            authors = []
            for au in art.findall(".//Author"):
                ln = au.findtext("LastName", default="")
                fn = au.findtext("ForeName", default="")
                if ln:
                    authors.append(f"{fn} {ln}".strip())

            pmid = medline.findtext("PMID", default="")
            pdf_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None

            papers.append(PaperDocument(
                title=title.strip(), abstract=abstract.strip(),
                authors=authors, pdf_url=pdf_url,
                source_platform=self.PLATFORM_NAME
            ))
        return papers
