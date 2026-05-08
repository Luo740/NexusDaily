"""
处理层模块：Markdown 转长图渲染器
"""
import os
import logging
import markdown
from html2image import Html2Image

logger = logging.getLogger(__name__)


class ImageRenderer:
    BASE_WIDTH = 800
    PADDING_V = 80   # 上下 padding 总和
    TITLE_H = 60     # 标题区域高度
    LINE_H = 36      # 单行高度 (22px * 1.6 ≈ 35, 加余量)
    MAX_HEIGHT = 5000  # 移动端长图安全上限，超出自动分批
    CHARS_PER_LINE = 45  # 800px 宽 / 22px 字体 ≈ 每行中文字数

    def __init__(self):
        self.hti = Html2Image()

    @classmethod
    def estimate_height(cls, text: str) -> int:
        """根据文本长度估算渲染后的图片高度"""
        lines_from_newlines = text.count('\n')
        lines_from_chars = len(text) / cls.CHARS_PER_LINE
        estimated_lines = max(lines_from_newlines, lines_from_chars)
        return int(cls.PADDING_V + cls.TITLE_H + estimated_lines * cls.LINE_H)

    def render(self, md_content: str, output_path: str, font_size: int = 22) -> str:
        logger.info("🎨 正在将 Markdown 渲染为精美长图...")

        html_body = markdown.markdown(md_content, extensions=['extra'])

        # 根据内容行数自适应计算高度
        line_count = md_content.count('\n') + 1
        height = self.PADDING_V + self.TITLE_H + line_count * self.LINE_H
        height = max(height, 400)  # 保底最小高度

        if height > self.MAX_HEIGHT:
            logger.warning(f"    ⚠️ 图片高度 {height}px 超出安全上限 {self.MAX_HEIGHT}px，移动端可能截断")

        css = f"""
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f7f9f9;
            color: #333;
            padding: 40px;
            width: {self.BASE_WIDTH}px;
            margin: 0;
            box-sizing: border-box;
        }}
        h2 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; margin-top: 20px; font-size: {font_size + 4}px; }}
        h3 {{ color: #202124; margin-top: 20px; font-size: {font_size + 2}px; }}
        p {{ line-height: 1.6; font-size: {font_size}px; color: #5f6368; margin: 6px 0; }}
        strong {{ color: #202124; font-size: {font_size}px; }}
        table {{ border-collapse: collapse; width: 100%; font-size: {font_size}px; }}
        th {{ background-color: #1a73e8; color: white; padding: 8px 12px; text-align: left; }}
        td {{ padding: 6px 12px; border-bottom: 1px solid #e0e0e0; }}
        """

        full_html = f"<html><head><style>{css}</style></head><body>{html_body}</body></html>"

        self.hti.output_path = os.path.dirname(output_path)
        filename = os.path.basename(output_path)

        self.hti.screenshot(html_str=full_html, save_as=filename, size=(self.BASE_WIDTH, height))

        logger.info(f"✅ 长图渲染完成: {output_path} ({self.BASE_WIDTH}x{height})")
        return output_path
