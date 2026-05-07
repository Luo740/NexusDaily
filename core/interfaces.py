"""
核心模块：接口抽象层[cite: 5]
"""
from abc import ABC, abstractmethod
from core.models import DailyData, ProcessedReport, RunContext

class IFetcher(ABC):
    @abstractmethod
    def fetch(self, context: RunContext) -> DailyData:
        pass

class IProcessor(ABC):
    @abstractmethod
    def process(self, data: DailyData, context: RunContext) -> ProcessedReport:
        pass

class IPusher(ABC):
    @abstractmethod
    def push(self, report: ProcessedReport, context: RunContext) -> bool:
        pass