"""
每日推送系统：重构后的主程序入口
"""
import os
from dotenv import load_dotenv

load_dotenv()

from core.engine import PipelineEngine
from fetchers import WebPaperFetcher, LocalVocabFetcher
from processors import LLMProcessor
from pushers import WeChatCorpPusher

def main():
    print("正在初始化星枢集成架构...")
    try:
        # 实例化所有可用的抓取器
        fetcher_registry = {
            "literature": WebPaperFetcher(),
            "internet": WebPaperFetcher(),
            "vocabulary": LocalVocabFetcher()
        }

        processor = LLMProcessor()
        pusher = WeChatCorpPusher()

        # 依赖注入：传入映射表
        engine = PipelineEngine(
            fetchers=fetcher_registry,
            processor=processor,
            pusher=pusher
        )

        engine.run()

    except Exception as e:
        print(f"系统启动失败: {e}")
        exit(1)

if __name__ == "__main__":
    main()