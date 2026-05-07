"""
推送层模块：企业微信应用推送器[cite: 12]
(支持根据配置一键切换 PDF 物理切片下发 / 原生纯文本链接下发)
"""
import os
import logging
import requests
from core.interfaces import IPusher
from core.models import ProcessedReport, RunContext
from core.exceptions import PushError
from processors.pdf_splitter import PDFSplitter

logger = logging.getLogger(__name__)

class WeChatCorpPusher(IPusher):
    def __init__(self):
        self.corp_id = os.getenv("WECHAT_CORP_ID")
        self.corp_secret = os.getenv("WECHAT_CORP_SECRET")
        self.agent_id = os.getenv("WECHAT_AGENT_ID")

        if not all([self.corp_id, self.corp_secret, self.agent_id]):
            raise ValueError("企业微信配置不完整，请检查 .env[cite: 12]")
        self._access_token = None

    def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token

        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.corp_secret}"
        try:
            resp = requests.get(url, timeout=10).json()
            if resp.get("errcode") == 0:
                self._access_token = resp.get("access_token")
                return self._access_token
            raise PushError(f"获取企微 Token 失败: {resp.get('errmsg')}[cite: 12]")
        except Exception as e:
            raise PushError(f"Token 请求网络异常: {e}[cite: 12]")

    def _upload_media(self, file_path: str, media_type: str = "file") -> str:
        token = self._get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={token}&type={media_type}"
        try:
            with open(file_path, 'rb') as f:
                mime = 'image/png' if media_type == 'image' else 'application/pdf'
                files = {'media': (os.path.basename(file_path), f, mime)}
                resp = requests.post(url, files=files, timeout=60).json()

            if resp.get("errcode") == 0:
                return resp.get("media_id")
            else:
                logger.error(f"素材上传失败: {resp.get('errmsg')}[cite: 12]")
                return None
        except Exception as e:
            logger.error(f"上传异常 {file_path}: {e}[cite: 12]")
            return None

    def push(self, report: ProcessedReport, context: RunContext) -> bool:
        token = self._get_access_token()
        send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        target_user_id = context.current_user.wechat_id

        # 1. 永远先推送当前的【长图简报】[cite: 12]
        if report.summary_image_path and os.path.exists(report.summary_image_path):
            logger.info(f"    准备下发频道长图: {context.current_task.task_name}[cite: 12]")
            img_media_id = self._upload_media(report.summary_image_path, media_type="image")
            if img_media_id:
                img_payload = {
                    "touser": target_user_id, "msgtype": "image", "agentid": self.agent_id,
                    "image": {"media_id": img_media_id}
                }
                requests.post(send_url, json=img_payload, timeout=10)

        # 2. 【核心路由】：检查是否开启了 PDF 物理下发[cite: 12]
        if context.current_task.send_pdf:
            logger.info("    ⚙️ 检测到物理 PDF 下发开启，准备处理附件...[cite: 12]")
            for file_path in report.paper_files:
                if not os.path.exists(file_path):
                    continue

                final_files_to_push = PDFSplitter.split(file_path, max_mb=14.0)
                for p_file in final_files_to_push:
                    logger.info(f"    正在下发 PDF 附件: {os.path.basename(p_file)}[cite: 12]")
                    media_id = self._upload_media(p_file, media_type="file")
                    if media_id:
                        file_payload = {
                            "touser": target_user_id, "msgtype": "file", "agentid": self.agent_id,
                            "file": {"media_id": media_id}
                        }
                        requests.post(send_url, json=file_payload, timeout=10)
        else:
            logger.info("    ⚡ 检测到物理 PDF 下发关闭，自动降级为原生纯文本链接...[cite: 12]")
            for item in report.paper_links:
                text_msg = f"📄 【{item['title']}】\n\n👉 原文下载链接：\n{item['url']}"

                text_payload = {
                    "touser": target_user_id,
                    "msgtype": "text",
                    "agentid": self.agent_id,
                    "text": {"content": text_msg}
                }
                # 发送纯文本，微信可直接点开原生浏览器[cite: 12]
                requests.post(send_url, json=text_payload, timeout=10)
                logger.info(f"    已下发纯文本链接: {item['title'][:20]}...[cite: 12]")

        return True