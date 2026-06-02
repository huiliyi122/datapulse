# DataPulse - pipelines
"""
数据采集 - 数据处理管道
支持数据清洗、去重、存储（CSV/JSON/数据库）
"""
import csv
import html as _html
import json
import os
import re as _re
import sqlite3
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Any, Optional

import pandas as pd
try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None  # MongoDB 可选依赖


class DataItem:
    """数据项封装"""

    def __init__(self, name: str, data: dict, source_url: str = ""):
        self.name = name
        self.data = data
        self.source_url = source_url
        self.created_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "data": self.data,
            "source_url": self.source_url,
            "created_at": self.created_at.isoformat(),
        }


class BasePipeline(ABC):
    """管道基类"""

    @abstractmethod
    def process_item(self, item: DataItem) -> Optional[DataItem]:
        """处理单个数据项，返回None表示丢弃"""
        pass


class DedupPipeline(BasePipeline):
    """数据去重管道"""

    def __init__(self, key_fields: list[str] = None):
        self.seen = set()
        self.key_fields = key_fields or ["title", "url"]

    def _make_key(self, item: DataItem) -> str:
        parts = []
        for field in self.key_fields:
            val = item.data.get(field, "")
            parts.append(str(val))
        return "|".join(parts)

    def process_item(self, item: DataItem) -> Optional[DataItem]:
        key = self._make_key(item)
        if key in self.seen:
            return None
        self.seen.add(key)
        return item


class CleanPipeline(BasePipeline):
    """数据清洗管道"""

    def __init__(self):
        self._rules = []

    def add_rule(self, field: str, cleaner):
        """注册清洗规则"""
        self._rules.append((field, cleaner))

    def process_item(self, item: DataItem) -> Optional[DataItem]:
        for field, cleaner in self._rules:
            if field in item.data:
                item.data[field] = cleaner(item.data[field])
        return item


class FilterPipeline(BasePipeline):
    """数据过滤管道"""

    def __init__(self):
        self._conditions = []

    def add_condition(self, field: str, op: str, value: Any):
        """添加过滤条件
        op: gt/lt/eq/ne/contains/regex
        """
        self._conditions.append((field, op, value))

    def process_item(self, item: DataItem) -> Optional[DataItem]:
        for field, op, value in self._conditions:
            actual = item.data.get(field)
            if actual is None:
                return None

            if op == "gt" and not (actual > value):
                return None
            elif op == "lt" and not (actual < value):
                return None
            elif op == "eq" and not (actual == value):
                return None
            elif op == "ne" and not (actual != value):
                return None
            elif op == "contains" and value not in str(actual):
                return None
            elif op == "regex" and not _re.search(str(value), str(actual)):
                return None

        return item


