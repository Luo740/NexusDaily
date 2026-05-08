"""
全局设置与路径中心 (settings.py)
利用 pathlib 实现优雅、跨平台的绝对路径解析
"""
from pathlib import Path

# 1. 锚定项目根目录
# __file__ 指向 settings.py 本身
# .parent 指向 scripts 目录
# .parent.parent 指向 NexusDaily 根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 2. 映射核心业务目录
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
ASSETS_DIR = PROJECT_ROOT / "assets"
ENV_FILE = PROJECT_ROOT / ".env"

# 3. 自动护栏：如果文件夹不存在则自动创建，防止运行时报错
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)