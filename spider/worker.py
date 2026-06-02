"""
DataPulse 分布式爬虫 - Worker 执行节点

可独立部署多台机器，连接到同一个 Redis Master

Usage:
    # 单机启动
    python -m spider.worker

    # 多台机器启动（连接到同一个 Redis Master）
    python -m spider.worker --redis redis://192.168.1.100:6379/0 --workers 10
"""
import argparse
import asyncio
import signal
import sys

import logging

from spider.engine import SpiderEngine, CrawlRequest
from spider.browser_engine import PlaywrightEngine, BrowserConfig

logger = logging.getLogger("datapulse.worker")


class SpiderWorker:
    """
    Worker 执行节点

    独立进程，连接到 Redis 获取任务并执行
    可水平扩展：启动更多 Worker 实例即可
    """

    def __init__(
        self,
        worker_id: str = None,
        redis_url: str = "redis://localhost:6379/0",
        engine_type: str = "aiohttp",  # aiohttp / playwright
        use_proxy_pool: bool = False,
    ):
        self.worker_id = worker_id or f"worker-{id(self):04x}"
        self.redis_url = redis_url
        self.engine_type = engine_type
        self.use_proxy_pool = use_proxy_pool
        self._running = False
        self._stats = {"tasks": 0, "success": 0, "failed": 0}

    async def start(self, master=None):
        """启动 Worker，持续消费任务队列"""
        from spider.master import SpiderMaster

        if master is None:
            master = SpiderMaster(self.redis_url)
            await master.connect()

        self._running = True
        logger.info("Worker启动", extra={"worker_id": self.worker_id, "engine": self.engine_type})

        # 初始化引擎
        engine = None
        try:
            if self.engine_type == "playwright":
                engine = PlaywrightEngine(BrowserConfig(stealth=True, headless=True))
                await engine.start()
            else:
                engine = SpiderEngine(concurrent=3)

            while self._running:
                task = await master.get_task(self.worker_id, block=3)
                if task is None:
                    continue

                self._stats["tasks"] += 1
                url = task["url"]

                try:
                    if self.engine_type == "playwright":
                        result = await engine.fetch(url)
                        status = result.status_code
                    else:
                        result = await engine.crawl(CrawlRequest(url=url))
                        status = result.status_code if result else 0

                    if status == 200:
                        self._stats["success"] += 1
                    else:
                        self._stats["failed"] += 1

                    data = {
                        "batch_id": task.get("batch_id"),
                        "url": url,
                        "status": status,
                        "html": result.html[:5000] if result and result.html else "",
                        "error": result.error if result else "URL已重复",
                        "elapsed": result.elapsed if result else 0,
                    }
                    logger.info("爬取完成", extra={"worker_id": self.worker_id, "url": url, "status": status})

                except Exception as e:
                    data = {
                        "batch_id": task.get("batch_id"),
                        "url": url,
                        "status": 0,
                        "error": str(e),
                    }
                    self._stats["failed"] += 1
                    logger.error("爬取失败", extra={"worker_id": self.worker_id, "url": url, "error": str(e)})

                await master.submit_result(data)

        finally:
            if engine is not None:
                if self.engine_type == "playwright":
                    await engine.stop()
                else:
                    await engine.close()
            self._running = False

    def stop(self):
        """优雅停止"""
        self._running = False

    @property
    def stats(self):
        return dict(self._stats)


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="DataPulse Worker 节点")
    parser.add_argument("--redis", default="redis://localhost:6379/0", help="Redis 地址")
    parser.add_argument("--workers", type=int, default=5, help="并发 Worker 数")
    parser.add_argument("--engine", choices=["aiohttp", "playwright"], default="aiohttp", help="爬虫引擎")
    parser.add_argument("--proxy", action="store_true", help="启用代理池")

    args = parser.parse_args()

    async def run():
        workers = []
        for i in range(args.workers):
            w = SpiderWorker(
                worker_id=f"worker-{i:03d}",
                redis_url=args.redis,
                engine_type=args.engine,
                use_proxy_pool=args.proxy,
            )
            workers.append(asyncio.create_task(w.start()))

        signal.signal(signal.SIGINT, lambda sig, frame: None)
        if sys.platform != "win32":
            signal.signal(signal.SIGTERM, lambda sig, frame: None)

        await asyncio.gather(*workers)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Worker已停止（Ctrl+C）")


if __name__ == "__main__":
    main()
