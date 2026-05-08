"""
arXiv 论文抓取器：通过 arXiv API 获取预印本论文
"""
import os
import time
import logging
import requests
import xml.etree.ElementTree as ET
from typing import List

from scripts.core.models import PaperDocument
from scripts.fetchers.papers.base import BasePlatformFetcher

logger = logging.getLogger(__name__)

ARXIV_API = "http://export.arxiv.org/api/query"


class ArxivFetcher(BasePlatformFetcher):
    PLATFORM_NAME = "arxiv"

    def __init__(self):
        self.headers = {
            'User-Agent': 'NexusDaily/1.0 (mailto:research@example.com)'
        }

    def search(self, keywords: List[str], max_results: int = 5,
               deep_mode: bool = False) -> List[PaperDocument]:
        papers = []
        for i, kw in enumerate(keywords):
            if not (kw.startswith("cat:") or kw.startswith("all:")):
                continue
            if i > 0:
                time.sleep(3.5)  # arXiv 速率限制: 1 req / 3 sec
            try:
                papers.extend(self._fetch(kw, max_results, deep_mode))
            except Exception as e:
                logger.error(f"arXiv {kw} 抓取失败: {e}")
        return papers

    def _fetch(self, search_query: str, max_results: int,
               deep_mode: bool, papers_dir: str = "") -> List[PaperDocument]:
        url = f"{ARXIV_API}?search_query={search_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
        resp = requests.get(url, headers=self.headers, timeout=15)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        papers = []

        for entry in root.findall('atom:entry', ns):
            title = entry.findtext('atom:title', namespaces=ns, default='').replace('\n', ' ').strip()
            summary = entry.findtext('atom:summary', namespaces=ns, default='').replace('\n', ' ').strip()
            authors = [a.findtext('atom:name', namespaces=ns) or ''
                       for a in entry.findall('atom:author', ns)]

            pdf_url = None
            for link in entry.findall('atom:link', ns):
                if link.attrib.get('title') == 'pdf':
                    pdf_url = link.attrib.get('href')
                    if pdf_url and 'abs' in pdf_url:
                        pdf_url = pdf_url.replace('abs', 'pdf') + ".pdf"
                    break

            paper = PaperDocument(
                title=title, abstract=summary, authors=authors,
                pdf_url=pdf_url, source_platform=self.PLATFORM_NAME
            )

            if deep_mode and pdf_url and papers_dir:
                self._download_and_extract(paper, papers_dir)

            papers.append(paper)
        return papers

    def _download_and_extract(self, paper: PaperDocument, papers_dir: str):
        """下载 PDF 并提取全文"""
        from scripts.processors.pdf_extractor import PDFExtractor
        try:
            logger.info(f"    下载 arXiv PDF: {paper.title[:40]}...")
            pdf_resp = requests.get(paper.pdf_url, headers=self.headers, timeout=30)
            pdf_resp.raise_for_status()

            safe = "".join(c for c in paper.title[:50] if c.isalnum() or c == ' ').rstrip()
            local = os.path.join(papers_dir, f"{safe}.pdf")
            with open(local, 'wb') as f:
                f.write(pdf_resp.content)
            paper.pdf_local_path = local

            paper.full_text = PDFExtractor.extract(local)
            logger.info(f"    全文提取完成: {len(paper.full_text)} 字符")
        except Exception as e:
            logger.warning(f"    arXiv PDF 下载/提取失败: {e}")
