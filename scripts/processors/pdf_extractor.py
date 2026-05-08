"""
PDF 纯文本提取器：从学术 PDF 中提取全文，供 LLM 精读使用
"""
import logging
from pypdf import PdfReader

logger = logging.getLogger(__name__)

MAX_CHARS = 30000  # 单篇论文最大字符数，超长部分截断


class PDFExtractor:

    @staticmethod
    def extract(file_path: str) -> str:
        try:
            reader = PdfReader(file_path)
            pages = []
            total = 0
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
                    total += len(text)
                    if total > MAX_CHARS:
                        break

            full_text = "\n\n".join(pages)
            # 清洗：合并被换行打断的单词（LaTeX PDF 常见问题）
            full_text = _clean_academic_text(full_text)
            if total > MAX_CHARS:
                full_text += f"\n\n[注：全文共 {total} 字符，已截断至 {MAX_CHARS} 字符]"
            return full_text
        except Exception as e:
            logger.warning(f"PDF 文本提取失败 {file_path}: {e}")
            return ""


def _clean_academic_text(text: str) -> str:
    """清洗学术 PDF 提取文本中的常见噪音"""
    import re
    # 移除行尾连字符断词 (e.g., "under-\nstanding" -> "understanding")
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    # 合并孤立的换行（保留段落间的双换行）
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    # 压缩多余空白
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
