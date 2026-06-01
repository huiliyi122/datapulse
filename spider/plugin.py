# DataPulse - plugin
"""
爬虫插件系统 - 支持注册自定义解析器
"""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class ParseResult:
    """解析结果"""
    items: list[dict]
    next_urls: list[str] = None

    def __post_init__(self):
        if self.next_urls is None:
            self.next_urls = []


class BaseParser(ABC):
    """解析器基类 - 所有自定义解析器必须继承此类"""

    name: str = "base"
    url_pattern: str = ".*"  # URL 匹配正则

    @abstractmethod
    def parse(self, html: str, url: str) -> dict:
        """
        解析页面内容
        Args:
            html: 页面 HTML 文本
            url: 当前页面 URL
        Returns:
            解析后的字典数据
        """
        pass

    def matches(self, url: str) -> bool:
        """检查 URL 是否匹配此解析器"""
        return bool(re.match(self.url_pattern, url))

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.name})>"


class PluginManager:
    """
    解析器插件管理器
    按 URL 模式匹配分派到对应的解析器
    """

    def __init__(self):
        self._parsers: dict[str, BaseParser] = {}

    def register(self, parser: BaseParser) -> "PluginManager":
        """注册一个解析器插件"""
        if parser.name in self._parsers:
            raise ValueError(f"解析器 '{parser.name}' 已存在")
        self._parsers[parser.name] = parser
        return self

    def unregister(self, name: str):
        """移除一个解析器"""
        self._parsers.pop(name, None)

    def get_parser(self, url: str) -> Optional[BaseParser]:
        """
        根据 URL 查找匹配的解析器
        返回第一个匹配的解析器
        """
        for parser in self._parsers.values():
            if parser.matches(url):
                return parser
        return None

    def list(self) -> list[str]:
        """列出所有已注册的解析器名称"""
        return list(self._parsers.keys())

    def parse(self, html: str, url: str) -> dict:
        """
        使用匹配的解析器解析页面
        如果没有匹配的解析器，返回空字典
        """
        parser = self.get_parser(url)
        if parser:
            return parser.parse(html, url)
        return {"url": url, "content": html[:500]}


# 全局插件管理器实例
plugin_manager = PluginManager()


def register_parser(name: str, url_pattern: str = ".*"):
    """
    装饰器：注册一个函数作为解析器插件

    Usage:
        @register_parser("my_parser", r"https://example\.com/.*")
        def my_parser(html: str, url: str) -> dict:
            return {"url": url, "data": ...}
    """
    def decorator(func: Callable[..., dict]):
        class FunctionParser(BaseParser):
            name_ = name
            url_pattern_ = url_pattern

            @property
            def name(self):
                return self.name_

            @property
            def url_pattern(self):
                return self.url_pattern_

            def parse(self, html: str, url: str) -> dict:
                return func(html, url)

        parser = FunctionParser()
        plugin_manager.register(parser)
        return func
    return decorator
