"""
获取层模块：GitHub Release 追踪器
抓取指定仓库的最新 Release 信息。
"""
import logging
import requests
from typing import List

from scripts.core import IFetcher, DailyData, Article, RunContext, FetchError

logger = logging.getLogger(__name__)


class GitHubReleaseFetcher(IFetcher):
    GITHUB_API = "https://api.github.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "NexusDaily/1.0",
            "Accept": "application/vnd.github+json"
        })

    def _parse_repo_spec(self, kw: str) -> tuple[str, str] | None:
        """解析 'github:owner/repo' 格式的关键词"""
        if kw.startswith("github:"):
            spec = kw[7:]
            parts = spec.split("/")
            if len(parts) == 2:
                return parts[0], parts[1]
        return None

    def _fetch_releases(self, owner: str, repo: str, limit: int = 3) -> List[Article]:
        url = f"{self.GITHUB_API}/repos/{owner}/{repo}/releases?per_page={limit}"
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        releases = resp.json()

        articles = []
        for rel in releases:
            body = (rel.get("body") or "")[:300]
            articles.append(Article(
                title=f"[{owner}/{repo}] {rel['tag_name']}: {rel.get('name', 'Release')}",
                content=body,
                source="github",
                url=rel.get("html_url")
            ))
        return articles

    def fetch(self, context: RunContext) -> DailyData:
        data = DailyData()
        for kw in context.current_task.keywords:
            spec = self._parse_repo_spec(kw)
            if not spec:
                continue
            owner, repo = spec
            try:
                logger.info(f"    -> 抓取 GitHub Release: {owner}/{repo}")
                data.articles.extend(self._fetch_releases(owner, repo))
            except Exception as e:
                logger.error(f"    GitHub {owner}/{repo} 抓取失败: {e}")

        if not data.articles:
            raise FetchError(f"GitHub Release 任务 '{context.current_task.task_name}' 抓取失败。")

        return data
