"""
核心模块：全局异常定义
"""

class DailyAssistantError(Exception):
    """每日推送系统基础异常类"""
    pass

class FetchError(DailyAssistantError):
    """信息获取阶段异常 (如网络中断、防爬拦截)"""
    pass

class ProcessError(DailyAssistantError):
    """AI 处理阶段异常 (如 API 余额不足、上下文超限)"""
    pass

class PushError(DailyAssistantError):
    """推送阶段异常 (如 Token 失效、多媒体上传失败)"""
    pass