# DataPulse - analysis
"""
数据分析模块 - 数据清洗、统计分析和可视化
"""
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Optional

import jieba
import jieba.analyse
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler


class DataCleaner:
    """数据清洗器"""

    @staticmethod
    def clean_text(text: str) -> str:
        """清洗文本：去空格、特殊字符、统一小写"""
        text = re.sub(r"\s+", " ", text.strip())
        text = re.sub(r"[^\w\u4e00-\u9fff\s]", "", text)
        return text

    @staticmethod
    def clean_phone(phone: str) -> Optional[str]:
        """清洗手机号"""
        phone = re.sub(r"\D", "", phone)
        if len(phone) == 11 and phone.startswith("1"):
            return phone
        return None

    @staticmethod
    def clean_price(price: Any) -> Optional[float]:
        """清洗价格数据"""
        if isinstance(price, (int, float)):
            return round(float(price), 2)
        if isinstance(price, str):
            price = re.sub(r"[^\d.]", "", price)
            try:
                return round(float(price), 2)
            except ValueError:
                return None
        return None

    @staticmethod
    def clean_date(date_str: str, formats: list = None) -> Optional[str]:
        """清洗日期格式"""
        if formats is None:
            formats = [
                "%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日",
                "%Y.%m.%d", "%Y-%m-%d %H:%M:%S",
            ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                continue
        return None

    @staticmethod
    def fill_missing(df: pd.DataFrame, strategy: str = "mean") -> pd.DataFrame:
        """填充缺失值"""
        df = df.copy()
        for col in df.columns:
            if df[col].isnull().sum() == 0:
                continue

            if df[col].dtype in ["float64", "int64"]:
                if strategy == "mean":
                    df[col].fillna(df[col].mean(), inplace=True)
                elif strategy == "median":
                    df[col].fillna(df[col].median(), inplace=True)
                elif strategy == "zero":
                    df[col].fillna(0, inplace=True)
                elif strategy == "ffill":
                    df[col].ffill(inplace=True)
            else:
                df[col].fillna(df[col].mode().iloc[0]
                               if not df[col].mode().empty else "",
                               inplace=True)
        return df

    @staticmethod
    def remove_outliers(
        df: pd.DataFrame, column: str, threshold: float = 3.0
    ) -> pd.DataFrame:
        """基于Z-Score去除异常值"""
        z_scores = np.abs(
            (df[column] - df[column].mean()) / df[column].std()
        )
        return df[z_scores < threshold]


class TextAnalyzer:
    """文本分析器"""

    @staticmethod
    def word_frequency(
        texts: list[str], top_n: int = 20
    ) -> list[dict]:
        """词频统计"""
        words = []
        for text in texts:
            words.extend(jieba.lcut(text))

        counter = Counter(words)
        # 过滤停用词（单字词和标点）
        filtered = [
            {"word": w, "count": c}
            for w, c in counter.most_common(top_n * 3)
            if len(w) > 1
        ]
        return filtered[:top_n]

    @staticmethod
    def extract_keywords(
        texts: list[str],
        top_n: int = 10,
        algorithm: str = "tfidf"
    ) -> list[dict]:
        """关键词提取"""
        combined = " ".join(texts)

        if algorithm == "tfidf":
            keywords = jieba.analyse.extract_tags(
                combined, topK=top_n, withWeight=True
            )
        elif algorithm == "textrank":
            keywords = jieba.analyse.textrank(
                combined, topK=top_n, withWeight=True
            )
        else:
            raise ValueError(f"不支持的算法: {algorithm}")

        return [
            {"keyword": kw, "weight": round(w, 4)}
            for kw, w in keywords
        ]

    @staticmethod
    def sentiment_score(text: str) -> float:
        """简单情感分析（基于情感词典）"""
        positive_words = {
            "好", "棒", "优秀", "满意", "喜欢", "推荐",
            "赞", "漂亮", "实惠", "方便", "快捷", "值得",
        }
        negative_words = {
            "差", "烂", "糟糕", "失望", "垃圾", "坑",
            "贵", "慢", "差劲", "后悔", "质量差", "退货",
        }

        words = set(jieba.lcut(text))
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        total = pos_count + neg_count

        if total == 0:
            return 0.5  # 中性

        return round(pos_count / total, 2)


class DataAnalyzer:
    """数据分析引擎"""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def summary(self) -> dict:
        """数据概览"""
        return {
            "rows": len(self.df),
            "columns": len(self.df.columns),
            "memory_mb": round(
                self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2
            ),
            "null_count": int(self.df.isnull().sum().sum()),
            "duplicate_count": int(self.df.duplicated().sum()),
            "column_types": {
                str(k): str(v)
                for k, v in self.df.dtypes.items()
            },
        }

    def describe_column(self, column: str) -> dict:
        """单列统计描述"""
        if self.df[column].dtype in ["float64", "int64"]:
            desc = self.df[column].describe()
            return {
                "count": int(desc["count"]),
                "mean": round(desc["mean"], 2),
                "std": round(desc["std"], 2),
                "min": round(desc["min"], 2),
                "25%": round(desc["25%"], 2),
                "50%": round(desc["50%"], 2),
                "75%": round(desc["75%"], 2),
                "max": round(desc["max"], 2),
                "missing": int(self.df[column].isnull().sum()),
            }
        else:
            value_counts = self.df[column].value_counts().head(10)
            return {
                "unique": int(self.df[column].nunique()),
                "top": value_counts.index[0] if len(value_counts) > 0 else None,
                "top_freq": int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                "missing": int(self.df[column].isnull().sum()),
                "top_values": [
                    {"value": str(k), "count": int(v)}
                    for k, v in value_counts.items()
                ],
            }

    def correlation_matrix(self) -> list[list]:
        """数值列相关性矩阵"""
        numeric_df = self.df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 2:
            return []

        corr = numeric_df.corr().round(4)
        return {
            "columns": list(corr.columns),
            "data": corr.values.tolist(),
        }

    def time_series_analysis(
        self, date_col: str, value_col: str, freq: str = "D"
    ) -> pd.DataFrame:
        """时间序列分析"""
        df = self.df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df.set_index(date_col, inplace=True)
        return df.resample(freq)[value_col].agg(["sum", "mean", "count"])

    def clustering(
        self, columns: list[str], n_clusters: int = 3
    ) -> list[int]:
        """KMeans聚类分析"""
        data = self.df[columns].dropna()
        scaler = StandardScaler()
        scaled = scaler.fit_transform(data)

        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
        )
        return kmeans.fit_predict(scaled).tolist()


