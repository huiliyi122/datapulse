"""
Celery 异步任务 - 爬虫任务调度
"""
import json
import os
import uuid
from datetime import datetime

from celery import Celery

app = Celery(
    "scraper",
    broker=os.environ.get(
        "CELERY_BROKER_URL", "redis://localhost:6379/0"
    ),
    backend=os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    ),
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
)


@app.task(bind=True, max_retries=3)
def run_spider_task(self, task_id: str, urls: list, **kwargs):
    """
    执行爬虫任务
    由 Celery Worker 异步执行
    """
    from spider.engine import SpiderEngine, CrawlRequest, RandomDelayMiddleware
    from spider.pipelines import (
        DataPipelineManager, DataItem,
        DedupPipeline, CleanPipeline, JsonExportPipeline,
    )

    OUTPUT_DIR = "./output"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 初始化爬虫引擎
    engine = SpiderEngine(concurrent=kwargs.get("concurrency", 5))
    engine.add_middleware(RandomDelayMiddleware(
        kwargs.get("min_delay", 0.5),
        kwargs.get("max_delay", 2.0),
    ))

    # 初始化数据管道
    pipeline = DataPipelineManager()
    pipeline.add_pipeline(DedupPipeline(key_fields=["title", "url"]))
    pipeline.add_pipeline(JsonExportPipeline(output_dir=OUTPUT_DIR))

    # 执行爬取
    result = engine.run(urls)
    results = result["results"]

    # 数据处理
    for i, crawl_result in enumerate(results):
        item = DataItem(
            name=f"task_{task_id}",
            data={
                "url": crawl_result.url,
                "status": crawl_result.status_code,
                "content_length": len(crawl_result.html),
                "title": "",
                "crawled_at": datetime.now().isoformat(),
            },
            source_url=crawl_result.url,
        )
        pipeline.process(item)

    pipeline.close()

    # 保存任务结果
    output_file = os.path.join(OUTPUT_DIR, f"{task_id}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "task_id": task_id,
            "status": "completed",
            "total": result["stats"]["total"],
            "success": result["stats"]["success"],
            "failed": result["stats"]["failed"],
            "elapsed": result["elapsed"],
            "completed_at": datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)

    return {
        "task_id": task_id,
        "total": result["stats"]["total"],
        "success": result["stats"]["success"],
        "failed": result["stats"]["failed"],
    }


@app.task
def cleanup_old_tasks(days: int = 7):
    """清理过期任务数据"""
    import shutil
    OUTPUT_DIR = "./output"
    now = datetime.now()
    for f in os.listdir(OUTPUT_DIR):
        filepath = os.path.join(OUTPUT_DIR, f)
        if os.path.isfile(filepath):
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if (now - mtime).days > days:
                os.remove(filepath)
    return f"清理完成，保留最近 {days} 天的数据"
