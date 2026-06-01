"""测试数据分析引擎"""
import pandas as pd
import pytest

from backend.analysis import (
    DataCleaner, DataAnalyzer, TextAnalyzer, generate_insights,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "name": ["  Alice  ", "Bob", "Charlie", None],
        "age": [25, 30, None, 35],
        "score": [85.5, 90.0, 78.3, 999999.0],  # 最后一个明显异常
        "text": ["product A review", "product B review", "product C review", ""],
    })


class TestDataCleaner:
    def test_clean_text(self):
        result = DataCleaner.clean_text("  Hello   World!  ")
        assert "Hello" in result
        assert "World" in result

    def test_clean_phone(self):
        assert DataCleaner.clean_phone("138-1234-5678") == "13812345678"
        assert DataCleaner.clean_phone("12345") is None

    def test_clean_price(self):
        assert DataCleaner.clean_price("¥99.99") == 99.99
        assert DataCleaner.clean_price(50) == 50.00

    def test_fill_missing(self, sample_df):
        result = DataCleaner.fill_missing(sample_df, strategy="mean")
        assert result["age"].isnull().sum() == 0

    def test_remove_outliers(self, sample_df):
        result = DataCleaner.remove_outliers(sample_df, "score", threshold=0.5)
        assert len(result) < len(sample_df)  # 异常值行被移除


class TestDataAnalyzer:
    def test_summary(self, sample_df):
        analyzer = DataAnalyzer(sample_df)
        result = analyzer.summary()
        assert result["rows"] == 4
        assert result["columns"] == 4
        assert result["null_count"] == 2

    def test_describe_column(self, sample_df):
        analyzer = DataAnalyzer(sample_df)
        desc = analyzer.describe_column("age")
        assert desc["missing"] == 1
        assert desc["mean"] > 0


class TestTextAnalyzer:
    def test_word_frequency(self):
        analyzer = TextAnalyzer()
        result = analyzer.word_frequency(["我 爱 编程", "编程 是 好 的"])
        assert len(result) > 0

    def test_sentiment(self):
        analyzer = TextAnalyzer()
        score = analyzer.sentiment_score("质量非常好，推荐购买")
        assert score > 0.5  # 正面情感


def test_generate_insights(sample_df):
    analyzer = DataAnalyzer(sample_df)
    insights = generate_insights(analyzer)
    assert len(insights) >= 2
