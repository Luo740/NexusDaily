"""
获取层模块：网络资讯抓取器 (注册制)
支持 V2EX (Atom) 等互联网数据源，通过注册机制扩展。
论文平台已迁移至 scripts/fetchers/papers/ 包。
"""
import logging
import re
import requests
import xml.etree.ElementTree as ET
from typing import Callable, Dict, List
from urllib.parse import urlparse

from scripts.core import IFetcher, DailyData, Article, RunContext

logger = logging.getLogger(__name__)

# 数据源抓取函数签名: (keywords: List[str], context: RunContext) -> List[Article]
SourceFunc = Callable[[List[str], RunContext], List[Article]]


class WebPaperFetcher(IFetcher):
    """互联网资讯抓取器：V2EX + 可注册扩展源，供 internet 任务使用"""

    _registry: Dict[str, SourceFunc] = {}

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
        }
        self._init_registry()

    def _init_registry(self):
        if "v2ex" not in self._registry:
            self._registry["v2ex"] = self._fetch_v2ex

    @classmethod
    def register(cls, name: str, func: SourceFunc):
        """注册新的互联网数据源"""
        cls._registry[name] = func
        logger.info(f"[注册] 新互联网源已注册: {name}")

    def fetch(self, context: RunContext) -> DailyData:
        data = DailyData()
        for kw in context.current_task.keywords:
            source_name, articles = self._dispatch(kw)
            if articles:
                logger.info(f"    -> 互联网源 [{source_name}] 返回 {len(articles)} 条资讯")
                data.articles.extend(articles)

        if not data.articles:
            from scripts.core.exceptions import FetchError
            raise FetchError(f"频道 '{context.current_task.task_name}' 的所有订阅源抓取失败。")
        return data

    def _dispatch(self, kw: str) -> tuple[str, List[Article]]:
        if kw.lower() == "v2ex":
            return "v2ex", self._fetch_v2ex([kw])
        for name, func in self._registry.items():
            if name == "v2ex":
                continue
            try:
                articles = func([kw])
                if articles:
                    return name, articles
            except Exception as e:
                logger.warning(f"    自定义源 [{name}] 处理失败: {e}")
        return "unknown", []

    def _fetch_v2ex(self, keywords: List[str]) -> List[Article]:
        try:
            return self._fetch_atom_articles("https://www.v2ex.com/index.xml", limit=3)
        except Exception as e:
            logger.error(f"    V2EX 抓取失败: {e}")
            return []

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

            articles.append(Article(title=title, content=clean_text,
                                    source=urlparse(atom_url).netloc, url=link))
        return articles
