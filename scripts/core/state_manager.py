"""
核心层模块：状态管理器[cite: 7]
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

class StateManager:
    def __init__(self, state_dir: str):
        self.state_file_path = os.path.join(state_dir, "progress.json")
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """确保状态文件及其目录存在[cite: 7]"""
        os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)
        if not os.path.exists(self.state_file_path):
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def get_progress(self, wechat_id: str, task_type: str = "english_vocab") -> int:
        try:
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get(wechat_id, {}).get(task_type, 0)
        except Exception as e:
            logger.error(f"读取进度失败: {e}")
            return 0

    def advance_progress(self, wechat_id: str, step: int, task_type: str = "english_vocab") -> int:
        try:
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if wechat_id not in data: data[wechat_id] = {}
            new_index = data[wechat_id].get(task_type, 0) + step
            data[wechat_id][task_type] = new_index
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return new_index
        except Exception as e:
            logger.error(f"写入进度失败: {e}")
            return -1