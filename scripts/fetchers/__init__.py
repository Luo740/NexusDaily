"""
fetchers 模块统一入口
"""
from .web_paper_fetcher import WebPaperFetcher
from .local_vocab_fetcher import LocalVocabFetcher
from .github_release_fetcher import GitHubReleaseFetcher
from .literature_fetcher import LiteratureFetcher

__all__ = ["WebPaperFetcher", "LocalVocabFetcher", "GitHubReleaseFetcher", "LiteratureFetcher"]