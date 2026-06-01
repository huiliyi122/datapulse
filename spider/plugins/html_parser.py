"""
内置解析器插件
"""
import json
import re

from bs4 import BeautifulSoup

from spider.plugin import BaseParser


class HtmlTableParser(BaseParser):
    """通用 HTML 表格解析器"""

    name = "html_table"
    url_pattern = "https?://.*"

    def parse(self, html: str, url: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")

        # 提取标题
        title = soup.title.string.strip() if soup.title else ""

        # 提取所有表格
        tables = []
        for table in soup.find_all("table"):
            headers = [
                th.get_text(strip=True)
                for th in table.select("thead th, tr th")
            ]
            rows = []
            for tr in table.select("tbody tr, tr"):
                cells = tr.select("td")
                if headers and len(cells) == len(headers):
                    row = {}
                    for i, cell in enumerate(cells):
                        row[headers[i]] = cell.get_text(strip=True)
                    rows.append(row)

            if rows:
                tables.append({"headers": headers, "rows": rows})

        # 提取所有链接
        links = [
            {"text": a.get_text(strip=True), "href": a.get("href")}
            for a in soup.find_all("a", href=True)
            if a.get_text(strip=True)
        ][:50]

        return {
            "url": url,
            "title": title,
            "tables": tables,
            "links_count": len(links),
            "links": links[:20],
        }


class JsonApiParser(BaseParser):
    """JSON API 解析器"""

    name = "json_api"
    url_pattern = r"https?://.*/api/.*"

    def parse(self, html: str, url: str) -> dict:
        try:
            data = json.loads(html)
            if isinstance(data, list):
                return {
                    "url": url,
                    "type": "list",
                    "count": len(data),
                    "sample": data[:5],
                    "keys": list(data[0].keys()) if data and isinstance(data[0], dict) else [],
                }
            elif isinstance(data, dict):
                return {
                    "url": url,
                    "type": "object",
                    "keys": list(data.keys()),
                    "sample": {k: str(v)[:200] for k, v in data.items()},
                }
        except (json.JSONDecodeError, Exception):
            pass

        return {"url": url, "type": "unknown", "content": html[:500]}
