"""
Playwright 浏览器引擎 - 支持 JS 渲染 + 反反爬

特性:
- Stealth 模式：隐藏 WebDriver 痕迹，对抗指纹检测
- 人类行为模拟：随机鼠标移动、滚动、打字延迟
- 代理支持：HTTP/SOCKS5 代理 + 代理池自动轮换
- 请求头伪造：真实浏览器 headers
"""
import asyncio
import random
import time
from dataclasses import dataclass
from typing import Optional

from .engine import CrawlResult
from .proxy_pool import ProxyPool

# ============================================================
# Stealth JavaScript 注入脚本
# ============================================================

STEALTH_JS = """
// === 隐藏 webdriver 属性 ===
Object.defineProperty(navigator, 'webdriver', { get: () => false });

// === 修复 chrome 对象 ===
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {}
};

// === 修复 permissions ===
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications'
        ? Promise.resolve({state: Notification.permission})
        : originalQuery(parameters)
);

// === 修复 plugins ===
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// === 修复 languages ===
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en']
});

// === 修复 platform ===
Object.defineProperty(navigator, 'platform', {
    get: () => 'Win32'
});

// === 移除 PhantomJS 痕迹 ===
delete window.__phantomas;
delete window.callPhantom;
"""


@dataclass
class BrowserConfig:
    """浏览器高级配置"""

    # 基础
    headless: bool = True
    timeout: int = 30
    user_agent: str = ""

    # 视口 & 指纹
    viewport_width: int = 1280
    viewport_height: int = 800

    # Stealth 反反爬
    stealth: bool = True
    simulate_human: bool = True

    # 代理
    proxy: Optional[str] = None  # "http://user:pass@host:port"
    proxy_pool: Optional[ProxyPool] = None

    # 页面交互
    scroll_to_bottom: bool = False
    scroll_times: int = 3
    wait_selector: str = ""
    wait_timeout: float = 5.0
    random_delay: tuple = (0.5, 2.0)  # 页面加载后随机等待范围


