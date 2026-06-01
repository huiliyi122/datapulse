"""
自动翻页检测与处理

支持三种翻页模式:
1. 链接翻页 - /page/2, ?page=3&size=10
2. 数字翻页 - 1, 2, 3, ... N, Next
3. 加载更多 - Load More / 无限滚动

Usage:
    from spider.pagination import PaginationDetector

    detector = PaginationDetector()
    pages = detector.detect(html, base_url="https://example.com/products")

    # 自动爬取所有分页
    for page_html in detector.crawl_all(start_url, engine):
        items = extract_items(page_html)
"""
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse


@dataclass
class PageLink:
    """分页链接"""
    url: str
    text: str
    page_num: int = 1
    is_current: bool = False
    is_next: bool = False


class PaginationDetector:
    """
    自动翻页检测器

    从页面 HTML 中自动发现分页模式
    """

    # 常见的分页链接关键词
    PAGINATION_KEYWORDS = [
        "page", "p", "pg", "pageNum", "pageIndex",
        "offset", "start",
        "分页", "页码", "下一页", "上一页",
    ]

    # Next 链接常见文本
    NEXT_TEXTS = [
        "next", "下一页", "下页", "»", "›", ">", "→",
        "next page", "Next", "NEXT",
    ]

    def __init__(self):
        self._page_param = None

    # ============================================================
    # 检测方法
    # ============================================================

    def detect(self, html: str, base_url: str = "") -> list[PageLink]:
        """
        从 HTML 中检测分页链接

        Returns:
            分页链接列表（按页码排序）
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        results = []

        # 策略1: 查找包含分页关键词的 <a> 标签
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            cls = " ".join(a.get("class", []))

            # 检查 URL 参数是否包含分页关键词
            page_num = self._extract_page_number(href)

            # 检查链接文本是否包含数字
            if page_num is None and text.isdigit():
                page_num = int(text)

            # 是否是当前页
            is_current = (
                "active" in cls.lower()
                or "current" in cls.lower()
                or a.get("aria-current") is not None
            )

            # 是否是 Next
            is_next = (
                text.lower() in [t.lower() for t in self.NEXT_TEXTS]
                or "next" in cls.lower()
            )

            if page_num is not None or is_next or self._is_pagination_url(href):
                full_url = urljoin(base_url, href) if base_url else href
                results.append(PageLink(
                    url=full_url,
                    text=text,
                    page_num=page_num or 0,
                    is_current=is_current,
                    is_next=is_next,
                ))

        # 策略2: 如果没有找到分页链接，尝试从 URL 参数推断
        if not results and base_url:
            inferred = self._infer_pagination(base_url)
            if inferred:
                return inferred

        # 去重、排序
        seen = set()
        unique = []
        for link in results:
            if link.url not in seen:
                seen.add(link.url)
                unique.append(link)
        unique.sort(key=lambda x: x.page_num)

        return unique

    def infer_page_count(self, html: str) -> int:
        """推断总页数"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        # 常见模式: 共 XX 页, Page X of Y, X/Y
        text = soup.get_text()
        patterns = [
            r"共\s*(\d+)\s*页",
            r"Page\s+\d+\s+of\s+(\d+)",
            r"(\d+)\s*/\s*\d+\s*页",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 0

    # ============================================================
    # 翻页 URL 生成
    # ============================================================

    def generate_page_urls(
        self,
        base_url: str,
        total_pages: int,
        page_param: str = None,
    ) -> list[str]:
        """
        生成所有分页 URL

        自动检测 URL 中的分页参数并生成下一页 URL
        """
        parsed = urlparse(base_url)
        params = parse_qs(parsed.query)

        # 自动检测分页参数
        if page_param is None:
            for key in params:
                if any(kw in key.lower() for kw in self.PAGINATION_KEYWORDS):
                    page_param = key
                    break
            if page_param is None:
                page_param = "page"

        urls = []
        for page in range(1, total_pages + 1):
            new_params = {k: v for k, v in params.items()}
            new_params[page_param] = [str(page)]
            new_query = urlencode(new_params, doseq=True)
            new_url = urlunparse(parsed._replace(query=new_query))
            urls.append(new_url)

        return urls

    # ============================================================
    # 自动爬取所有分页
    # ============================================================

    async def crawl_all(
        self,
        start_url: str,
        engine,
        max_pages: int = 10,
    ) -> list[dict]:
        """
        自动爬取所有分页

        Args:
            start_url: 起始 URL
            engine: SpiderEngine 或 PlaywrightEngine 实例
            max_pages: 最大页数限制

        Returns:
            [{"url": "...", "page": 1, "html": "..."}, ...]
        """
        results = []
        visited = set()

        current_url = start_url

        for _ in range(max_pages):
            if current_url in visited:
                break
            visited.add(current_url)

            # 爬取当前页
            from .engine import SpiderEngine, CrawlRequest

            if isinstance(engine, SpiderEngine):
                result = await engine.crawl(CrawlRequest(url=current_url))
            else:
                result = await engine.fetch(current_url)

            if result.status_code != 200:
                break

            html = result.html
            results.append({"url": current_url, "html": html, "page": len(results) + 1})

            # 检测下一页
            links = self.detect(html, base_url=current_url)
            next_links = [l for l in links if l.is_next]
            if next_links:
                current_url = next_links[0].url
            else:
                # 尝试数字翻页
                next_page_links = [l for l in links if l.page_num == len(results) + 1]
                if next_page_links:
                    current_url = next_page_links[0].url
                else:
                    break

        return results

    # ============================================================
    # 内部工具
    # ============================================================

    def _extract_page_number(self, url: str) -> Optional[int]:
        """从 URL 中提取页码"""
        # 路径模式: /page/5, /p/3, /page=5
        path_match = re.search(r"/(?:page|p)/(\d+)/?", url)
        if path_match:
            return int(path_match.group(1))

        # 参数模式: ?page=5&size=10
        if "?" in url:
            query = url.split("?")[1]
            for param in query.split("&"):
                if "=" in param:
                    key, val = param.split("=", 1)
                    if any(kw in key.lower() for kw in self.PAGINATION_KEYWORDS):
                        try:
                            return int(val)
                        except ValueError:
                            pass
        return None

    def _is_pagination_url(self, url: str) -> bool:
        """判断 URL 是否包含分页参数"""
        return any(kw.lower() in url.lower() for kw in self.PAGINATION_KEYWORDS)

    def _infer_pagination(self, base_url: str) -> list[PageLink]:
        """从 URL 模式推断分页链接"""
        # 检测 URL 中是否已有 page param
        parsed = urlparse(base_url)
        params = parse_qs(parsed.query)

        page_param = None
        for key in params:
            if any(kw in key.lower() for kw in self.PAGINATION_KEYWORDS):
                page_param = key
                break

        if not page_param:
            return []

        current = int(params.get(page_param, [1])[0])
        urls = []
        for p in range(max(1, current - 2), current + 3):
            new_params = {k: v for k, v in params.items()}
            new_params[page_param] = [str(p)]
            new_query = urlencode(new_params, doseq=True)
            urls.append(PageLink(
                url=urlunparse(parsed._replace(query=new_query)),
                text=str(p),
                page_num=p,
                is_current=p == current,
            ))
        return urls
