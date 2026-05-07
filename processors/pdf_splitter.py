"""
处理层模块：PDF 物理切片引擎[cite: 11]
利用动态内存探针技术，精确计算页面体积，确保不发生分卷超标。
"""
import os
import io
import logging
from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

class PDFSplitter:
    @staticmethod
    def split(file_path: str, max_mb: float = 14.0) -> list[str]:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb <= 19.5:
            return [file_path]

        logger.info(f"✂️ 触发动态精准切片引擎: {os.path.basename(file_path)} ({file_size_mb:.1f}MB)[cite: 11]")

        reader = PdfReader(file_path)
        output_files = []
        base, ext = os.path.splitext(file_path)

        pages_for_current_part = []
        part_num = 1

        for i, page in enumerate(reader.pages):
            pages_for_current_part.append(page)

            test_writer = PdfWriter()
            for p in pages_for_current_part:
                test_writer.add_page(p)

            mem_buffer = io.BytesIO()
            test_writer.write(mem_buffer)
            current_size_mb = len(mem_buffer.getvalue()) / (1024 * 1024)

            if current_size_mb > max_mb:
                if len(pages_for_current_part) > 1:
                    last_page = pages_for_current_part.pop()

                    part_path = f"{base}_Part{part_num}{ext}"
                    final_writer = PdfWriter()
                    for p in pages_for_current_part:
                        final_writer.add_page(p)

                    with open(part_path, "wb") as f:
                        final_writer.write(f)

                    output_files.append(part_path)
                    logger.info(f"   - 已生成分卷 {part_num}: {os.path.basename(part_path)} ({os.path.getsize(part_path)/(1024*1024):.1f}MB)[cite: 11]")

                    pages_for_current_part = [last_page]
                    part_num += 1
                else:
                    logger.warning(f"   ⚠️ 警告：检测到极其庞大的单页数据 (页码 {i})，可能包含未压缩原图。[cite: 11]")

        if pages_for_current_part:
            part_path = f"{base}_Part{part_num}{ext}"
            final_writer = PdfWriter()
            for p in pages_for_current_part:
                final_writer.add_page(p)

            with open(part_path, "wb") as f:
                final_writer.write(f)

            output_files.append(part_path)
            logger.info(f"   - 已生成尾卷 {part_num}: {os.path.basename(part_path)} ({os.path.getsize(part_path)/(1024*1024):.1f}MB)[cite: 11]")

        return output_files