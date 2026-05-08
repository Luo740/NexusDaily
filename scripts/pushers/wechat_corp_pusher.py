"""
推送层模块：企业微信应用推送器
"""
import os
import logging
import requests

# 增加 scripts. 前缀
from scripts.core.interfaces import IPusher
from scripts.core.models import ProcessedReport, RunContext
from scripts.core.exceptions import PushError
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

        # 1.5 推送额外图片（如词汇任务的英文对话、单词表）
        for img_path in report.extra_images:
            if img_path and os.path.exists(img_path):
                logger.info(f"    准备下发额外图片: {os.path.basename(img_path)}")
                img_media_id = self._upload_media(img_path, media_type="image")
                if img_media_id:
                    img_payload = {
                        "touser": target_user_id, "msgtype": "image", "agentid": self.agent_id,
                        "image": {"media_id": img_media_id}
                    }
                    requests.post(send_url, json=img_payload, timeout=10)

        # 2. 推送精读论文图（每 2 篇一图）
        for pi in report.paper_images:
            img_path = pi.get("image_path", "")
            if img_path and os.path.exists(img_path):
                logger.info(f"    准备下发精读图: {pi.get('title', '')[:30]}")
                img_media_id = self._upload_media(img_path, media_type="image")
                if img_media_id:
                    img_payload = {
                        "touser": target_user_id, "msgtype": "image", "agentid": self.agent_id,
                        "image": {"media_id": img_media_id}
                    }
                    requests.post(send_url, json=img_payload, timeout=10)

        # 3. 推送合并链接文本（所有论文链接一条消息）
        if report.paper_links:
            lines = []
            for i, item in enumerate(report.paper_links, 1):
                lines.append(f"📄 {i}. 【{item['title']}】\n👉 {item['url']}")
            combined = "\n\n".join(lines)

            text_payload = {
                "touser": target_user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {"content": combined}
            }
            requests.post(send_url, json=text_payload, timeout=10)
            logger.info(f"    已下发合并链接文本 ({len(report.paper_links)} 篇)")

        return True