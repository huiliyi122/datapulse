"""
AI 辅助 JS 逆向引擎 (实验性)

WARNING: 实验性功能，成功率取决于目标网站的混淆程度。
简单签名（Base64/MD5/明文拼接）成功率较高，
大厂混淆代码（JSVMP/Obfuscator）基本无解。

Usage:
    from spider import JSReverseEngineer

    engine = JSReverseEngineer(provider="ollama")
    result = await engine.analyze("https://example.com/api", "_sign")
    if result.found and result.python_code:
        exec(result.python_code)
        signature = sign({"page": "1"})
"""
import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReverseResult:
    """逆向分析结果"""
    url: str
    target_param: str = ""
    found: bool = False
    confidence: str = "low"         # low / medium / high
    js_file_url: str = ""           # 签名 JS 文件 URL
    js_code: str = ""               # 原始 JS 代码片段
    python_code: str = ""           # 生成的 Python 代码
    explanation: str = ""           # LLM 分析说明
    error: str = ""                 # 失败原因

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "target_param": self.target_param,
            "found": self.found,
            "confidence": self.confidence,
            "python_code": self.python_code,
            "explanation": self.explanation,
            "error": self.error,
        }


class JSReverseEngineer:
    """
    AI 辅助 JS 逆向引擎

    工作流程:
    1. 用 Playwright 打开页面，拦截所有网络请求
    2. 找到包含目标参数的请求
    3. 搜索生成该参数的 JS 代码
    4. 把 JS 发给 LLM 翻译成 Python

    限制:
    - 对简单签名有效（Base64/MD5/字符串拼接/时间戳）
    - 对大厂混淆 JS 无效（JSVMP/Obfuscator/eval 嵌套）
    - 依赖 LLM 质量，不同模型结果差异大
    """

    SUPPORTED_PROVIDERS = ["ollama", "openai"]

    def __init__(
        self,
        provider: str = "ollama",
        model: str = None,
        api_key: str = None,
    ):
        self.provider = provider
        self.model = model or {"ollama": "qwen2.5:7b", "openai": "gpt-4o-mini"}.get(provider, "qwen2.5:7b")
        self.api_key = api_key

        self._browser = None
        self._context = None
        self._playwright = None
        self._captured_scripts: list[str] = []

    # ============================================================
    # 核心方法
    # ============================================================

    async def analyze(self, url: str, target_param: str = "_sign", timeout: int = 30) -> ReverseResult:
        """
        分析目标 URL 的签名参数

        Args:
            url: 包含签名参数的目标 URL
            target_param: 目标签名参数名（如 _sign, token, x-bogus）
            timeout: 页面加载超时
        """
        result = ReverseResult(url=url, target_param=target_param)

        try:
            # Step 1: 启动浏览器，拦截请求
            await self._start_browser()
            page = await self._context.new_page()

            # 拦截所有 JS 文件
            self._captured_scripts = []
            page.on("response", self._on_response)

            await page.goto(url, wait_until="networkidle", timeout=timeout * 1000)
            await asyncio.sleep(2)

            # Step 2: 在页面中搜索签名生成代码
            js_code = await self._search_sign_code(page, target_param)

            if not js_code:
                # 降级：搜索拦截到的 JS 文件
                js_code = self._search_in_captured_scripts(target_param)

            if not js_code:
                result.error = f"未找到 {target_param} 的生成代码"
                return result

            result.found = True
            result.js_code = js_code[:8000]

            # Step 3: 用 LLM 翻译 JS -> Python
            python_code, explanation = await self._translate_js(result.js_code, target_param)

            result.python_code = python_code
            result.explanation = explanation
            result.confidence = self._estimate_confidence(js_code)

            await page.close()

        except Exception as e:
            result.error = str(e)
        finally:
            await self._stop_browser()

        return result

    # ============================================================
    # 浏览器操作
    # ============================================================

    async def _start_browser(self):
        """启动 Playwright"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("需要安装 playwright: pip install playwright && playwright install chromium")

        self._playwright = await async_playwright().__aenter__()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context()

    async def _stop_browser(self):
        """关闭浏览器"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.__aexit__(None, None, None)

    async def _on_response(self, response):
        """拦截 JS 文件"""
        url = response.url
        content_type = response.headers.get("content-type", "")
        if url.endswith(".js") or "javascript" in content_type:
            try:
                text = await response.text()
                self._captured_scripts.append(text)
            except Exception:
                pass

    # ============================================================
    # 签名搜索
    # ============================================================

    async def _search_sign_code(self, page, target_param: str) -> Optional[str]:
        """在页面执行环境中搜索签名生成代码"""
        search_script = f"""
        () => {{
            const keyword = "{target_param}";
            const results = [];

            // 策略1: 查找赋值语句
            document.querySelectorAll("script").forEach(s => {{
                if (s.src || !s.textContent) return;
                const lines = s.textContent.split("\\n");
                lines.forEach((line, i) => {{
                    if (line.includes(keyword) && line.includes("=")) {{
                        const start = Math.max(0, i - 3);
                        const end = Math.min(lines.length, i + 10);
                        results.push(lines.slice(start, end).join("\\n"));
                    }}
                }});
            }});

            // 策略2: 查找函数定义
            const allScripts = Array.from(document.scripts)
                .filter(s => s.src && s.src.includes(".js"))
                .map(s => s.src);

            return JSON.stringify({{
                inline: results.slice(0, 3),
                external: allScripts.slice(0, 5)
            }});
        }}
        """

        try:
            raw = await page.evaluate(search_script)
            data = json.loads(raw)

            # 优先内联代码
            for chunk in data.get("inline", []):
                if target_param in chunk:
                    return chunk

            return None
        except Exception:
            return None

    def _search_in_captured_scripts(self, target_param: str) -> Optional[str]:
        """在拦截到的 JS 文件中搜索"""
        for script in self._captured_scripts:
            idx = script.find(target_param)
            if idx == -1:
                continue

            # 截取上下文（前后各 500 字符）
            start = max(0, idx - 500)
            end = min(len(script), idx + 2000)
            return script[start:end]

        return None

    # ============================================================
    # LLM 翻译
    # ============================================================

    async def _translate_js(self, js_code: str, target_param: str) -> tuple[str, str]:
        """把 JS 签名代码翻译成 Python"""
        prompt = f"""你是一个 JS 逆向专家。以下是生成「{target_param}」签名参数的 JavaScript 代码。

请做两件事：
1. 如果代码简单（Base64/MD5/字符串拼接），把它翻译成等效的 Python 函数
2. 如果太复杂或依赖浏览器 API，说明为什么无法翻译

JS 代码:
```javascript
{js_code[:5000]}
```

返回 JSON 格式（不要其他内容）：
```json
{{
  "translatable": true,
  "python_code": "import hashlib\\nimport time\\n\\ndef sign(params):\\n    ...",
  "explanation": "签名使用 MD5 + 时间戳拼接，可以直接翻译"
}}
```

或如果无法翻译：
```json
{{
  "translatable": false,
  "python_code": "",
  "explanation": "代码使用了 window.crypto.subtle，需要浏览器原生API，无法翻译"
}}
```"""

        try:
            response = await self._call_llm(prompt)

            # 解析 JSON
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("python_code", ""), data.get("explanation", "")

            return "", "LLM 响应格式异常"
        except Exception as e:
            return "", f"LLM 调用失败: {e}"

    # ============================================================
    # 评估 & LLM
    # ============================================================

    @staticmethod
    def _estimate_confidence(js_code: str) -> str:
        """根据代码复杂度估计成功率"""
        red_flags = [
            "eval(", "Function(", "constructor(",   # 动态执行
            "window.crypto", "navigator.",          # 浏览器 API
            "\\u", "\\\\x",                         # Unicode 编码
        ]
        score = sum(1 for flag in red_flags if flag in js_code)

        if score >= 3:
            return "low"
        elif score >= 1:
            return "medium"
        else:
            return "high"

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM（复用 ai_parser 的模式）"""
        if self.provider == "ollama":
            return await self._call_ollama(prompt)
        else:
            return await self._call_openai(prompt)

    async def _call_ollama(self, prompt: str) -> str:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False,
                      "options": {"temperature": 0.1, "num_predict": 2048}},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                data = await resp.json()
                return data.get("response", "")

    async def _call_openai(self, prompt: str) -> str:
        import aiohttp
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                json={"model": self.model, "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.1, "max_tokens": 2048},
                headers=headers, timeout=30,
            ) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]


# ============================================================
# 快捷 API
# ============================================================

async def try_reverse(url: str, param: str = "_sign", provider: str = "ollama") -> dict:
    """
    一键逆向分析（实验性）

    Usage:
        result = await try_reverse("https://example.com/api/data", "_sign")
        print(result["confidence"])  # low / medium / high
    """
    engine = JSReverseEngineer(provider=provider)
    result = await engine.analyze(url, param)
    return result.to_dict()
