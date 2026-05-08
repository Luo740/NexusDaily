"""
NEXUS DAILY - Core Module
星枢日报核心模块初始化文件。
负责暴露核心引擎、状态管理、异常定义、数据模型与接口契约[cite: 1, 2]。
"""

from .engine import PipelineEngine
from .state_manager import StateManager
from .exceptions import (
    DailyAssistantError,
    FetchError,
    ProcessError,
    PushError
)
from .models import (
    TaskConfig,
    UserSubscription,
    RunContext,
    Article,
    PaperDocument,
    DailyData,
    ProcessedReport
)
from .interfaces import (
    IFetcher,
    IProcessor,
    IPusher
)

# 显式定义导出列表，确保模块整洁并支持 'from core import *'[cite: 1]
__all__ = [
    "PipelineEngine",
    "StateManager",
    "DailyAssistantError",
    "FetchError",
    "ProcessError",
    "PushError",
    "TaskConfig",
    "UserSubscription",
    "RunContext",
    "Article",
    "PaperDocument",
    "DailyData",
    "ProcessedReport",
    "IFetcher",
    "IProcessor",
    "IPusher",
]