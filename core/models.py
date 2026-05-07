"""
数据模型层：定义各层级之间传递的统一数据结构[cite: 6]
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class TaskConfig:
    """单个订阅任务的配置实体[cite: 6]"""
    task_name: str
    task_type: str
    keywords: List[str]
    prompt_template: str
    send_pdf: bool = True  # 是否物理下发 PDF 附件[cite: 6]

@dataclass
class UserSubscription:
    user_name: str
    wechat_id: str
    tasks: List[TaskConfig] = field(default_factory=list)

    def __post_init__(self):
        # 处理嵌套的 dict 转换为 TaskConfig 对象[cite: 6]
        if self.tasks and isinstance(self.tasks[0], dict):
            self.tasks = [TaskConfig(**t) for t in self.tasks]

@dataclass
class RunContext:
    date_str: str
    workspace_dir: str
    papers_dir: str
    current_user: Optional[UserSubscription] = None
    current_task: Optional[TaskConfig] = None

@dataclass
class Article:
    title: str
    content: str
    source: str
    url: Optional[str] = None

@dataclass
class PaperDocument:
    title: str
    abstract: str
    authors: List[str]
    pdf_local_path: Optional[str] = None
    pdf_url: Optional[str] = None

@dataclass
class DailyData:
    articles: List[Article] = field(default_factory=list)
    papers: List[PaperDocument] = field(default_factory=list)

@dataclass
class ProcessedReport:
    summary_text: str
    summary_image_path: Optional[str] = None
    paper_files: List[str] = field(default_factory=list)
    paper_links: List[Dict[str, str]] = field(default_factory=list)