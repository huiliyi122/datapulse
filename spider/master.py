"""
分布式爬虫 - Master 调度节点

负责:
- 任务分发
- 结果汇总
- 进度监控

通信方式: Redis List 队列 (生产级可换 Kafka/RabbitMQ)

Usage:
    # 启动 Master
    master = SpiderMaster(redis_url="redis://localhost:6379/0")
    tasks = master.create_tasks(["https://example.com/page1", "https://example.com/page2"])
    results = await master.collect_results(timeout=60)
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional


class SpiderMaster:
    """
    分布式爬虫调度节点

    架构:
        Master (分发任务 + 收集结果)
          ├── Redis: 任务队列 + 结果队列
          ├── Worker 1: 爬取节点
          ├── Worker 2: 爬取节点
          └── Worker N: 爬取节点

    队列设计:
        datapulse:tasks     - 待执行任务
        datapulse:results   - 爬取结果
        datapulse:status    - 任务状态 Hash
    """

    TASK_QUEUE = "datapulse:tasks"
    RESULT_QUEUE = "datapulse:results"
    STATUS_PREFIX = "datapulse:status:"

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis = None
        self._running = False
        self._batch_id = None

    async def connect(self):
        """连接 Redis"""
        import redis.asyncio as aioredis
        self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        await self._redis.ping()
        return self

    async def close(self):
        if self._redis:
            await self._redis.close()

    # ============================================================
    # 任务管理
    # ============================================================

    async def create_tasks(
        self,
        urls: list[str],
        batch_id: str = None,
        priority: int = 0,
    ) -> str:
        """
        创建一批爬取任务

        Args:
            urls: 目标 URL 列表
            batch_id: 批次 ID（可选，自动生成）
            priority: 优先级（越大越优先）

        Returns:
            batch_id
        """
        self._batch_id = batch_id or f"batch_{uuid.uuid4().hex[:8]}"

        for url in urls:
            task = {
                "batch_id": self._batch_id,
                "url": url,
                "priority": priority,
                "created_at": datetime.now().isoformat(),
            }
            await self._redis.rpush(self.TASK_QUEUE, json.dumps(task))

        # 记录批次信息
        await self._redis.hset(
            f"{self.STATUS_PREFIX}{self._batch_id}",
            mapping={
                "total": str(len(urls)),
                "completed": "0",
                "failed": "0",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            },
        )

        return self._batch_id

    async def get_task_status(self, batch_id: str) -> dict:
        """查询批次状态"""
        return await self._redis.hgetall(f"{self.STATUS_PREFIX}{batch_id}")

    # ============================================================
    # 结果收集
    # ============================================================

    async def collect_results(
        self,
        batch_id: str = None,
        timeout: int = 60,
        max_results: int = 0,
    ) -> list[dict]:
        """
        收集爬取结果（阻塞，直到完成或超时）

        Returns:
            [{"url": "...", "status": 200, "html": "...", ...}, ...]
        """
        results = []
        deadline = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < deadline:
            # 检查是否还有结果
            raw = await self._redis.lpop(self.RESULT_QUEUE)
            if raw:
                result = json.loads(raw)

                # 过滤批次
                if batch_id and result.get("batch_id") != batch_id:
                    continue

                results.append(result)

                # 更新状态
                if batch_id:
                    status = await self.get_task_status(batch_id)
                    done = int(status.get("completed", 0)) + int(status.get("failed", 0))
                    total = int(status.get("total", 0))

                    if done >= total:
                        break

                if max_results and len(results) >= max_results:
                    break
            else:
                # 短暂等待
                await asyncio.sleep(0.5)

        return results

    # ============================================================
    # Worker 端调用
    # ============================================================

    async def get_task(self, worker_id: str = None, block: int = 5) -> Optional[dict]:
        """Worker 获取下一个任务（阻塞）"""
        raw = await self._redis.blpop(self.TASK_QUEUE, timeout=block)
        if raw:
            task = json.loads(raw[1])
            task["worker_id"] = worker_id
            return task
        return None

    async def submit_result(self, result: dict):
        """Worker 提交结果"""
        result["submitted_at"] = datetime.now().isoformat()
        await self._redis.rpush(self.RESULT_QUEUE, json.dumps(result))

        # 更新批次统计
        batch_id = result.get("batch_id")
        if batch_id:
            if result.get("status") == 200:
                await self._redis.hincrby(f"{self.STATUS_PREFIX}{batch_id}", "completed", 1)
            else:
                await self._redis.hincrby(f"{self.STATUS_PREFIX}{batch_id}", "failed", 1)

    # ============================================================
    # 工具方法
    # ============================================================

    async def queue_length(self) -> int:
        """剩余任务数"""
        return await self._redis.llen(self.TASK_QUEUE)

    async def clear_queues(self):
        """清空所有队列"""
        await self._redis.delete(self.TASK_QUEUE, self.RESULT_QUEUE)


# ============================================================
# 便捷方法
# ============================================================

async def distributed_crawl(
    urls: list[str],
    worker_func: "Callable",
    redis_url: str = "redis://localhost:6379/0",
    concurrent: int = 5,
) -> dict:
    """
    分布式爬取（Master + Worker 一体化便捷方法）

    Args:
        urls: 目标 URL 列表
        worker_func: Worker 函数 async func(url) -> dict
        redis_url: Redis 连接地址
        concurrent: 并发 Worker 数

    Returns:
        {"total": 100, "success": 95, "failed": 5, "results": [...]}
    """
    master = SpiderMaster(redis_url)
    await master.connect()

    batch_id = await master.create_tasks(urls)

    async def worker(wid: str):
        while True:
            task = await master.get_task(wid)
            if task is None:
                break
            try:
                result = await worker_func(task["url"])
                result.update({"batch_id": batch_id, "url": task["url"], "status": 200})
            except Exception as e:
                result = {
                    "batch_id": batch_id,
                    "url": task["url"],
                    "status": 0,
                    "error": str(e),
                }
            await master.submit_result(result)

    # 启动 Worker 协程
    workers = [asyncio.create_task(worker(f"worker-{i}")) for i in range(concurrent)]
    await asyncio.gather(*workers)

    # 收集结果
    results = await master.collect_results(batch_id=batch_id)
    status = await master.get_task_status(batch_id)

    await master.close()

    return {
        "total": int(status.get("total", 0)),
        "success": int(status.get("completed", 0)),
        "failed": int(status.get("failed", 0)),
        "results": results,
    }
