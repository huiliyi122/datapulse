"""
DataPulse v0.3.1 应用配置管理

优先级: 环境变量 > YAML 配置文件 > 默认值
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _load_yaml(path: str) -> dict:
    """加载 YAML 配置文件"""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _env_or(key: str, fallback):
    """从环境变量或配置值读取，支持类型转换"""
    env_val = os.environ.get(key)
    if env_val is not None:
        if isinstance(fallback, bool):
            return env_val.lower() in ("true", "1", "yes")
        if isinstance(fallback, int):
            return int(env_val)
        if isinstance(fallback, float):
            return float(env_val)
        return env_val
    return fallback


# --- 加载配置文件 ---
_CONFIG_PATH = os.environ.get("DATAPULSE_CONFIG", "datapulse.yaml")
_config = _load_yaml(_CONFIG_PATH) if Path(_CONFIG_PATH).exists() else {}


def _get(section: str, key: str, default):
    """三层优先级读取: 环境变量 > YAML > 默认值"""
    env_key = f"DATAPULSE_{section.upper()}_{key.upper()}"
    yaml_val = _config.get(section, {}).get(key) if _config else None
    return _env_or(env_key, yaml_val if yaml_val is not None else default)


@dataclass
class SpiderSettings:
    concurrent: int = field(default_factory=lambda: _get("spider", "concurrent", 5))
    min_delay: float = field(default_factory=lambda: _get("spider", "min_delay", 0.5))
    max_delay: float = field(default_factory=lambda: _get("spider", "max_delay", 2.0))
    timeout: int = field(default_factory=lambda: _get("spider", "timeout", 30))
    max_retries: int = field(default_factory=lambda: _get("spider", "max_retries", 3))
    user_agent_rotation: bool = field(default_factory=lambda: _get("spider", "user_agent_rotation", True))


@dataclass
class BrowserSettings:
    headless: bool = field(default_factory=lambda: _get("browser", "headless", True))
    stealth: bool = field(default_factory=lambda: _get("browser", "stealth", True))
    simulate_human: bool = field(default_factory=lambda: _get("browser", "simulate_human", True))
    timeout: int = field(default_factory=lambda: _get("browser", "timeout", 30))


@dataclass
class ProxySettings:
    enabled: bool = field(default_factory=lambda: _get("proxy", "enabled", False))
    pool_file: Optional[str] = field(default_factory=lambda: _get("proxy", "pool_file", None))
    strategy: str = field(default_factory=lambda: _get("proxy", "strategy", "weighted"))
    max_fail: int = field(default_factory=lambda: _get("proxy", "max_fail", 3))


@dataclass
class AppSettings:
    # 服务
    host: str = field(default_factory=lambda: _get("server", "host", "0.0.0.0"))
    port: int = field(default_factory=lambda: _get("server", "port", 8000))
    debug: bool = field(default_factory=lambda: _get("server", "debug", True))

    # 路径
    upload_dir: str = field(default_factory=lambda: _get("storage", "upload_dir", "./uploads"))
    output_dir: str = field(default_factory=lambda: _get("storage", "output_dir", "./output"))
    db_path: str = field(default_factory=lambda: _get("storage", "db_path", "./tasks.db"))
    user_db_path: str = ""

    # Redis
    redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # JWT
    jwt_secret: str = field(default_factory=lambda: _get("auth", "jwt_secret", "datapulse-secret-change-in-production"))
    jwt_expire_hours: int = field(default_factory=lambda: _get("auth", "jwt_expire_hours", 24))

    # AI
    ai_provider: str = field(default_factory=lambda: _get("ai", "provider", "ollama"))
    ai_model: str = field(default_factory=lambda: _get("ai", "model", "qwen2.5:7b"))
    ai_base_url: Optional[str] = field(default_factory=lambda: _get("ai", "base_url", None))
    ai_api_key: Optional[str] = field(default_factory=lambda: _get("ai", "api_key", None))

    # 子配置
    spider: SpiderSettings = field(default_factory=SpiderSettings)
    browser: BrowserSettings = field(default_factory=BrowserSettings)
    proxy: ProxySettings = field(default_factory=ProxySettings)


settings = AppSettings()
