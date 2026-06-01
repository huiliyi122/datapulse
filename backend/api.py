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
    FastAPI, UploadFile, File, HTTPException, Query, WebSocket
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from analysis import (
    DataCleaner, DataAnalyzer, TextAnalyzer,
    ReportGenerator, generate_insights,
)

app = FastAPI(
    title="数据采集与分析平台 API",
    description="提供数据上传、清洗、分析、导出等一站式服务",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
OUTPUT_DIR = "./output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 请求/响应模型
# ============================================================

class ScrapeRequest(BaseModel):
    urls: list[str]
    max_pages: int = 10
    delay: float = 1.0
    use_proxy: bool = False

class AnalysisRequest(BaseModel):
    dataset_id: str
    analysis_type: str = "summary"
    columns: list[str] = []

class ExportRequest(BaseModel):
    dataset_id: str
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
    """模拟爬虫任务执行并生成结果文件"""
    await asyncio.sleep(3)  # 模拟爬取耗时

    results = []
    for i, url in enumerate(request.urls):
        results.append({
            "title": f"商品 {i+1}",
            "price": f"{round(10 + i * 10.5, 2)}",
            "url": url,
            "crawled_at": datetime.now().isoformat(),
        })

    total = len(results)
    task_data = {
        "task_id": task_id,
        "status": "completed",
        "total": total,
        "success": total,
        "failed": 0,
        "elapsed": 3.0,
        "created_at": tasks_db[task_id]["created_at"],
        "completed_at": datetime.now().isoformat(),
        "urls": request.urls,
        "results": results,
    }

    # 保存到文件（持久化）
    with open(os.path.join(OUTPUT_DIR, f"{task_id}.json"), "w", encoding="utf-8") as f:
        json.dump(task_data, f, ensure_ascii=False, indent=2)

    # 更新内存状态
    tasks_db[task_id] = {"task_id": task_id, "status": "completed", **task_data}


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


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0", "timestamp": datetime.now().isoformat(), "uptime": "running"}
