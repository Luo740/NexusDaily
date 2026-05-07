"""
处理层模块：Markdown 转长图渲染器[cite: 9]
"""
import os
import logging
import markdown
from html2image import Html2Image

logger = logging.getLogger(__name__)

class ImageRenderer:
    def __init__(self):
        # 初始化截屏工具[cite: 9]
        self.hti = Html2Image()

    def render(self, md_content: str, output_path: str) -> str:
        logger.info("🎨 正在将 Markdown 渲染为精美长图...[cite: 9]")

        # 1. Markdown 转 HTML[cite: 9]
        html_body = markdown.markdown(md_content, extensions=['extra'])

        # 2. 注入微信阅读友好的 CSS 样式[cite: 9]
        css = """
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f7f9f9;
            color: #333;
            padding: 40px;
            width: 800px; /* 固定宽度，适配手机屏幕缩放 */
            margin: 0;
            box-sizing: border-box;
        }
        h2 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; margin-top: 30px;}
        h3 { color: #202124; margin-top: 25px; }
        p { line-height: 1.6; font-size: 16px; color: #5f6368; }
        strong { color: #202124; }
        """

        full_html = f"<html><head><style>{css}</style></head><body>{html_body}</body></html>"

        # 3. 设定输出目录并截图 (高度自适应)[cite: 9]
        self.hti.output_path = os.path.dirname(output_path)
        filename = os.path.basename(output_path)

        # size=(宽, 高) 高度设大一点，以免截断[cite: 9]
        self.hti.screenshot(html_str=full_html, save_as=filename, size=(800, 3000))

        logger.info(f"✅ 长图渲染完成: {output_path}[cite: 9]")
        return output_path