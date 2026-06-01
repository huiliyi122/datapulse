"""
DataPulse 内置解析器插件
"""
from .html_parser import HtmlTableParser, JsonApiParser

__all__ = ["HtmlTableParser", "JsonApiParser"]

# 自动注册内置解析器
try:
    from spider.plugin import plugin_manager
    plugin_manager.register(HtmlTableParser())
    plugin_manager.register(JsonApiParser())
except ImportError:
    pass
