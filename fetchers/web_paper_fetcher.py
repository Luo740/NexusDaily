"""
获取层模块：网络与论文综合抓取器[cite: 8]
支持 V2EX (Atom) 与 arXiv (API) 的内容抓取。
"""
import os
import re
import logging
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from core import IFetcher, DailyData, Article, PaperDocument, RunContext, FetchError

logger = logging.getLogger(__name__)

class WebPaperFetcher(IFetcher):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }

    def fetch(self, context: RunContext) -> DailyData:
        data = DailyData()
        task_keywords = context.current_task.keywords

        for kw in task_keywords:
            if kw.lower() == "v2ex":
                try:
                    logger.info(f"    -> 抓取资讯源: V2EX[cite: 8]")
                    data.articles.extend(self._fetch_atom_articles("https://www.v2ex.com/index.xml", limit=3))
                except Exception as e:
                    logger.error(f"    V2EX 抓取失败: {e}")

            elif kw.startswith("cat:") or kw.startswith("all:"):
                try:
                    logger.info(f"    -> 抓取 arXiv 论文 (关键词/分类): {kw}[cite: 8]")
                    data.papers.extend(self._fetch_arxiv_papers(kw, context.papers_dir, max_results=2))
                except Exception as e:
                    logger.error(f"    arXiv {kw} 抓取失败: {e}")

        if not data.articles and not data.papers:
            raise FetchError(f"频道任务 '{context.current_task.task_name}' 的所有订阅源抓取失败。[cite: 8]")

        return data

    def _fetch_atom_articles(self, atom_url: str, limit: int = 5) -> list[Article]:
        response = requests.get(atom_url, headers=self.headers, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        articles = []

        for entry in root.findall('atom:entry', namespace)[:limit]:
            title = entry.findtext('atom:title', namespaces=namespace, default='无标题')
            link_elem = entry.find('atom:link', namespace)
            link = link_elem.attrib.get('href') if link_elem is not None else ''

            content = entry.findtext('atom:content', namespaces=namespace)
            if not content:
                content = entry.findtext('atom:summary', namespaces=namespace, default='')

            clean_text = re.sub(r'<[^>]+>', '', content).replace('\n', ' ').strip()
            clean_text = clean_text[:200] + "..." if len(clean_text) > 200 else clean_text

            articles.append(Article(title=title, content=clean_text, source=urlparse(atom_url).netloc, url=link))
        return articles

    def _fetch_arxiv_papers(self, search_query: str, papers_dir: str, max_results: int = 2) -> list[PaperDocument]:
        api_url = f"http://export.arxiv.org/api/query?search_query={search_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        papers = []

        for entry in root.findall('atom:entry', namespace):
            title = entry.findtext('atom:title', namespaces=namespace, default='').replace('\n', ' ')
            summary = entry.findtext('atom:summary', namespaces=namespace, default='').replace('\n', ' ')
            authors = [author.findtext('atom:name', namespaces=namespace) for author in entry.findall('atom:author', namespace)]

            pdf_url = None
            for link in entry.findall('atom:link', namespace):
                if link.attrib.get('title') == 'pdf':
                    pdf_url = link.attrib.get('href')
                    if pdf_url and 'abs' in pdf_url:
                        pdf_url = pdf_url.replace('abs', 'pdf') + ".pdf"
                    break

            paper = PaperDocument(title=title, abstract=summary, authors=authors, pdf_url=pdf_url)

            if pdf_url:
                try:
                    logger.info(f"    正在下载论文 PDF: {title[:30]}...")
                    pdf_resp = requests.get(pdf_url, headers=self.headers, timeout=30)
                    pdf_resp.raise_for_status()

                    safe_filename = "".join([c for c in title[:50] if c.isalnum() or c==' ']).rstrip() + ".pdf"
                    local_path = os.path.join(papers_dir, safe_filename)

                    with open(local_path, 'wb') as f:
                        f.write(pdf_resp.content)

                    paper.pdf_local_path = local_path
                except Exception as e:
                    logger.warning(f"    论文 PDF 下载失败: {pdf_url}, 错误: {e}")
            papers.append(paper)
        return papers