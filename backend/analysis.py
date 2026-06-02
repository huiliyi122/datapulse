# DataPulse - analysis
"""
数据分析模块 - 数据清洗、统计分析和可视化
"""
import math
import re
from collections import Counter
from datetime import datetime
from typing import Any, Optional

import jieba
import jieba.analyse
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def _safe_num(val):
    """将 NaN/Inf 转为 None，避免 JSON 序列化报错"""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return val

def _py_val(v):
    """将 numpy 类型转为 Python 原生类型，确保 JSON 可序列化"""
    if v is None:
        return None
    try:
        if hasattr(v, 'item'):
            raw = v.item()
            if isinstance(raw, float) and (math.isnan(raw) or math.isinf(raw)):
                return None
            return raw
    except Exception:
        pass
    if isinstance(v, (np.integer, np.floating)):
        if isinstance(v, np.floating) and (math.isnan(v) or math.isinf(v)):
            return None
        return float(v) if isinstance(v, np.floating) else int(v)
    return v


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
                    df[col] = df[col].fillna(df[col].mean())
                elif strategy == "median":
                    df[col] = df[col].fillna(df[col].median())
                elif strategy == "zero":
                    df[col] = df[col].fillna(0)
                elif strategy == "ffill":
                    df[col] = df[col].ffill()
            else:
                df[col] = df[col].fillna(df[col].mode().iloc[0]
                                         if not df[col].mode().empty else "")
        return df

    @staticmethod
    def remove_outliers(
        df: pd.DataFrame, column: str, threshold: float = 3.0
    ) -> pd.DataFrame:
        """基于Z-Score去除异常值"""
        if df[column].std() == 0:
            return df  # 常量列，无异常值
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
                "mean": _safe_num(round(desc["mean"], 2)),
                "std": _safe_num(round(desc["std"], 2)),
                "min": _safe_num(round(desc["min"], 2)),
                "25%": _safe_num(round(desc["25%"], 2)),
                "50%": _safe_num(round(desc["50%"], 2)),
                "75%": _safe_num(round(desc["75%"], 2)),
                "max": _safe_num(round(desc["max"], 2)),
                "missing": int(self.df[column].isnull().sum()),
            }
        else:
            value_counts = self.df[column].value_counts().head(10)
            return {
                "unique": int(self.df[column].nunique()),
                "top": _py_val(value_counts.index[0]) if len(value_counts) > 0 else None,
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
        """KMeans聚类分析（NaN 行保留为 None）"""
        data = self.df[columns].dropna()
        if len(data) == 0:
            return [None] * len(self.df)
        scaler = StandardScaler()
        scaled = scaler.fit_transform(data)

        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=42,
            n_init=10,
        )
        labels = [None] * len(self.df)
        for i, idx in enumerate(data.index):
            labels[idx] = int(kmeans.fit_predict(scaled)[i])
        return labels


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
    """报告生成器 — 生成精美的 HTML 数据分析报告"""

    @staticmethod
    def generate_html_report(analyzer: DataAnalyzer, title: str = "数据分析报告") -> str:
        """生成 HTML 格式报告"""
        summary = analyzer.summary()
        insights = generate_insights(analyzer)
        cols_detail = {col: analyzer.describe_column(col) for col in analyzer.df.columns[:30]}
        corr = analyzer.correlation_matrix()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # --- 概览卡片 ---
        cards = [
            ("总记录", f"{summary['rows']:,}", "#409eff", "📊"),
            ("字段数", f"{summary['columns']}", "#67c23a", "📋"),
            ("缺失值", f"{summary['null_count']}", "#e6a23c" if summary['null_count'] > 0 else "#67c23a", "🔍"),
            ("重复值", f"{summary['duplicate_count']}", "#f56c6c" if summary['duplicate_count'] > 0 else "#67c23a", "📎"),
        ]
        cards_html = "".join(
            f'<div class="card"><div class="card-icon">{icon}</div>'
            f'<div class="card-val" style="color:{color}">{val}</div>'
            f'<div class="card-label">{label}</div></div>'
            for label, val, color, icon in cards
        )

        # --- 字段详情表 ---
        def _nf(v, fmt=".1f"):
            n = _safe_num(v)
            return f"{n:{fmt}}" if n is not None else "N/A"

        field_rows = ""
        for col, desc in cols_detail.items():
            if "mean" in desc:
                detail = f'均值 {_nf(desc.get("mean"))}  |  范围 {_nf(desc.get("min"),".0f")} ~ {_nf(desc.get("max"),".0f")}  |  标准差 {_nf(desc.get("std"))}'
                dtype = "数值"
            else:
                top = desc.get("top") or "-"
                freq = desc.get("top_freq", 0)
                detail = f'Top: {top} ({freq}次)  |  共 {desc.get("unique","?")} 个唯一值'
                dtype = "文本"
            missing = desc.get("missing", 0)
            missing_flag = f'<span style="color:{"#f56c6c" if missing > 0 else "#67c23a"}">{missing}</span>'
            field_rows += f'<tr><td>{col}</td><td><span class="tag tag-{"num" if dtype=="数值" else "cat"}">{dtype}</span></td><td>{desc.get("unique","-")}</td><td>{missing_flag}</td><td>{detail}</td></tr>'

        # --- 相关性矩阵 ---
        corr_html = ""
        if corr and corr.get("columns", []):
            cols = corr["columns"]
            data = corr["data"]
            thead = '<tr><th></th>' + ''.join(f'<th>{c}</th>' for c in cols) + '</tr>'
            tbody = ""
            for i, c in enumerate(cols):
                tbody += f'<tr><th>{c}</th>'
                for j in range(len(cols)):
                    v = data[i][j]
                    color = "#409eff" if v > 0 else "#f56c6c" if v < 0 else "#909399"
                    opacity = min(abs(v), 1.0)
                    tbody += f'<td style="background:rgba({64 if v>0 else 245},{126 if v>0 else 108},{255 if v>0 else 108},{opacity*0.3:.1f});color:{color};font-weight:600">{v:.3f}</td>'
                tbody += '</tr>'
            corr_html = f'<table class="corr-table"><thead>{thead}</thead><tbody>{tbody}</tbody></table>'

        # --- 洞察 ---
        insights_html = ""
        for i, ins in enumerate(insights, 1):
            insights_html += f'<li>{ins}</li>'
        if not insights:
            insights_html = '<li>数据整体质量良好，无异常发现</li>'

        # --- 组装 ---
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f7fa;color:#303133;line-height:1.6}}
.header{{background:linear-gradient(135deg,#409eff,#337ecc);color:#fff;padding:32px 40px;text-align:center}}
.header h1{{font-size:26px;margin-bottom:6px}}
.header p{{font-size:14px;opacity:.85}}
.container{{max-width:1100px;margin:0 auto;padding:24px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:28px}}
.card{{background:#fff;border-radius:12px;padding:20px 24px;text-align:center;box-shadow:0 1px 4px rgba(0,0,0,.04)}}
.card-icon{{font-size:24px;margin-bottom:6px}}
.card-val{{font-size:32px;font-weight:700}}
.card-label{{font-size:13px;color:#909399;margin-top:4px}}
.section{{background:#fff;border-radius:12px;padding:24px 28px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.04)}}
.section h2{{font-size:18px;color:#303133;border-bottom:2px solid #409eff;padding-bottom:10px;margin-bottom:16px}}
.insights{{padding-left:20px}}
.insights li{{padding:6px 0;font-size:14px}}
.insights li::marker{{color:#409eff}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid #ebeef5}}
th{{background:#f5f7fa;font-weight:600;color:#606266;white-space:nowrap}}
tr:hover td{{background:#f0f7ff}}
.tag{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:500}}
.tag-num{{background:#e8f4fd;color:#409eff}}
.tag-cat{{background:#fef0e6;color:#e6a23c}}
.corr-table{{font-size:13px}}
.corr-table th{{text-align:center}}
.corr-table td{{text-align:center}}
.footer{{text-align:center;padding:20px;color:#909399;font-size:12px}}
@media(max-width:768px){{.container{{padding:12px}} .section{{padding:16px}} .card-val{{font-size:24px}}}}
</style></head>
<body>
<div class="header"><h1>{title}</h1><p>生成时间: {now}</p></div>
<div class="container">
<div class="cards">{cards_html}</div>
<div class="section"><h2>数据洞察</h2><ul class="insights">{insights_html}</ul></div>
<div class="section"><h2>字段统计详情</h2><table><thead><tr><th>字段名</th><th>类型</th><th>唯一值</th><th>缺失</th><th>统计详情</th></tr></thead><tbody>{field_rows}</tbody></table></div>
<div class="section"><h2>相关性矩阵</h2>{corr_html if corr_html else '<p style="color:#909399">无足够数值列计算相关性</p>'}</div>
</div>
<div class="footer">DataPulse v0.3.4 — Data Collection & Analysis Platform</div>
</body></html>'''

    @staticmethod
    def generate_markdown_report(analyzer, title="数据分析报告"):
        """兼容旧接口：生成 Markdown 报告"""
        return ReportGenerator.generate_html_report(analyzer, title)