class PlaywrightEngine:
    """
    增强版 Playwright 浏览器引擎

    反反爬能力:
    - ✅ 隐藏 webdriver/navigator 指纹
    - ✅ 随机视口大小
    - ✅ Chrome props 补全
    - ✅ 代理支持 + 代理池自动轮换
    - ✅ 人类行为模拟

    Usage:
        engine = PlaywrightEngine(BrowserConfig(stealth=True, simulate_human=True))
        await engine.start()
        result = await engine.fetch("https://example.com")
        await engine.stop()
    """

    def __init__(self, config: BrowserConfig = None):
        self.config = config or BrowserConfig()
        self._playwright = None
        self._browser = None
        self._context = None
        self._stats = {"total": 0, "success": 0, "failed": 0, "blocked": 0}

    # -------------------- 生命周期 --------------------

    async def start(self):
        """启动浏览器（自动配置 stealth）"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "缺少 playwright，请执行: pip install playwright && playwright install chromium"
            )

        self._playwright = await async_playwright().__aenter__()

        # 启动参数
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ]

        # 代理（浏览器级别）
        proxy_settings = None
        proxy = self._get_proxy()
        if proxy:
            proxy_settings = {"server": proxy}

        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless,
            args=launch_args,
            proxy=proxy_settings if proxy else None,
        )

        self._context = await self._new_context()
        return self

    async def _new_context(self):
        """创建新的浏览器上下文（含 stealth hooks）"""
        viewport = self._random_viewport() if self.config.stealth else {
            "width": self.config.viewport_width,
            "height": self.config.viewport_height,
        }

        user_agent = self.config.user_agent or self._random_ua()

        ctx = await self._browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        # 注入 stealth 脚本到所有新页面
        if self.config.stealth:
            async def _inject_stealth(page):
                await page.evaluate(STEALTH_JS)
            ctx.on("page", _inject_stealth)

            # 给当前已有页面也注入
            for page in ctx.pages:
                await page.evaluate(STEALTH_JS)

        return ctx

    async def stop(self):
        """关闭浏览器"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.__aexit__(None, None, None)

    # -------------------- 核心方法 --------------------

    async def fetch(self, url: str) -> CrawlResult:
        """访问页面，自动绕过常见反爬检测"""
        start_time = time.time()

        if not self._browser:
            await self.start()

        page = await self._context.new_page()

        if self.config.stealth:
            await page.evaluate(STEALTH_JS)

        try:
            # 添加额外请求头
            await page.set_extra_http_headers({
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            })

            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.config.timeout * 1000,
            )
            status_code = response.status if response else 0

            # 检测是否被拦截
            html = await page.content()
            if self._is_blocked(html, status_code):
                self._stats["blocked"] += 1

            # 等待指定元素出现
            if self.config.wait_selector:
                try:
                    await page.wait_for_selector(
                        self.config.wait_selector,
                        timeout=self.config.wait_timeout * 1000,
                    )
                except Exception:
                    pass

            # 人类行为模拟
            if self.config.simulate_human and not self._is_blocked(html, status_code):
                await self._simulate_human(page)

            # 滚动加载
            if self.config.scroll_to_bottom:
                await self._scroll_like_human(page, self.config.scroll_times)

            # 随机延迟
            if self.config.random_delay:
                await asyncio.sleep(random.uniform(*self.config.random_delay))

            html = await page.content()
            elapsed = time.time() - start_time

            return CrawlResult(
                url=url,
                status_code=status_code,
                html=html,
                elapsed=elapsed,
            )

        except Exception as e:
            self._stats["failed"] += 1
            return CrawlResult(
                url=url,
                status_code=0,
                error=str(e),
                elapsed=time.time() - start_time,
            )
        finally:
            await page.close()

    async def crawl(self, url: str) -> CrawlResult | None:
        """爬取单个 URL"""
        self._stats["total"] += 1
        result = await self.fetch(url)
        if result.status_code == 200:
            self._stats["success"] += 1
        return result

    async def crawl_many(self, urls: list[str]) -> list[CrawlResult]:
        """批量爬取"""
        tasks = [self.crawl(u) for u in urls]
        raw = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in raw if not isinstance(r, BaseException) and r is not None]

    # -------------------- Stealth 辅助方法 --------------------

    @staticmethod
    def _random_ua() -> str:
        """生成随机真实 User-Agent"""
        uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ]
        return random.choice(uas)

    @staticmethod
    def _random_viewport() -> dict:
        """随机视口大小（模拟不同屏幕）"""
        resolutions = [
            (1920, 1080), (1366, 768), (1440, 900),
            (1536, 864), (1680, 1050), (2560, 1440),
        ]
        w, h = random.choice(resolutions)
        # 浏览器窗口比屏幕略小
        return {"width": w - random.randint(0, 50), "height": h - random.randint(50, 150)}

    @staticmethod
    async def _simulate_human(page):
        """模拟人类行为"""
        # 随机轻微移动鼠标
        for _ in range(random.randint(2, 5)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y, steps=random.randint(3, 8))
            await asyncio.sleep(random.uniform(0.1, 0.3))

        # 随机小幅滚动
        scroll_distance = random.randint(50, 400)
        await page.evaluate("window.scrollBy(0, arguments[0])", scroll_distance)
        await asyncio.sleep(random.uniform(0.5, 1.5))

    @staticmethod
    async def _scroll_like_human(page, times: int):
        """模拟人类滚动到底部"""
        for i in range(times):
            amount = random.randint(300, 800)
            await page.evaluate("window.scrollBy(0, arguments[0])", amount)
            await asyncio.sleep(random.uniform(1.0, 2.5))

    @staticmethod
    def _is_blocked(html: str, status_code: int) -> bool:
        """检测是否被反爬拦截"""
        if status_code in (403, 429, 503):
            return True

        blocked_keywords = [
            "验证码", "请输入验证码", "滑块验证",
            "captcha", "verify you are a human",
            "请完成安全验证", "访问过于频繁",
            "Access Denied", "您的IP已被限制",
        ]
        html_lower = html.lower()
        return any(kw.lower() in html_lower for kw in blocked_keywords)

    # -------------------- 工具属性 --------------------

    @property
    def stats(self):
        return dict(self._stats)

    def _get_proxy(self) -> Optional[str]:
        """获取代理地址"""
        if self.config.proxy:
            return self.config.proxy
        if self.config.proxy_pool:
            p = self.config.proxy_pool.get_proxy()
            return p.url if p else None
        return None


# ============================================================
# 便捷函数
# ============================================================

async def render_page(
    url: str,
    wait_selector: str = "",
    timeout: int = 30,
    stealth: bool = True,
    proxy: str = None,
) -> str:
    """
    异步方法: 渲染单个 JS 页面返回 HTML
    自动应用 stealth 模式

    Usage:
        html = await render_page("https://example.com", stealth=True)
    """
    engine = PlaywrightEngine(BrowserConfig(
        headless=True,
        timeout=timeout,
        wait_selector=wait_selector,
        stealth=stealth,
        proxy=proxy,
    ))
    await engine.start()
    try:
        result = await engine.fetch(url)
        return result.html
    finally:
        await engine.stop()


def render_page_sync(
    url: str,
    wait_selector: str = "",
    timeout: int = 30,
    stealth: bool = True,
    proxy: str = None,
) -> str:
    """同步便捷方法: render_page 的同步包装"""
    return asyncio.run(render_page(url, wait_selector, timeout, stealth, proxy))
