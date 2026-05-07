"""
处理层模块：基于大模型的智能数据处理引擎[cite: 10]
"""
import os
import logging
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader
from core import IProcessor, DailyData, ProcessedReport, RunContext, ProcessError
from processors.image_renderer import ImageRenderer

logger = logging.getLogger(__name__)

class LLMProcessor(IProcessor):
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        self.base_url = os.getenv("AI_BASE_URL")
        self.model_name = os.getenv("AI_MODEL_NAME", "deepseek-chat")

        if not self.api_key:
            raise ValueError("启动失败: AI_API_KEY 未配置[cite: 10]")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        template_dir = os.path.join(os.getcwd(), "config", "prompts")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self.image_renderer = ImageRenderer()

    def process(self, data: DailyData, context: RunContext) -> ProcessedReport:
        if not data.articles and not data.papers:
            return ProcessedReport(summary_text="今日暂无新资讯。", paper_files=[], paper_links=[])

        try:
            template_name = context.current_task.prompt_template
            template = self.jinja_env.get_template(template_name)

            prompt = template.render(
                task_name=context.current_task.task_name,
                articles=data.articles,
                papers=data.papers
            )

            logger.info(f"    🧠 请求模型 ({self.model_name}) 进行浅层解读与频道图文排版...[cite: 10]")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一位拥有顶尖学术品味和科技嗅觉的专栏主编。请严格遵循用户的排版指令。[cite: 10]"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            summary = response.choices[0].message.content

            report_md_path = os.path.join(context.workspace_dir, "report.md")
            with open(report_md_path, 'w', encoding='utf-8') as f:
                f.write(summary)

            report_img_path = os.path.join(context.workspace_dir, "report.png")
            self.image_renderer.render(summary, report_img_path)

            paper_files = [paper.pdf_local_path for paper in data.papers if paper.pdf_local_path]

            # 提取出需要进行文本发送的标题和链接对[cite: 10]
            paper_links = [{"title": paper.title, "url": paper.pdf_url} for paper in data.papers if paper.pdf_url]

            return ProcessedReport(
                summary_text=summary,
                summary_image_path=report_img_path,
                paper_files=paper_files,
                paper_links=paper_links
            )

        except Exception as e:
            raise ProcessError(f"AI 处理或长图渲染发生异常: {e}[cite: 10]")