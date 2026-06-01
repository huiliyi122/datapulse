"""
DataPulse - 数据采集引擎

双引擎架构:
- SpiderEngine (aiohttp): 高速异步爬虫，适合静态页面
- PlaywrightEngine: JS渲染浏览器引擎，带 stealth 反反爬
"""
from .engine import SpiderEngine, CrawlRequest, CrawlResult, HtmlParser
from .browser_engine import PlaywrightEngine, BrowserConfig, render_page
from .pipelines import (
    DataItem, DataPipelineManager,
    DedupPipeline, CleanPipeline, FilterPipeline,
    CsvExportPipeline, JsonExportPipeline,
)
from .proxy_pool import ProxyPool, Proxy
from .plugin import BaseParser, PluginManager, plugin_manager, register_parser
from .ai_parser import AIParser, auto_extract
from .js_reverse import JSReverseEngineer, ReverseResult, try_reverse

__all__ = [
    # 引擎
    "SpiderEngine", "CrawlRequest", "CrawlResult", "HtmlParser",
    "PlaywrightEngine", "BrowserConfig", "render_page",
    # 管道
    "DataItem", "DataPipelineManager",
    "DedupPipeline", "CleanPipeline", "FilterPipeline",
    "CsvExportPipeline", "JsonExportPipeline",
    # 代理池
    "ProxyPool", "Proxy",
    # 插件
    "BaseParser", "PluginManager", "plugin_manager", "register_parser",
    # AI
    "AIParser", "auto_extract",
    # JS逆向 (实验性)
    "JSReverseEngineer", "ReverseResult", "try_reverse",
]
