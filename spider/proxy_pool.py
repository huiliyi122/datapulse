"""
代理池模块

功能:
- 多种代理来源：手动列表 / 文件加载 / 免费API
- 自动健康检查：定期验证代理可用性
- 智能轮换：轮询 + 随机 + 加权（低延迟优先）
- 自动剔除：失败次数超阈值自动移除

Usage:
    pool = ProxyPool(["http://1.2.3.4:8080", "http://5.6.7.8:3128"])
    pool.validate_all()

    proxy = pool.get_proxy()   # 获取一个可用代理
    pool.report_result(proxy, success=True)  # 上报使用结果
"""
import asyncio
import json
import random
import threading
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class Proxy:
    """代理实体"""
    url: str
    protocol: str = "http"
    host: str = ""
    port: int = 8080
    username: str = ""
    password: str = ""

    # 运行时状态
    alive: bool = True
    latency: float = 0.0          # 响应延迟（秒）
    fail_count: int = 0           # 连续失败次数
    success_count: int = 0        # 成功次数
    last_used: float = 0.0        # 最后使用时间戳
    last_checked: float = 0.0     # 最后健康检查时间戳

    def __post_init__(self):
        if self.url and not self.host:
            self._parse_url()

    def _parse_url(self):
        """从 URL 解析代理信息"""
        # 格式: protocol://user:pass@host:port
        url = self.url
        for proto in ("socks5://", "https://", "http://"):
            if url.startswith(proto):
                self.protocol = proto.rstrip("://")
                url = url[len(proto):]
                break

        if "@" in url:
            auth, url = url.split("@", 1)
            if ":" in auth:
                self.username, self.password = auth.split(":", 1)

        if ":" in url:
            self.host, port_str = url.rsplit(":", 1)
            self.port = int(port_str)
        else:
            self.host = url

    def __repr__(self):
        status = "✓" if self.alive else "✗"
        return f"<Proxy({status}) {self.protocol}://{self.host}:{self.port} latency={self.latency:.1f}s>"


class ProxyPool:
    """
    代理池

    Attributes:
        max_fail: 连续失败多少次后标记为不可用（默认 3）
        health_interval: 健康检查间隔秒数（默认 300）
        strategy: 选择策略 "round_robin" / "random" / "weighted"（默认 "weighted"）
    """

    def __init__(
        self,
        proxies: list[str] = None,
        max_fail: int = 3,
        health_interval: int = 300,
        strategy: str = "weighted",
    ):
        self._proxies: list[Proxy] = []
        self._index = 0
        self._lock = threading.Lock()
        self.max_fail = max_fail
        self.health_interval = health_interval
        self.strategy = strategy

        if proxies:
            for p in proxies:
                self.add_proxy(p)

    # -------------------- 增删 --------------------

    def add_proxy(self, proxy: str | Proxy):
        """添加代理"""
        if isinstance(proxy, str):
            proxy = Proxy(url=proxy)
        with self._lock:
            if not any(p.url == proxy.url for p in self._proxies):
                self._proxies.append(proxy)

    def remove_proxy(self, proxy: Proxy):
        """移除代理"""
        with self._lock:
            if proxy in self._proxies:
                self._proxies.remove(proxy)

    def load_from_file(self, filepath: str):
        """从文件加载代理列表（每行一个）"""
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    self.add_proxy(line)

    def load_from_json(self, filepath: str):
        """从 JSON 文件加载代理"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    url = item if isinstance(item, str) else item.get("url", "")
                    if url:
                        self.add_proxy(url)

    # -------------------- 选择 --------------------

    def get_proxy(self) -> Optional[Proxy]:
        """获取一个可用代理"""
        alive = self.get_alive()
        if not alive:
            return None

        if self.strategy == "weighted":
            return self._weighted_choice(alive)
        elif self.strategy == "random":
            return random.choice(alive)
        else:  # round_robin
            with self._lock:
                p = alive[self._index]
                p.last_used = time.time()
                self._index = (self._index + 1) % len(alive)
                return p

    def _weighted_choice(self, proxies: list[Proxy]) -> Proxy:
        """加权选择：延迟低的优先"""
        total_weight = 0
        for p in proxies:
            if p.latency > 0:
                total_weight += 1.0 / p.latency
            else:
                total_weight += 1.0  # 从未用过，权重 1

        r = random.uniform(0, total_weight)
        cumulative = 0
        for p in proxies:
            weight = (1.0 / p.latency) if p.latency > 0 else 1.0
            cumulative += weight
            if r <= cumulative:
                p.last_used = time.time()
                return p

        return proxies[-1]

    # -------------------- 健康检查 --------------------

    async def validate_proxy(self, proxy: Proxy, test_url: str = "http://httpbin.org/ip", timeout: int = 10) -> bool:
        """验证单个代理是否可用（异步 aiohttp）"""
        import aiohttp

        try:
            start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    proxy=proxy.url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status == 200:
                        proxy.alive = True
                        proxy.latency = time.time() - start
                        proxy.last_checked = time.time()
                        proxy.fail_count = 0
                        return True
        except Exception:
            pass

        proxy.alive = False
        proxy.last_checked = time.time()
        return False

    async def validate_all(self, test_url: str = "http://httpbin.org/ip"):
        """验证所有代理（异步并发）"""
        tasks = [self.validate_proxy(p, test_url) for p in self._proxies]
        await asyncio.gather(*tasks, return_exceptions=True)

    # -------------------- 结果上报 --------------------

    def report_result(self, proxy: Proxy, success: bool, latency: float = 0):
        """上报代理使用结果（用于动态调整）"""
        if success:
            proxy.success_count += 1
            proxy.fail_count = 0
            if latency > 0:
                proxy.latency = (proxy.latency * 0.7 + latency * 0.3)  # 指数平均
        else:
            proxy.fail_count += 1
            if proxy.fail_count >= self.max_fail:
                proxy.alive = False

    # -------------------- 查询 --------------------

    def get_alive(self) -> list[Proxy]:
        """获取所有存活代理"""
        with self._lock:
            return [p for p in self._proxies if p.alive]

    @property
    def all(self) -> list[Proxy]:
        return list(self._proxies)

    @property
    def alive_count(self) -> int:
        return len(self.get_alive())

    def stats(self) -> dict:
        """代理池统计"""
        alive = self.get_alive()
        if alive:
            avg_latency = sum(p.latency for p in alive) / len(alive)
        else:
            avg_latency = 0
        return {
            "total": len(self._proxies),
            "alive": len(alive),
            "avg_latency": round(avg_latency, 3),
            "strategy": self.strategy,
        }