def generate_insights(analyzer: DataAnalyzer) -> list[str]:
    """自动生成数据洞察"""
    insights = []
    summary = analyzer.summary()

    insights.append(
        f"数据集包含 {summary['rows']} 行 {summary['columns']} 列, "
        f"占用内存 {summary['memory_mb']}MB"
    )

    if summary["null_count"] > 0:
        insights.append(
            f"发现 {summary['null_count']} 个缺失值, "
            f"占比 {summary['null_count'] / (summary['rows'] * summary['columns']) * 100:.1f}%"
        )

    if summary["duplicate_count"] > 0:
        insights.append(
            f"发现 {summary['duplicate_count']} 条重复数据"
        )

    return insights


class ReportGenerator:
    """报告生成器"""

    @staticmethod
    def generate_markdown_report(
        analyzer: DataAnalyzer,
        title: str = "数据分析报告"
    ) -> str:
        """生成Markdown格式报告"""
        summary = analyzer.summary()
        insights = generate_insights(analyzer)

        lines = [
            f"# {title}",
            f"**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 数据概览",
            f"- 记录数: {summary['rows']}",
            f"- 字段数: {summary['columns']}",
            f"- 缺失值: {summary['null_count']}",
            f"- 重复值: {summary['duplicate_count']}",
            f"- 占用内存: {summary['memory_mb']}MB",
            "",
            "## 数据洞察",
        ]
        for i, insight in enumerate(insights, 1):
            lines.append(f"{i}. {insight}")

        lines.extend(["", "## 字段详情"])
        for col in analyzer.df.columns:
            desc = analyzer.describe_column(col)
            lines.append(f"")
            lines.append(f"### {col}")
            for k, v in desc.items():
                if k != "top_values":
                    lines.append(f"- {k}: {v}")

        return "\n".join(lines)