class CsvExportPipeline(BasePipeline):
    """CSV导出管道"""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        self._files = {}

    def process_item(self, item: DataItem) -> Optional[DataItem]:
        os.makedirs(self.output_dir, exist_ok=True)
        filepath = os.path.join(
            self.output_dir, f"{item.name}.csv"
        )

        file_exists = os.path.exists(filepath)
        mode = "a" if file_exists else "w"
        with open(filepath, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=item.data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(item.data)

        return item

class JsonExportPipeline(BasePipeline):
    """JSON导出管道"""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        self._all = {}  # 累积全部数据，close 时一次性写入

    def process_item(self, item: DataItem) -> Optional[DataItem]:
        os.makedirs(self.output_dir, exist_ok=True)
        if item.name not in self._all:
            self._all[item.name] = []
        self._all[item.name].append(item.to_dict())
        return item

    def close(self):
        """关闭管道，写入全部数据"""
        for name, items in self._all.items():
            filepath = os.path.join(self.output_dir, f"{name}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)


class MongoPipeline(BasePipeline):
    """MongoDB存储管道"""

    def __init__(self, uri: str, db: str, collection: str):
        if MongoClient is None:
            raise ImportError("需要安装 pymongo: pip install pymongo>=4.5")
        self.client = MongoClient(uri)
        self.collection = self.client[db][collection]

    def process_item(self, item: DataItem) -> Optional[DataItem]:
        self.collection.insert_one(item.to_dict())
        return item

    def close(self):
        self.client.close()


class DataPipelineManager:
    """
    数据管道管理器
    支持链式处理：清洗 → 去重 → 过滤 → 导出
    """

    def __init__(self):
        self.pipelines: list[BasePipeline] = []
        self._stats = {"input": 0, "output": 0, "dropped": 0}

    def add_pipeline(self, pipeline: BasePipeline):
        """注册管道"""
        self.pipelines.append(pipeline)

    def process(self, item: DataItem) -> Optional[DataItem]:
        """执行管道链处理"""
        self._stats["input"] += 1
        for pipeline in self.pipelines:
            item = pipeline.process_item(item)
            if item is None:
                self._stats["dropped"] += 1
                return None

        self._stats["output"] += 1
        return item

    def process_batch(self, items: list[DataItem]) -> list[DataItem]:
        """批量处理"""
        return [
            processed for item in items
            if (processed := self.process(item)) is not None
        ]

    def close(self):
        """关闭所有管道"""
        for pipeline in self.pipelines:
            if hasattr(pipeline, "close"):
                pipeline.close()

    def stats(self) -> dict:
        return {**self._stats, "pipelines": len(self.pipelines)}


class AnalysisExporter:
    """数据分析导出工具"""

    @staticmethod
    def to_excel(
        data: list[dict],
        filepath: str,
        sheet_name: str = "Sheet1"
    ):
        """导出为Excel"""
        df = pd.DataFrame(data)
        df.to_excel(filepath, sheet_name=sheet_name, index=False)
        print(f"[导出] Excel已保存: {filepath}")

    @staticmethod
    def to_sqlite(
        data: list[dict],
        db_path: str,
        table_name: str
    ):
        """导出到SQLite数据库"""
        conn = sqlite3.connect(db_path)
        df = pd.DataFrame(data)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()
        print(f"[导出] SQLite已保存: {db_path}.{table_name}")

    @staticmethod
    def generate_report(
        data: list[dict],
        title: str = "数据采集报告",
        output_path: str = "./report.html"
    ):
        """生成HTML数据报告"""
        df = pd.DataFrame(data)

        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head><meta charset="UTF-8">
        <title>{title}</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; max-width: 1200px;
                   margin: 0 auto; padding: 20px; background: #f5f7fa; }}
            h1 {{ color: #303133; border-bottom: 2px solid #409eff;
                 padding-bottom: 12px; }}
            table {{ border-collapse: collapse; width: 100%;
                    background: #fff; border-radius: 8px;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
            th {{ background: #409eff; color: #fff; padding: 12px 16px;
                 text-align: left; }}
            td {{ padding: 10px 16px; border-bottom: 1px solid #ebeef5; }}
            tr:hover {{ background: #f0f7ff; }}
            .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
            .stat-card {{ background: #fff; border-radius: 8px;
                         padding: 20px 24px; flex: 1;
                         box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
            .stat-num {{ font-size: 28px; font-weight: 600; color: #409eff; }}
        </style>
        </head>
        <body>
        <h1>{title}</h1>
        <div class="stats">
            <div class="stat-card">
                <div>数据总量</div>
                <div class="stat-num">{len(df)}</div>
            </div>
            <div class="stat-card">
                <div>字段数量</div>
                <div class="stat-num">{len(df.columns)}</div>
            </div>
            <div class="stat-card">
                <div>生成时间</div>
                <div class="stat-num" style="font-size:16px">
                    {datetime.now().strftime('%Y-%m-%d %H:%M')}
                </div>
            </div>
        </div>
        <table>
            <thead><tr>"""
        for col in df.columns:
            html += f"<th>{col}</th>"
        html += "</tr></thead><tbody>"

        for _, row in df.head(100).iterrows():
            html += "<tr>"
            for val in row:
                html += f"<td>{_html.escape(str(val))}</td>"
            html += "</tr>"

        html += f"""
        </tbody></table>
        <p style="color:#909399;margin-top:12px;">
            共 {len(df)} 条记录，仅展示前100条
        </p>
        </body></html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[报告] HTML报告已生成: {output_path}")
