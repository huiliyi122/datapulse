"""
数据采集平台 - FastAPI 后端服务（完整版）
"""
import json
import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import (
    FastAPI, UploadFile, File, HTTPException, Query, WebSocket, Depends, Header
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from analysis import (
    DataCleaner, DataAnalyzer, TextAnalyzer,
    ReportGenerator, generate_insights,
)
from auth import user_store, create_jwt, verify_jwt

app = FastAPI(
    title="DataPulse API",
    description="生产级数据采集与分析平台",
    version="0.3.1",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 限流中间件（60 req/min 全局限流）
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
except ImportError:
    limiter = None


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """统一错误响应格式"""
    import traceback
    from logging_config import get_logger

    logger = get_logger("datapulse.api")
    logger.error("未处理异常", exc_info=True, extra={
        "url": str(request.url),
        "method": request.method,
    })

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": str(exc) if app.debug else "服务器内部错误",
            "request_id": str(uuid.uuid4())[:8],
        },
    )


UPLOAD_DIR = "./uploads"
OUTPUT_DIR = "./output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

security = HTTPBearer(auto_error=False)


# ============================================================
# 认证依赖
# ============================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict | None:
    payload = verify_jwt(credentials.credentials) if credentials else None
    if payload is None and credentials:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    return payload


