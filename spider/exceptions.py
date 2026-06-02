"""
DataPulse 自定义异常体系

层次结构:
    DataPulseError (基类)
    ├── SpiderError (爬虫相关)
    │   ├── RequestError (HTTP 请求失败)
    │   ├── ParseError (解析失败)
    │   ├── ProxyError (代理失败)
    │   └── BlockedError (被反爬拦截)
    ├── PipelineError (管道相关)
    ├── ConfigError (配置错误)
    └── AuthError (认证错误)
"""


class DataPulseError(Exception):
    """基础异常"""
    def __init__(self, message: str, detail: dict = None):
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


# ============================================================
# 爬虫异常
# ============================================================

class SpiderError(DataPulseError):
    """爬虫通用异常"""
    pass


class RequestError(SpiderError):
    """HTTP 请求失败"""
    def __init__(self, message: str, url: str = "", status_code: int = 0):
        super().__init__(message, {"url": url, "status_code": status_code})
        self.url = url
        self.status_code = status_code


class ParseError(SpiderError):
    """页面解析失败"""
    def __init__(self, message: str, url: str = "", selector: str = ""):
        super().__init__(message, {"url": url, "selector": selector})
        self.url = url
        self.selector = selector


class ProxyError(SpiderError):
    """代理连接失败"""
    def __init__(self, message: str, proxy_url: str = ""):
        super().__init__(message, {"proxy_url": proxy_url})
        self.proxy_url = proxy_url


class BlockedError(SpiderError):
    """被反爬拦截"""
    def __init__(self, message: str, url: str = "", reason: str = ""):
        super().__init__(message, {"url": url, "reason": reason})
        self.url = url
        self.reason = reason


# ============================================================
# 管道异常
# ============================================================

class PipelineError(DataPulseError):
    """数据管道异常"""
    pass


class ExportError(PipelineError):
    """数据导出失败"""
    pass


# ============================================================
# 配置异常
# ============================================================

class ConfigError(DataPulseError):
    """配置错误"""
    pass


# ============================================================
# 认证异常
# ============================================================

class AuthError(DataPulseError):
    """认证失败"""
    pass


class InvalidTokenError(AuthError):
    """Token 无效"""
    pass
