"""
处理层模块：基于大模型的智能数据处理引擎
"""
import os
import random
import logging
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader

from scripts.core import IProcessor, DailyData, PaperDocument, ProcessedReport, RunContext, ProcessError
from scripts.processors.image_renderer import ImageRenderer
from scripts.settings import CONFIG_DIR

logger = logging.getLogger(__name__)

SCENE_THEMES = {
    "workplace": "职场办公（会议、邮件、汇报、面试等）",
    "daily_life": "日常生活（购物、就餐、出行、社交等）",
    "travel": "旅行出行（机场、酒店、景点、问路等）",
    "tech": "科技讨论（AI、编程、数码产品、科技新闻等）",
    "campus": "校园学习（上课、考试、图书馆、社团等）",
}

class LLMProcessor(IProcessor):
    def __init__(self):
        # 1. 恢复丢失的鉴权配置
        self.api_key = os.getenv("AI_API_KEY")
        self.base_url = os.getenv("AI_BASE_URL")
        self.model_name = os.getenv("AI_MODEL_NAME", "deepseek-chat")

        if not self.api_key:
            raise ValueError("启动失败: AI_API_KEY 未配置")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        # 2. 使用全局路径定位模板目录
        template_dir = CONFIG_DIR / "prompts"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.image_renderer = ImageRenderer()

    def process(self, data: DailyData, context: RunContext) -> ProcessedReport:
        if context.current_task.task_type == "vocabulary":
            return self._process_vocabulary(data, context)

        if context.current_task.task_type == "literature":
            if context.reading_mode == "deep":
                return self._process_deep_reading(data, context)
            else:
                return self._process_skim_reading(data, context)

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

            logger.info(f"    🧠 请求模型 ({self.model_name}) 进行浅层解读与频道图文排版...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一位拥有顶尖学术品味和科技嗅觉的专栏主编。请严格遵循用户的排版指令。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            summary = response.choices[0].message.content

            # 这里的 workspace_dir 已经在 engine 中使用 pathlib 处理好并传入
            report_md_path = os.path.join(context.workspace_dir, "report.md")
            with open(report_md_path, 'w', encoding='utf-8') as f:
                f.write(summary)

            report_img_path = os.path.join(context.workspace_dir, "report.png")
            self.image_renderer.render(summary, report_img_path)

            paper_files = [paper.pdf_local_path for paper in data.papers if paper.pdf_local_path]

            # 提取出需要进行文本发送的标题和链接对
            paper_links = [{"title": paper.title, "url": paper.pdf_url} for paper in data.papers if paper.pdf_url]

            return ProcessedReport(
                summary_text=summary,
                summary_image_path=report_img_path,
                paper_files=paper_files,
                paper_links=paper_links
            )

        except Exception as e:
            raise ProcessError(f"AI 处理或长图渲染发生异常: {e}")

    def _process_vocabulary(self, data: DailyData, context: RunContext) -> ProcessedReport:
        if not data.articles or not data.articles[0].content.strip():
            return ProcessedReport(summary_text="今日暂无单词数据。")

        words = [w.strip() for w in data.articles[0].content.split("\n") if w.strip()]
        if not words:
            return ProcessedReport(summary_text="今日暂无单词数据。")

        theme_key = getattr(context.current_task, "scene_theme", "random") or "random"
        if theme_key == "random" or theme_key not in SCENE_THEMES:
            theme_key = random.choice(list(SCENE_THEMES.keys()))
        theme_desc = SCENE_THEMES[theme_key]

        logger.info(f"    📝 场景主题: {theme_desc}")
        word_list = ", ".join(words)

        prompt = f"""你是一位资深英语教师，擅长创作鲜活、口语化的场景对话。

请用以下 5 个英语单词，创作一段在「{theme_desc}」场景下的自然对话。

**单词**：{word_list}

**要求**：
1. 对话包含 2-3 个人物，篇幅 4-6 个来回，简洁自然
2. 每个目标单词在英文对话中至少出现一次，并用 **粗体** 标记
3. 中文对话独立成文：用母语者的口语表达，加入语气词（吧、嘛、啦、哦等）、省略、停顿等真实对话特征，不要逐字翻译英文句式
4. 英文对话同样口语化：使用缩写（gonna、wanna、it's）、省略句、日常用语，避免书面语
5. 输出严格按以下三段格式，用标记行分隔：

[中文对话]
人物A：早啊，今天看着挺精神的嘛！
人物B：还行吧，昨晚总算睡了个好觉。
（以此类推，8-12 行）

[英文对话]
A: Morning! You look pretty fresh today.
B: Yeah, I guess. Finally got some good sleep last night.
（以此类推，8-12 行）

[单词表]
| 单词 | 词性 | 中文释义 |
|------|------|----------|
| word1 | n. | 释义1 |
（每个目标单词一行，共 5 行）"""

        logger.info("    🧠 请求 AI 生成词汇对话...")
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "你是一位专业的英语教师，擅长创作自然的场景对话和准确的单词释义。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=800
        )
        content = response.choices[0].message.content
        logger.info("    ✅ AI 生成完成")

        cn_text, en_text, table_text = self._parse_vocab_response(content)
        if not cn_text or not en_text or not table_text:
            raise ProcessError("AI 词汇对话解析失败，输出格式不符合要求")

        ws_dir = context.workspace_dir
        img_cn_path = os.path.join(ws_dir, "vocab_cn.png")
        img_en_path = os.path.join(ws_dir, "vocab_en.png")
        img_table_path = os.path.join(ws_dir, "vocab_table.png")

        self.image_renderer.render(self._format_dialogue_md(cn_text, "请用英语说出以下内容"), img_cn_path)
        logger.info(f"    🎨 CN 对话图: {img_cn_path}")
        self.image_renderer.render(self._format_dialogue_md(en_text, "English Dialogue"), img_en_path)
        logger.info(f"    🎨 EN 对话图: {img_en_path}")
        self.image_renderer.render(self._format_table_md(table_text), img_table_path)
        logger.info(f"    🎨 单词表图: {img_table_path}")

        return ProcessedReport(
            summary_text=cn_text,
            summary_image_path=img_cn_path,
            extra_images=[img_en_path, img_table_path],
        )

    # 粗读模式：每批摘要总字符数上限（避免 AI 输出过长导致图片超限）
    SKIM_BATCH_CHARS = 4000

    def _process_skim_reading(self, data: DailyData, context: RunContext) -> ProcessedReport:
        """粗读模式：聚合论文摘要 → 按预估高度自动分批 → 每批一张图"""
        if not data.papers:
            return ProcessedReport(summary_text="今日暂无学术论文更新。")

        # 按摘要长度分批，避免单张图过长
        batches = self._batch_papers(data.papers)
        logger.info(f"    🧠 粗读模式：{len(data.papers)} 篇论文 → {len(batches)} 批")

        template = self.jinja_env.get_template("literature/skim.j2")
        ws_dir = context.workspace_dir
        paper_images = []

        for bi, batch in enumerate(batches):
            batch_label = f"skim_{bi + 1}" if len(batches) > 1 else ""
            prompt = template.render(
                task_name=context.current_task.task_name,
                papers=batch
            )

            logger.info(f"    第 {bi+1}/{len(batches)} 批 ({len(batch)} 篇)...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一位拥有顶尖学术品味和科技嗅觉的专栏主编。请严格遵循用户的排版指令。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            summary = response.choices[0].message.content

            # 写入 report.md
            md_name = f"report_{batch_label}.md" if batch_label else "report.md"
            with open(os.path.join(ws_dir, md_name), 'w', encoding='utf-8') as f:
                f.write(summary)

            # 预估高度，确定图片文件名
            est_h = self.image_renderer.estimate_height(summary)
            img_name = f"report_{batch_label}.png" if batch_label else "report.png"
            img_path = os.path.join(ws_dir, img_name)
            self.image_renderer.render(summary, img_path)
            logger.info(f"    🎨 粗读图: {img_path} (预估 {est_h}px)")

            titles = " + ".join(p.title[:25] for p in batch)
            paper_images.append({
                "title": titles,
                "image_path": img_path,
                "url": ""
            })

        paper_links = [
            {"title": p.title, "url": p.pdf_url}
            for p in data.papers if p.pdf_url
        ]

        # 单批走 summary_image_path，多批走 paper_images（避免重复推送）
        if len(paper_images) == 1:
            return ProcessedReport(
                summary_text="粗读完成",
                summary_image_path=paper_images[0]["image_path"],
                paper_links=paper_links,
            )
        return ProcessedReport(
            summary_text="粗读完成",
            paper_images=paper_images,
            paper_links=paper_links,
        )

    def _process_deep_reading(self, data: DailyData, context: RunContext) -> ProcessedReport:
        """精读模式：一文一图，全文精读"""
        if not data.papers:
            return ProcessedReport(summary_text="今日暂无学术论文更新。")

        template = self.jinja_env.get_template("literature/deep.j2")
        ws_dir = context.workspace_dir
        paper_images = []
        paper_links = []

        for i, paper in enumerate(data.papers):
            # 全文过长时截断
            full_text = paper.full_text or paper.abstract
            if len(full_text) > 20000:
                full_text = full_text[:20000] + "\n\n[注：全文过长，已截断至 20000 字符]"
            truncated = PaperDocument(
                title=paper.title, abstract=paper.abstract,
                authors=paper.authors, pdf_url=paper.pdf_url,
                source_platform=paper.source_platform, full_text=full_text,
            )

            prompt = template.render(
                task_name=context.current_task.task_name,
                papers=[truncated]
            )

            logger.info(f"    🧠 精读 {i+1}/{len(data.papers)}: {paper.title[:40]}...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一位顶会审稿人，擅长对学术论文进行深度、批判性的全文解读。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=3000
            )
            summary = response.choices[0].message.content

            img_name = f"deep_report_{i+1}.png"
            img_path = os.path.join(ws_dir, img_name)
            self.image_renderer.render(summary, img_path)
            est_h = self.image_renderer.estimate_height(summary)
            logger.info(f"    🎨 精读图 {i+1}: {img_path} (预估 {est_h}px)")

            paper_images.append({
                "title": paper.title,
                "image_path": img_path,
                "url": paper.pdf_url or ""
            })

        for p in data.papers:
            if p.pdf_url:
                paper_links.append({"title": p.title, "url": p.pdf_url})

        return ProcessedReport(
            summary_text="精读完成",
            paper_images=paper_images,
            paper_links=paper_links,
        )

    @staticmethod
    def _batch_papers(papers) -> list:
        """将论文按摘要总长度分批，控制每批产出图片高度"""
        batches = []
        current_batch = []
        current_chars = 0
        for p in papers:
            abstract_len = len(p.abstract or "")
            if current_chars + abstract_len > LLMProcessor.SKIM_BATCH_CHARS and current_batch:
                batches.append(current_batch)
                current_batch = []
                current_chars = 0
            current_batch.append(p)
            current_chars += abstract_len
        if current_batch:
            batches.append(current_batch)
        return batches if batches else [papers]

    @staticmethod
    def _parse_vocab_response(content: str) -> tuple[str, str, str]:
        cn_text = en_text = table_text = ""
        sections = content.split("[中文对话]")
        if len(sections) > 1:
            after_cn = sections[1].split("[英文对话]")
            cn_text = after_cn[0].strip() if after_cn else ""
            if len(after_cn) > 1:
                after_en = after_cn[1].split("[单词表]")
                en_text = after_en[0].strip() if after_en else ""
                table_text = after_en[1].strip() if len(after_en) > 1 else ""
        return cn_text, en_text, table_text

    @staticmethod
    def _format_dialogue_md(text: str, title: str) -> str:
        lines = text.strip().split("\n")
        formatted = [f"## {title}\n"]
        for line in lines:
            line = line.strip()
            if not line:
                formatted.append("")
            elif "：" in line or ":" in line:
                formatted.append(f"**{line}**")
            else:
                formatted.append(line)
            formatted.append("")
        return "\n".join(formatted)

    @staticmethod
    def _format_table_md(text: str) -> str:
        lines = text.strip().split("\n")
        formatted = ["## 今日单词表\n"]
        for line in lines:
            formatted.append(line)
        return "\n".join(formatted)