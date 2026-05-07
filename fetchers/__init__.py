"""
fetchers 模块统一入口[cite: 1]
"""
from .web_paper_fetcher import WebPaperFetcher
from .local_vocab_fetcher import LocalVocabFetcher

__all__ = ["WebPaperFetcher", "LocalVocabFetcher"]