async def require_auth(user: dict = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


# ============================================================
# 认证接口
# ============================================================

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=200)
    password: str = Field(..., min_length=6, max_length=128)

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    user = user_store.create_user(req.username, req.email, req.password)
    if user is None:
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
    token = create_jwt(user["id"], user["username"])
    user_store.save_token(user["id"], token)
    return {"message": "注册成功", "user": {"id": user["id"], "username": user["username"]}, "access_token": token, "token_type": "bearer"}

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = user_store.verify_user(req.username, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_jwt(user["id"], user["username"])
    user_store.save_token(user["id"], token)
    return {"access_token": token, "token_type": "bearer", "user": {"id": user["id"], "username": user["username"], "email": user["email"]}}

@app.get("/api/auth/me")
async def me(user: dict = Depends(require_auth)):
    return {"user_id": user["user_id"], "username": user["username"]}

@app.post("/api/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials:
        user_store.revoke_token(credentials.credentials)
    return {"message": "已退出登录"}


# ============================================================
# 请求/响应模型
# ============================================================

class ScrapeRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=100)
    max_pages: int = Field(default=10, ge=1, le=100)
    delay: float = Field(default=1.0, ge=0.1, le=10.0)
    use_proxy: bool = False

class AnalysisRequest(BaseModel):
    dataset_id: str = Field(..., min_length=1)
    analysis_type: str = "summary"
    columns: list[str] = Field(default=[], max_length=20)

class ExportRequest(BaseModel):
    dataset_id: str = Field(..., min_length=1)
    format: str = "excel"
    filters: dict = {}

# ============================================================
# 数据采集接口
# ============================================================

tasks_db: dict = {}

@app.post("/api/scrape/start")
async def start_scrape(request: ScrapeRequest):
    """启动爬虫任务（真实后端任务）"""
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    created_at = datetime.now().isoformat()

    tasks_db[task_id] = {
        "task_id": task_id,
        "status": "running",
        "total": 0,
        "success": 0,
        "failed": 0,
        "created_at": created_at,
        "message": f"正在爬取 {len(request.urls)} 个URL...",
    }

    # 模拟爬虫异步执行
    asyncio.create_task(_run_scrape_task(task_id, request))

    return {"task_id": task_id, "status": "running", "created_at": created_at}


async def _run_scrape_task(task_id: str, request: ScrapeRequest):
    """真实调用爬虫引擎执行任务"""
    import time
    from logging_config import get_logger

    logger = get_logger("datapulse.scraper")

    try:
        # 导入爬虫引擎
        from spider.engine import SpiderEngine, CrawlRequest, RandomDelayMiddleware
        from spider.pipelines import DataPipelineManager, JsonExportPipeline, DedupPipeline, DataItem

        engine = SpiderEngine(concurrent=min(request.max_pages, 10))
        engine.add_middleware(RandomDelayMiddleware(min_delay=max(0.5, request.delay), max_delay=request.delay + 1))

        start = time.time()

        # 真实爬取
        crawl_result = await engine.run(request.urls)

        # 构建结果
        results = []
        for r in crawl_result["results"]:
            if r.status_code == 200 and r.html:
                results.append({
                    "url": r.url,
                    "status": r.status_code,
                    "content_length": len(r.html),
                    "title": r.html[:200] if r.html else "",
                    "crawled_at": datetime.now().isoformat(),
                })

        elapsed = round(time.time() - start, 2)
        success = crawl_result["stats"]["success"]
        failed = crawl_result["stats"]["failed"]

        task_data = {
            "task_id": task_id,
            "status": "completed",
            "total": crawl_result["stats"]["total"],
            "success": success,
            "failed": failed,
            "elapsed": elapsed,
            "created_at": tasks_db[task_id]["created_at"],
            "completed_at": datetime.now().isoformat(),
            "urls": request.urls,
            "results": results,
        }

        logger.info("爬虫任务完成", extra={
            "task_id": task_id, "total": crawl_result["stats"]["total"],
            "success": success, "elapsed": elapsed,
        })

    except Exception as e:
        logger.error("爬虫任务失败", exc_info=True, extra={"task_id": task_id})

        task_data = {
            "task_id": task_id,
            "status": "failed",
            "total": 0,
            "success": 0,
            "failed": len(request.urls),
            "elapsed": 0,
            "created_at": tasks_db[task_id]["created_at"],
            "completed_at": datetime.now().isoformat(),
            "urls": request.urls,
            "error": str(e),
            "results": [],
        }

    # 持久化
    with open(os.path.join(OUTPUT_DIR, f"{task_id}.json"), "w", encoding="utf-8") as f:
        json.dump(task_data, f, ensure_ascii=False, indent=2)

    tasks_db[task_id] = {"task_id": task_id, "status": task_data["status"], **task_data}


@app.get("/api/scrape/task/{task_id}")
async def get_task_status(task_id: str):
    """查询爬虫任务状态"""
    task = tasks_db.get(task_id)
    if not task:
        task_file = os.path.join(OUTPUT_DIR, f"{task_id}.json")
        if os.path.exists(task_file):
            with open(task_file, "r", encoding="utf-8") as f:
                return json.load(f)
        raise HTTPException(status_code=404, detail="任务不存在")

    # 如果已完成且有结果文件，返回完整数据
    if task.get("status") == "completed":
        task_file = os.path.join(OUTPUT_DIR, f"{task_id}.json")
        if os.path.exists(task_file):
            with open(task_file, "r", encoding="utf-8") as f:
                return json.load(f)

    return task


@app.get("/api/scrape/tasks")
async def list_scrape_tasks():
    """获取所有爬虫任务列表"""
    task_list = []

    # 已完成的任务文件
    for f in sorted(os.listdir(OUTPUT_DIR), reverse=True):
        if f.endswith(".json"):
            try:
                with open(os.path.join(OUTPUT_DIR, f), "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                task_list.append({
                    "task_id": data.get("task_id", f.replace(".json", "")),
                    "status": "completed",
                    "total": data.get("total", 0),
                    "success": data.get("success", 0),
                    "failed": data.get("failed", 0),
                    "elapsed": data.get("elapsed", 0),
                    "created_at": data.get("created_at", ""),
                    "completed_at": data.get("completed_at", ""),
                    "urls": data.get("urls", []),
                    "results_count": len(data.get("results", [])),
                })
            except (json.JSONDecodeError, KeyError):
                continue

    # 内存中的运行中任务
    for task_id, task in tasks_db.items():
        if task.get("status") == "running":
            task_list.insert(0, {
                "task_id": task_id,
                "status": "running",
                "created_at": task.get("created_at", ""),
                "message": task.get("message", ""),
            })

    return {"tasks": task_list, "total": len(task_list)}


