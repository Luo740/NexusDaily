"""
获取层模块：本地词库抓取器[cite: 1]
从 assets/ 目录读取静态资产。
"""
import os
from core import IFetcher, DailyData, Article, RunContext


class LocalVocabFetcher(IFetcher):
    def fetch(self, context: RunContext) -> DailyData:
        # 路径约束：必须指向资产目录[cite: 1]
        vocab_path = os.path.join(os.getcwd(), "assets", "vocabulary.txt")
        data = DailyData()

        if os.path.exists(vocab_path):
            with open(vocab_path, "r", encoding="utf-8") as f:
                words = [line.strip() for line in f if line.strip()]
                # 简单包装为 Article 实体用于后续处理
                content = "\n".join(words[:10])  # 演示：每次取前10个
                data.articles.append(Article(
                    title="今日单词池",
                    content=content,
                    source="local_assets"
                ))
        return data