# DataPulse - engine
"""
自动化数据采集引擎 - 分布式爬虫核心
"""
import asyncio
import hashlib
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger("datapulse.engine")


@dataclass
class CrawlRequest:
    """爬取请求数据类"""
    url: str
    method: str = "GET"
    headers: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    data: dict = field(default_factory=dict)
    cookies: dict = field(default_factory=dict)
    proxy: Optional[str] = None
    timeout: int = 30
    priority: int = 0
    retry_times: int = 3
    callback: Optional[str] = None


@dataclass
class CrawlResult:
    """爬取结果数据类"""
    url: str
    status_code: int
    html: str = ""
    json_data: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    elapsed: float = 0.0
    error: Optional[str] = None


class BaseMiddleware(ABC):
    """中间件基类"""

    @abstractmethod
    async def process_request(self, request: CrawlRequest) -> CrawlRequest:
        pass

    @abstractmethod
    async def process_response(self, result: CrawlResult) -> CrawlResult:
        pass


class RandomDelayMiddleware(BaseMiddleware):
    """随机延迟中间件 - 避免请求过快被封"""

    def __init__(self, min_delay: float = 1.0, max_delay: float = 3.0):
        self.min_delay = min_delay
        self.max_delay = max_delay

    async def process_request(self, request: CrawlRequest) -> CrawlRequest:
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)
        return request

    async def process_response(self, result: CrawlResult) -> CrawlResult:
        return result


class RotateUserAgentMiddleware(BaseMiddleware):
    """User-Agent 轮换中间件"""

    def __init__(self):
        self.ua = UserAgent(browsers=["chrome", "firefox", "edge"])

    async def process_request(self, request: CrawlRequest) -> CrawlRequest:
        if "User-Agent" not in request.headers:
            request.headers["User-Agent"] = self.ua.random
        return request

    async def process_response(self, result: CrawlResult) -> CrawlResult:
        return result


class ProxyMiddleware(BaseMiddleware):
    """代理中间件 - 支持IP轮换"""

    def __init__(self, proxy_list: list[str] = None):
        self.proxies = proxy_list or []
        self.current_idx = 0

    async def process_request(self, request: CrawlRequest) -> CrawlRequest:
        if self.proxies and not request.proxy:
            proxy = self.proxies[self.current_idx % len(self.proxies)]
            request.proxy = proxy
            self.current_idx += 1
        return request

    async def process_response(self, result: CrawlResult) -> CrawlResult:
        return result