@app.get("/api/scrape/results/{task_id}")
async def get_scrape_results(task_id: str):
    """获取爬取结果数据"""
    task_file = os.path.join(OUTPUT_DIR, f"{task_id}.json")
    if not os.path.exists(task_file):
        raise HTTPException(status_code=404, detail="结果文件不存在")
    with open(task_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


# ============================================================
# 数据上传与预览接口
# ============================================================

@app.post("/api/data/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传数据文件（CSV / Excel / JSON）"""
    file_id = uuid.uuid4().hex[:12]
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in [".csv", ".xlsx", ".xls", ".json"]:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

    filepath = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    df = _load_dataframe(filepath)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "size": len(content),
        "rows": len(df),
        "columns": list(df.columns),
        "preview": json.loads(df.head(10).to_json(orient="records", force_ascii=False)),
        "upload_time": datetime.now().isoformat(),
    }


@app.get("/api/data/datasets")
async def list_datasets():
    """列出已上传的数据集（含预览）"""
    files = []
    for f in os.listdir(UPLOAD_DIR):
        filepath = os.path.join(UPLOAD_DIR, f)
        if not os.path.isfile(filepath):
            continue
        stats = os.stat(filepath)
        try:
            df = _load_dataframe(filepath)
            preview = json.loads(df.head(5).to_json(orient="records", force_ascii=False))
            files.append({
                "id": os.path.splitext(f)[0],
                "filename": f,
                "size": stats.st_size,
                "rows": len(df),
                "columns": list(df.columns),
                "preview": preview,
                "upload_time": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            })
        except Exception:
            files.append({
                "id": os.path.splitext(f)[0],
                "filename": f,
                "size": stats.st_size,
                "upload_time": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            })
    return {"datasets": files}


# ============================================================
# 数据分析接口
# ============================================================

@app.post("/api/analyze")
async def analyze_data(request: AnalysisRequest):
    """执行数据分析"""
    filepath = _resolve_dataset(request.dataset_id)
    if not filepath:
        raise HTTPException(status_code=404, detail="数据集不存在")

    df = _load_dataframe(filepath)
    analyzer = DataAnalyzer(df)

    if request.analysis_type == "summary":
        result = analyzer.summary()
        result["insights"] = generate_insights(analyzer)
        result["columns_detail"] = {
            col: analyzer.describe_column(col)
            for col in df.columns[:20]
        }
    elif request.analysis_type == "correlation":
        result = analyzer.correlation_matrix()
    elif request.analysis_type == "clustering":
        cols = request.columns or df.select_dtypes(
            include=["float64", "int64"]
        ).columns[:3].tolist()
        clusters = analyzer.clustering(cols)
        result = {
            "clusters": clusters,
            "columns": cols,
            "n_clusters": len(set(clusters)),
        }
    else:
        raise HTTPException(status_code=400, detail=f"未知分析类型: {request.analysis_type}")

    return {"dataset_id": request.dataset_id, "analysis_type": request.analysis_type, "result": result}


@app.post("/api/analyze/text")
async def analyze_text(texts: list[str] = Query(...), analysis: str = "wordcloud"):
    """文本分析（词频/关键词/情感）"""
    analyzer = TextAnalyzer()
    if analysis == "wordcloud":
        result = analyzer.word_frequency(texts)
    elif analysis == "keyword":
        result = analyzer.extract_keywords(texts)
    elif analysis == "sentiment":
        result = [{"text": t[:50], "score": analyzer.sentiment_score(t)} for t in texts]
    else:
        raise HTTPException(status_code=400, detail=f"未知分析类型: {analysis}")
    return {"analysis": analysis, "result": result}


# ============================================================
# 数据导出接口
# ============================================================

@app.post("/api/export")
async def export_data(request: ExportRequest):
    """导出分析结果"""
    filepath = _resolve_dataset(request.dataset_id)
    if not filepath:
        raise HTTPException(status_code=404, detail="数据集不存在")

    df = _load_dataframe(filepath)
    for field, value in request.filters.items():
        if field in df.columns:
            df = df[df[field] == value]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if request.format == "excel":
        path = os.path.join(OUTPUT_DIR, f"export_{request.dataset_id}_{ts}.xlsx")
        df.to_excel(path, index=False)
    elif request.format == "csv":
        path = os.path.join(OUTPUT_DIR, f"export_{request.dataset_id}_{ts}.csv")
        df.to_csv(path, index=False, encoding="utf-8-sig")
    elif request.format == "json":
        path = os.path.join(OUTPUT_DIR, f"export_{request.dataset_id}_{ts}.json")
        df.to_json(path, orient="records", force_ascii=False, indent=2)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {request.format}")

    return {"download_url": f"/api/download/{os.path.basename(path)}", "rows": len(df), "format": request.format}


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """文件下载"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath, filename=filename)


@app.post("/api/report/generate")
async def generate_report(dataset_id: str, title: str = "数据分析报告"):
    """生成数据分析报告"""
    filepath = _resolve_dataset(dataset_id)
    if not filepath:
        raise HTTPException(status_code=404, detail="数据集不存在")
    df = _load_dataframe(filepath)
    analyzer = DataAnalyzer(df)
    report = ReportGenerator.generate_markdown_report(analyzer, title)
    report_path = os.path.join(OUTPUT_DIR, f"report_{dataset_id}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    return {"report": report, "download_url": f"/api/download/{os.path.basename(report_path)}"}


# ============================================================
# WebSocket 实时推送
# ============================================================

connected_clients: set = set()

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Pong: {data}")
    except Exception:
        pass
    finally:
        connected_clients.discard(websocket)


# ============================================================
# AI 智能解析接口
# ============================================================

class AIExtractRequest(BaseModel):
    url: str
    description: str
    provider: str = "ollama"  # ollama / openai

@app.post("/api/ai/extract")
async def ai_extract(request: AIExtractRequest):
    """
    AI 智能解析: 给 URL + 自然语言描述，自动提取数据

    示例:
    {
        "url": "https://books.toscrape.com",
        "description": "提取所有书名和价格",
        "provider": "ollama"
    }
    """
    try:
        from spider.ai_parser import AIParser

        parser = AIParser(provider=request.provider)

        # 先爬取
        html = await parser._fetch_url(request.url)

        # AI 推断规则
        schema = await parser.infer(html, request.description)

        # 提取数据
        data = parser.extract(html, schema)

        return {
            "url": request.url,
            "description": request.description,
            "provider": request.provider,
            "schema": schema,
            "data_count": len(data),
            "data": data[:20],  # 只返回前 20 条预览
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI解析失败: {str(e)}")


# ============================================================
# 辅助函数
# ============================================================

def _resolve_dataset(dataset_id: str) -> Optional[str]:
    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(dataset_id):
            return os.path.join(UPLOAD_DIR, f)
    return None


def _load_dataframe(filepath: str) -> pd.DataFrame:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        return pd.read_csv(filepath, encoding="utf-8")
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(filepath)
    elif ext == ".json":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
    return pd.DataFrame()


# 静态文件服务（前端打包 + 桌面模式）
from fastapi.staticfiles import StaticFiles
try:
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
except Exception:
    pass  # 开发模式下前端由 Vite 提供


@app.get("/api/health")
@app.get("/healthz")
async def health_check():
    """健康检查 - 基础存活探针"""
    return {"status": "ok", "version": "0.3.1", "timestamp": datetime.now().isoformat()}

@app.get("/api/ready")
async def readiness_check():
    """就绪探针 - 含存储目录检查"""
    checks = {
        "api": "ok",
        "uploads": os.path.isdir(UPLOAD_DIR),
        "output": os.path.isdir(OUTPUT_DIR),
    }
    all_ok = all(checks.values())
    return {
        "ready": all_ok,
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }
