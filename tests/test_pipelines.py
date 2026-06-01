# DataPulse Test Suite
"""测试数据处理管道"""
import pytest

from spider.pipelines import (
    DataItem, DedupPipeline, CleanPipeline,
    FilterPipeline, DataPipelineManager,
)
from spider.engine import CrawlResult, HtmlParser


class TestDedupPipeline:
    def test_remove_duplicates(self):
        p = DedupPipeline()
        item1 = DataItem("test", {"title": "A", "url": "/1"})
        item2 = DataItem("test", {"title": "A", "url": "/1"})  # 重复
        item3 = DataItem("test", {"title": "B", "url": "/2"})   # 不同

        assert p.process_item(item1) is not None
        assert p.process_item(item2) is None  # 应被去重
        assert p.process_item(item3) is not None

    def test_keep_first_occurrence(self):
        p = DedupPipeline(key_fields=["name"])
        item1 = DataItem("t", {"name": "X", "value": 1})
        item2 = DataItem("t", {"name": "X", "value": 2})  # name 相同
        item3 = DataItem("t", {"name": "Y", "value": 3})

        r1 = p.process_item(item1)
        r2 = p.process_item(item2)
        r3 = p.process_item(item3)

        assert r1 is not None
        assert r2 is None
        assert r3 is not None


class TestCleanPipeline:
    def test_clean_rules(self):
        p = CleanPipeline()

        def strip(s):
            return str(s).strip().upper()

        p.add_rule("name", strip)
        item = DataItem("t", {"name": " hello ", "age": 25})
        result = p.process_item(item)
        assert result.data["name"] == "HELLO"


class TestFilterPipeline:
    def test_filter_conditions(self):
        p = FilterPipeline()
        p.add_condition("price", "gt", 100)

        assert p.process_item(DataItem("t", {"price": 150})) is not None
        assert p.process_item(DataItem("t", {"price": 50})) is None

    def test_filter_contains(self):
        p = FilterPipeline()
        p.add_condition("title", "contains", "手机")

        assert p.process_item(DataItem("t", {"title": "苹果手机壳"})) is not None
        assert p.process_item(DataItem("t", {"title": "电脑包"})) is None


class TestDataPipelineManager:
    def test_chain_processing(self):
        mgr = DataPipelineManager()
        mgr.add_pipeline(DedupPipeline(key_fields=["name"]))
        mgr.add_pipeline(FilterPipeline())

        items = [
            DataItem("t", {"name": "A", "score": 90}),
            DataItem("t", {"name": "A", "score": 80}),  # 重复 name
            DataItem("t", {"name": "B", "score": 70}),
        ]
        mgr.pipelines[1].add_condition("score", "gt", 60)

        results = mgr.process_batch(items)
        # A/90 和 B/70 都通过 score>60 过滤
        assert len(results) == 2


class TestHtmlParser:
    def test_extract_links(self, sample_html):
        links = HtmlParser.extract_links(sample_html, "https://test.com")
        assert any("/page1" in l for l in links)
        assert any("/page2" in l for l in links)

    def test_extract_meta(self, sample_html):
        meta = HtmlParser.extract_meta(sample_html)
        assert meta["title"] == "测试页面"

    def test_extract_table(self, sample_html):
        rows = HtmlParser.extract_table(sample_html)
        assert len(rows) == 2
        assert rows[0]["商品"] == "商品A"
        assert rows[0]["价格"] == "99"