class SpiderEngine:
    """
    分布式爬虫引擎
    支持异步并发、中间件链、自动重试、去重
    """

    def __init__(self, concurrent: int = 10):
        self.concurrent = concurrent
        self.semaphore = asyncio.Semaphore(concurrent)
        self.middlewares: list[BaseMiddleware] = []
        self.seen_urls: set = set()
        self.results: list[CrawlResult] = []
        self._stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "start_time": None,
        }

    def add_middleware(self, middleware: BaseMiddleware):
        """注册中间件"""
        self.middlewares.append(middleware)

    async def _ensure_session(self):
        """延迟创建共享 Session，复用连接池（线程安全）"""
        if not hasattr(self, '_session_lock'):
            self._session_lock = asyncio.Lock()
        async with self._session_lock:
            if not hasattr(self, '_session') or self._session is None:
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                )

    async def close(self):
        """关闭引擎，释放连接"""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
            self._session = None

    def _url_fingerprint(self, url: str) -> str:
        """URL去重指纹"""
        parsed = urlparse(url)
        normalized = f"{parsed.netloc}{parsed.path}".rstrip("/")
        return hashlib.md5(normalized.encode()).hexdigest()

    def is_duplicate(self, url: str) -> bool:
        """检查URL是否已爬取"""
        fp = self._url_fingerprint(url)
        if fp in self.seen_urls:
            return True
        self.seen_urls.add(fp)
        return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (aiohttp.ClientError, asyncio.TimeoutError)
        ),
    )
    async def fetch(self, request: CrawlRequest) -> CrawlResult:
        """执行HTTP请求（含自动重试）"""
        # 执行请求前中间件链
        for middleware in self.middlewares:
            request = await middleware.process_request(request)

        start = time.time()
        await self._ensure_session()
        try:
            async with self._session.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                params=request.params,
                json=request.data if request.method == "POST" else None,
                cookies=request.cookies,
                proxy=request.proxy,
                ssl=False,
            ) as resp:
                elapsed = time.time() - start
                content_type = resp.headers.get("Content-Type", "")

                if "application/json" in content_type:
                    data = await resp.json()
                    result = CrawlResult(
                        url=request.url,
                        status_code=resp.status,
                        json_data=data,
                        headers=dict(resp.headers),
                        elapsed=elapsed,
                    )
                else:
                    html = await resp.text(encoding="utf-8", errors="ignore")
                    result = CrawlResult(
                        url=request.url,
                        status_code=resp.status,
                        html=html,
                        headers=dict(resp.headers),
                        elapsed=elapsed,
                    )

        except aiohttp.ClientError as e:
            result = CrawlResult(
                url=request.url,
                status_code=0,
                error=str(e),
                elapsed=time.time() - start,
            )

        # 执行响应后中间件链
        for middleware in self.middlewares:
            result = await middleware.process_response(result)

        return result

    async def crawl(self, request: CrawlRequest) -> Optional[CrawlResult]:
        """爬取单个URL（带并发控制和去重）"""
        if self.is_duplicate(request.url):
            return None

        async with self.semaphore:
            self._stats["total"] += 1
            result = await self.fetch(request)

            if result.status_code == 200:
                self._stats["success"] += 1
                self.results.append(result)
            else:
                self._stats["failed"] += 1

            return result

    async def crawl_many(
        self, urls: list[str], **kwargs
    ) -> list[CrawlResult]:
        """批量爬取多个URL"""
        tasks = [
            self.crawl(CrawlRequest(url=url, **kwargs))
            for url in urls
        ]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def run(self, start_urls: list[str], **kwargs):
        """启动爬虫"""
        self._stats["start_time"] = time.time()
        logger.info("启动爬虫，目标: %d 个URL", len(start_urls))

        await self.crawl_many(start_urls, **kwargs)

        elapsed = time.time() - self._stats["start_time"]
        logger.info(
            "爬取完成! 总计: %d, 成功: %d, 失败: %d, 耗时: %.2fs",
            self._stats["total"], self._stats["success"],
            self._stats["failed"], elapsed,
        )

        return {
            "stats": self._stats,
            "results": self.results,
            "elapsed": round(elapsed, 2),
        }


# ============================================================
# HTML解析工具
# ============================================================

class HtmlParser:
    """HTML页面解析器"""

    @staticmethod
    def extract_links(html: str, base_url: str) -> list[str]:
        """提取页面中所有链接"""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            if full_url.startswith(("http://", "https://")):
                links.append(full_url)
        return list(set(links))

    @staticmethod
    def extract_meta(html: str) -> dict:
        """提取页面元信息"""
        soup = BeautifulSoup(html, "html.parser")
        meta = {
            "title": soup.title.get_text(strip=True) if soup.title else "",
            "description": "",
            "keywords": "",
        }
        for tag in soup.find_all("meta"):
            name = tag.get("name", "").lower()
            content = tag.get("content", "")
            if name == "description":
                meta["description"] = content
            elif name == "keywords":
                meta["keywords"] = content
        return meta

    @staticmethod
    def extract_text(html: str, css_selector: str = "body") -> str:
        """提取指定选择器的纯文本"""
        soup = BeautifulSoup(html, "html.parser")
        elements = soup.select(css_selector)
        return "\n".join(
            el.get_text(strip=True) for el in elements
        )

    @staticmethod
    def extract_table(html: str, css_selector: str = "table") -> list[dict]:
        """提取HTML表格数据"""
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one(css_selector)
        if not table:
            return []

        headers = [
            th.get_text(strip=True)
            for th in table.select("thead th, tr th")
        ]
        rows = []
        for tr in table.select("tbody tr, tr"):
            cells = tr.select("td")
            if len(cells) == len(headers):
                row = {}
                for i, cell in enumerate(cells):
                    row[headers[i]] = cell.get_text(strip=True)
                rows.append(row)

        return rows
