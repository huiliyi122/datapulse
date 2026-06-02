"""
AI 智能解析器

使用 LLM 自动生成网页数据提取规则，告别手写选择器。

支持:
- OpenAI API / 兼容 API
- 本地 Ollama（免费、无限制）
- 自动生成 CSS Selector + JSON Schema

Usage:
    parser = AIParser(provider="ollama")  # 或用 "openai"
    schema = await parser.infer("https://example.com/products", "提取商品名、价格、评分")
    data = parser.extract(html, schema)
"""
import asyncio
import json
import re

from bs4 import BeautifulSoup


class AIParser:
    """
    基于 LLM 的智能数据提取器

    工作流程:
    1. 获取页面 HTML
    2. 发送给 LLM：「这个页面包含商品列表，请提取每个商品的名称、价格、评分」
    3. LLM 返回 CSS Selector + 字段映射
    4. 自动提取数据

    Usage:
        # 方式一：本地 Ollama (免费)
        parser = AIParser(provider="ollama", model="qwen2.5:7b")

        # 方式二：OpenAI API
        parser = AIParser(provider="openai", api_key="sk-xxx")

        # 推断规则
        schema = await parser.infer(html, "提取所有商品的名字和价格")
        # => {"container": ".product-item", "fields": {"title": ".title a", "price": ".price .current"}}

        # 提取数据
        data = parser.extract(html, schema)
    """

    SUPPORTED_PROVIDERS = ["ollama", "openai", "deepseek", "custom"]

    def __init__(
        self,
        provider: str = "ollama",
        model: str = None,
        api_key: str = None,
        base_url: str = None,
    ):
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"不支持的 provider: {provider}，可选: {self.SUPPORTED_PROVIDERS}")

        self.provider = provider
        self.model = model or {
            "ollama": "qwen2.5:7b",
            "openai": "gpt-4o-mini",
            "deepseek": "deepseek-v4-pro",
            "custom": "default",
        }[provider]
        self.api_key = api_key
        self.base_url = base_url or {
            "deepseek": "https://api.deepseek.com/v1",
        }.get(provider)

    # ============================================================
    # 核心方法
    # ============================================================

    async def infer(self, html_or_url: str, description: str) -> dict:
        """
        从页面推断提取规则

        Args:
            html_or_url: 页面 HTML 文本 或 URL
            description: 自然语言描述「提取所有商品的名字和价格」

        Returns:
            {"container": ".product-list > div", "fields": {"name": ".title", "price": ".price-num"}}
        """
        # 如果是 URL，先爬取
        if html_or_url.startswith(("http://", "https://")):
            html = await self._fetch_url(html_or_url)
        else:
            html = html_or_url

        # 压缩 HTML（只保留结构，去掉大量文本）
        compact = self._compact_html(html)

        # 让 LLM 推断选择器
        prompt = self._build_prompt(compact, description)
        response = await self._call_llm(prompt)
        schema = self._parse_response(response)

        return schema

    def extract(self, html: str, schema: dict) -> list[dict]:
        """
        根据推断出的规则提取数据

        Args:
            html: 页面 HTML
            schema: {"container": ".item", "fields": {"title": ".title", "price": ".price"}}

        Returns:
            [{"title": "iPhone", "price": "5999"}, ...]
        """
        soup = BeautifulSoup(html, "html.parser")

        container_sel = schema.get("container", "body")
        fields = schema.get("fields", {})

        if not fields:
            return []

        # 找到所有容器
        containers = soup.select(container_sel)
        if not containers:
            return []

        results = []
        for el in containers:
            item = {}
            for field_name, selector in fields.items():
                target = el.select_one(selector)
                if target:
                    # 优先取 text，如果是 img 取 src/alt
                    if target.name == "img":
                        item[field_name] = target.get("src", "") or target.get("alt", "")
                    elif target.name == "a":
                        item[field_name] = {
                            "text": target.get_text(strip=True),
                            "href": target.get("href", ""),
                        }
                    else:
                        item[field_name] = target.get_text(strip=True)
                else:
                    item[field_name] = ""
            results.append(item)

        return results

    def infer_sync(self, html: str, description: str) -> dict:
        """同步版本（仅用于同步上下文，异步中请用 await parser.infer()）"""
        return asyncio.run(self.infer(html, description))

    # ============================================================
    # LLM 调用
    # ============================================================

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM API"""
        if self.provider == "ollama":
            return await self._call_ollama(prompt)
        elif self.provider in ("openai", "deepseek", "custom"):
            return await self._call_openai(prompt)
        raise ValueError(f"未知 provider: {self.provider}")

    async def _call_ollama(self, prompt: str) -> str:
        """调用本地 Ollama"""
        import aiohttp

        url = self.base_url or "http://localhost:11434"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 1024},
                },
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Ollama 调用失败: {resp.status} - {await resp.text()}")

                data = await resp.json()
                return data.get("response", "")

    async def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI API"""
        import aiohttp

        url = self.base_url or "https://api.openai.com/v1"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个网页数据提取专家。返回 JSON 格式的选择器规则，不要任何解释。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1024,
                },
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"OpenAI 调用失败: {resp.status} - {await resp.text()}")
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    async def _fetch_url(self, url: str) -> str:
        """快速爬取 URL"""
        import aiohttp

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=30) as resp:
                return await resp.text()

    # ============================================================
    # 工具方法
    # ============================================================

    def _build_prompt(self, html: str, description: str) -> str:
        """构建 LLM 提示词"""
        return f"""分析以下 HTML 代码片段，根据用户需求生成 CSS 选择器提取规则。

用户需求: {description}

HTML 片段:
```html
{html[:6000]}
```

请返回 JSON 格式（不要任何解释，只返回 JSON）：
```json
{{
  "container": "CSS选择器，用于定位每个数据项的父容器",
  "fields": {{
    "字段名1": "CSS选择器",
    "字段名2": "CSS选择器"
  }}
}}
```"""

    def _parse_response(self, response: str) -> dict:
        """解析 LLM 响应，提取 JSON"""
        # 提取 JSON 块
        json_match = re.search(r"\{[\s\S]*\}", response)
        if not json_match:
            return {"container": "", "fields": {}}

        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return {"container": "", "fields": {}}

    @staticmethod
    def _compact_html(html: str) -> str:
        """压缩 HTML：删除 script/style 标签和过长文本"""
        # 删除 script 和 style
        html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
        html = re.sub(r"<style[\s\S]*?</style>", "", html, flags=re.IGNORECASE)

        # 删除注释
        html = re.sub(r"<!--[\s\S]*?-->", "", html)

        # 删除多余空白
        html = re.sub(r"\n\s*\n", "\n", html)
        html = re.sub(r"[ \t]+", " ", html)

        return html


# ============================================================
# 快捷 API
# ============================================================

async def auto_extract(url: str, description: str, provider: str = "ollama") -> list[dict]:
    """
    一键自动提取: 给 URL + 描述，返回结构化数据

    这是 AI 解析的终极简化接口

    Usage:
        data = await auto_extract(
            "https://books.toscrape.com",
            "提取所有书的书名和价格"
        )
        # => [{"书名": "A Light", "价格": "£51.77"}, ...]
    """
    parser = AIParser(provider=provider)
    html = await parser._fetch_url(url)
    schema = await parser.infer(html, description)
    return parser.extract(html, schema)
