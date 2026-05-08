"""
每日推送系统：重构后的主程序入口
"""
import os
import sys
from pathlib import Path

# 终极护栏：强制将项目根目录加入 Python 环境变量
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from scripts.settings import ENV_FILE

# ... 下面保留你原来的代码不变
# 强制注入绝对路径的 .env
load_dotenv(dotenv_path=ENV_FILE)

from scripts.core.engine import PipelineEngine
from scripts.fetchers import WebPaperFetcher, LocalVocabFetcher, GitHubReleaseFetcher, LiteratureFetcher
from scripts.processors import LLMProcessor, SemanticClusteringFilter, WeeklyDigestEngine
from scripts.pushers import WeChatCorpPusher

def main():
    print("正在初始化星枢集成架构...")
    try:
        fetcher_registry = {
            "literature": LiteratureFetcher(),
            "internet": WebPaperFetcher(),
            "vocabulary": LocalVocabFetcher(),
            "github": GitHubReleaseFetcher(),
        }

        processor = LLMProcessor()
        pusher = WeChatCorpPusher()
        clustering_filter = SemanticClusteringFilter()
        weekly_digest = WeeklyDigestEngine()

        engine = PipelineEngine(
            fetchers=fetcher_registry,
            processor=processor,
            pusher=pusher,
            clustering_filter=clustering_filter,
            weekly_digest=weekly_digest,
        )

        engine.run()

    except Exception as e:
        print(f"系统启动失败: {e}")
        exit(1)

if __name__ == "__main__":
    main()