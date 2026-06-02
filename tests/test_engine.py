"""测试爬虫引擎"""
import pytest

from spider.engine import SpiderEngine, CrawlRequest, HtmlParser, RandomDelayMiddleware
from spider.exceptions import RequestError, BlockedError


class TestCrawlRequest:
    def test_default_values(self):
        req = CrawlRequest(url="https://example.com")
        assert req.method == "GET"
        assert req.timeout == 30
        assert req.retry_times == 3

    def test_custom_values(self):
        req = CrawlRequest(url="https://test.com", method="POST", timeout=10, retry_times=5)
        assert req.method == "POST"
        assert req.timeout == 10
        assert req.retry_times == 5


class TestHtmlParser:
    def test_extract_meta_empty(self):
        meta = HtmlParser.extract_meta("<html><head></head><body></body></html>")
        assert meta["title"] == ""

    def test_extract_text_by_selector(self):
        html = "<html><body><div class='content'>Hello World<p>Para</p></div></body></html>"
        text = HtmlParser.extract_text(html, ".content")
        assert "Hello" in text
        assert "Para" in text

    def test_extract_table_no_table(self):
        rows = HtmlParser.extract_table("<html><body>No table</body></html>")
        assert rows == []


class TestSpiderEngine:
    @pytest.mark.asyncio
    async def test_url_dedup(self):
        engine = SpiderEngine()
        assert not await engine.is_duplicate("https://example.com")
        assert await engine.is_duplicate("https://example.com")
        assert not await engine.is_duplicate("https://example.com/page2")

    def test_middleware_registration(self):
        engine = SpiderEngine()
        mw = RandomDelayMiddleware(min_delay=0.1, max_delay=0.2)
        engine.add_middleware(mw)
        assert len(engine.middlewares) == 1


class TestExceptions:
    def test_request_error(self):
        err = RequestError("连接超时", url="https://example.com", status_code=504)
        assert err.url == "https://example.com"
        assert err.status_code == 504
        assert str(err) == "连接超时"

    def test_blocked_error(self):
        err = BlockedError("被反爬拦截", url="https://test.com", reason="滑块验证码")
        assert err.reason == "滑块验证码"

    def test_exception_hierarchy(self):
        from spider.exceptions import SpiderError, DataPulseError
        assert isinstance(RequestError("x"), SpiderError)
        assert isinstance(RequestError("x"), DataPulseError)
        assert isinstance(BlockedError("x"), SpiderError)
