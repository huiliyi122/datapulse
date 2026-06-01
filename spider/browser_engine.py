"""
Playwright 浏览器引擎 - 支持 JS 渲染页面爬取
"""
import asyncio
import time
from dataclasses import dataclass, field

from .engine import CrawlResult


@dataclass
class BrowserConfig:
    """浏览器配置"""
    headless: bool = True
    timeout: int = 30
    user_agent: str = ""
    viewport_width: int = 1280
    viewport_height: int = 800
    scroll_to_bottom: bool = False
    wait_selector: str = ""  # 等待某个 CSS 选择器出现
    wait_timeout: float = 5.0


class PlaywrightEngine:
    """
    基于 Playwright 的浏览器爬虫引擎
    支持 JavaScript 渲染的页面

    依赖: pip install playwright && playwright install chromium
    """

    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        self._browser = None
        self._context = None
        self._stats = {"total": 0, "success": 0, "failed": 0}

    async def start(self):
        """启动浏览器"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "缺少 playwright，请执行: pip install playwright && playwright install chromium"
            )

        self._playwright = await async_playwright().__aenter__()
        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless
        )
        self._context = await self._browser.new_context(
            viewport={
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            user_agent=self.config.user_agent or None,
        )
        return self

    async def stop(self):
        """关闭浏览器"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.__aexit__(None, None, None)

    async def fetch(self, url: str) -> CrawlResult:
        """访问单个页面并获取内容"""
        start = time.time()

        if not self._browser:
            await self.start()

        page = await self._context.new_page()
        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.config.timeout * 1000,
            )
            status_code = response.status if response else 0

            # 等待指定元素
            if self.config.wait_selector:
                try:
                    await page.wait_for_selector(
                        self.config.wait_selector,
                        timeout=self.config.wait_timeout * 1000,
                    )
                except Exception:
                    pass

            # 滚动到底部（加载更多内容）
            if self.config.scroll_to_bottom:
                await page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight)"
                )
                await asyncio.sleep(1)

            html = await page.content()
            elapsed = time.time() - start

            return CrawlResult(
                url=url,
                status_code=status_code,
                html=html,
                elapsed=elapsed,
            )
        except Exception as e:
            return CrawlResult(
                url=url,
                status_code=0,
                error=str(e),
                elapsed=time.time() - start,
            )
        finally:
            await page.close()

    async def crawl(self, url: str) -> CrawlResult | None:
        """爬取单个 URL"""
        self._stats["total"] += 1
        result = await self.fetch(url)
        if result.status_code == 200:
            self._stats["success"] += 1
        else:
            self._stats["failed"] += 1
        return result

    async def crawl_many(self, urls: list[str]) -> list[CrawlResult]:
        """批量爬取"""
        results = []
        for url in urls:
            result = await self.crawl(url)
            if result:
                results.append(result)
        return results

    @property
    def stats(self):
        return dict(self._stats)


def render_page(url: str, wait_selector: str = "", timeout: int = 30) -> str:
    """
    同步便捷方法: 渲染单个 JS 页面，返回 HTML
    适用于简单场景

    Usage:
        html = render_page("https://example.com", wait_selector=".product-item")
    """
    async def _render():
        engine = PlaywrightEngine(
            BrowserConfig(
                headless=True,
                timeout=timeout,
                wait_selector=wait_selector,
                wait_timeout=5,
            )
        )
        await engine.start()
        try:
            result = await engine.fetch(url)
            return result.html
        finally:
            await engine.stop()

    return asyncio.run(_render())
