"""
爬虫任务持久化存储（SQLite）
"""
import json
import os
import sqlite3
import threading
from datetime import datetime


DB_PATH = os.environ.get("TASK_DB_PATH", "./tasks.db")


class TaskStore:
    """基于 SQLite 的任务存储"""

    def __init__(self, db_path: str = DB_PATH):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock, self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL DEFAULT 'pending',
                    urls TEXT,
                    total INTEGER DEFAULT 0,
                    success INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    elapsed REAL DEFAULT 0,
                    message TEXT,
                    created_at TEXT,
                    completed_at TEXT,
                    result_data TEXT
                )
            """)
            conn.commit()

    def create_task(self, task_id: str, urls: list[str]) -> dict:
        """创建新任务"""
        data = {
            "task_id": task_id,
            "status": "pending",
            "urls": json.dumps(urls, ensure_ascii=False),
            "created_at": datetime.now().isoformat(),
        }
        with self._lock, self._get_conn() as conn:
            conn.execute("""
                INSERT INTO tasks (task_id, status, urls, created_at)
                VALUES (:task_id, :status, :urls, :created_at)
            """, data)
            conn.commit()
        return data

    def update_task(self, task_id: str, **kwargs):
        """更新任务状态"""
        sets = ", ".join(f"{k}=:{k}" for k in kwargs)
        with self._lock, self._get_conn() as conn:
            conn.execute(
                f"UPDATE tasks SET {sets} WHERE task_id=:task_id",
                {"task_id": task_id, **kwargs},
            )
            conn.commit()

    def get_task(self, task_id: str) -> dict | None:
        """获取单个任务"""
        with self._lock, self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    def list_tasks(self, status: str = None, limit: int = 50) -> list[dict]:
        """列出任务"""
        query = "SELECT * FROM tasks"
        params = ()
        if status:
            query += " WHERE status=?"
            params = (status,)
        query += " ORDER BY created_at DESC LIMIT ?"
        params += (limit,)

        with self._lock, self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock, self._get_conn() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status='running' THEN 1 ELSE 0 END) as running,
                    SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
                FROM tasks
            """).fetchone()
        return dict(row)

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        d = dict(row)
        if d.get("urls"):
            try:
                d["urls"] = json.loads(d["urls"])
            except (json.JSONDecodeError, TypeError):
                pass
        if d.get("result_data"):
            try:
                d["result_data"] = json.loads(d["result_data"])
            except (json.JSONDecodeError, TypeError):
                pass
        return d

    def close(self):
        pass


# 全局单例
task_store = TaskStore()
