"""
生产级日志配置

Usage:
    from logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("任务启动", extra={"task_id": task_id})
    logger.error("爬取失败", exc_info=True, extra={"url": url})
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "json")  # json / text
LOG_FILE = os.environ.get("LOG_FILE", "")  # 不设置则只输出到 stdout


class JsonFormatter(logging.Formatter):
    """JSON 格式化器（便于 ELK/日志平台解析）"""

    def format(self, record):
        import json
        from datetime import datetime, timezone

        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        log_entry = {
            "timestamp": ts,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 合并 extra 字段
        for key in ("task_id", "url", "batch_id", "elapsed", "rows"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])

        return json.dumps(log_entry, ensure_ascii=False, default=str)


def get_logger(name: str = "datapulse") -> logging.Logger:
    """获取配置好的 logger 实例"""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    logger.propagate = False

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    if LOG_FORMAT == "json":
        console.setFormatter(JsonFormatter())
    else:
        console.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)-7s %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        ))
    logger.addHandler(console)

    # 文件 handler（可选）
    if LOG_FILE:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    return logger
