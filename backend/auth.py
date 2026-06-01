"""
用户认证系统

- JWT Token 认证
- SQLite 存储用户（零依赖）
- bcrypt 密码哈希
- 登录/注册/Token 刷新
"""
import hashlib
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional


# ============================================================
# 用户存储
# ============================================================

class UserStore:
    """SQLite 用户存储"""

    def __init__(self, db_path: str = "./users.db"):
        self._db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    last_login TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    expires_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            conn.commit()

    def create_user(self, username: str, email: str, password: str) -> dict:
        """创建用户"""
        password_hash = hash_password(password)
        with self._get_conn() as conn:
            try:
                cursor = conn.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, password_hash),
                )
                conn.commit()
                return {"id": cursor.lastrowid, "username": username, "email": email}
            except sqlite3.IntegrityError:
                return None

    def get_user(self, username: str) -> Optional[dict]:
        """通过用户名获取用户"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username=? AND is_active=1", (username,)
            ).fetchone()
            return dict(row) if row else None

    def verify_user(self, username: str, password: str) -> Optional[dict]:
        """验证用户密码"""
        user = self.get_user(username)
        if user and verify_password(password, user["password_hash"]):
            # 更新最后登录时间
            with self._get_conn() as conn:
                conn.execute(
                    "UPDATE users SET last_login=datetime('now') WHERE id=?",
                    (user["id"],),
                )
                conn.commit()
            return user
        return None

    def save_token(self, user_id: int, token: str, expires_hours: int = 24):
        """保存 API Token"""
        expires = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO api_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
                (user_id, token, expires),
            )
            conn.commit()

    def verify_token(self, token: str) -> Optional[int]:
        """验证 Token，返回 user_id"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM api_tokens WHERE token=? AND expires_at > datetime('now')",
                (token,),
            ).fetchone()
            return row["user_id"] if row else None

    def revoke_token(self, token: str):
        """撤销 Token"""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM api_tokens WHERE token=?", (token,))
            conn.commit()


# ============================================================
# 密码哈希（简易 bcrypt 替代，零依赖）
# ============================================================

def hash_password(password: str) -> str:
    """密码哈希"""
    salt = os.urandom(16).hex()
    return f"{salt}${_pbkdf2(password, salt)}"


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    try:
        salt, stored = hashed.split("$", 1)
        return _pbkdf2(password, salt) == stored
    except (ValueError, AttributeError):
        return False


def _pbkdf2(password: str, salt: str, iterations: int = 100000) -> str:
    """PBKDF2 哈希"""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()


# ============================================================
# JWT 生成与验证
# ============================================================

JWT_SECRET = os.environ.get("JWT_SECRET", "datapulse-secret-change-in-production")


def create_jwt(user_id: int, username: str, expires_hours: int = 24) -> str:
    """创建 JWT Token"""
    import base64
    import json

    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + expires_hours * 3600,
        "iat": int(time.time()),
    }).encode()).rstrip(b"=").decode()
    signature = base64.urlsafe_b64encode(
        hashlib.sha256(f"{header}.{payload}.{JWT_SECRET}".encode()).digest()
    ).rstrip(b"=").decode()

    return f"{header}.{payload}.{signature}"


def verify_jwt(token: str) -> Optional[dict]:
    """验证 JWT Token"""
    import base64
    import json

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header, payload, signature = parts

        # 验证签名
        expected_sig = base64.urlsafe_b64encode(
            hashlib.sha256(f"{header}.{payload}.{JWT_SECRET}".encode()).digest()
        ).rstrip(b"=").decode()

        if signature != expected_sig:
            return None

        # 解码 payload
        payload_bytes = payload.encode() + b"=" * (4 - len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload_bytes))

        # 检查过期
        if data.get("exp", 0) < int(time.time()):
            return None

        return {"user_id": data["user_id"], "username": data["username"]}

    except Exception:
        return None


# ============================================================
# 全局实例
# ============================================================

user_store = UserStore()

# 首次启动自动创建默认管理员账号
admin = user_store.get_user("admin")
if admin is None:
    user_store.create_user("admin", "admin@datapulse.local", "admin123")
    print("默认管理员已创建: admin / admin123")
