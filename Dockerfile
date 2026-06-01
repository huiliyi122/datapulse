# ============================================================
# DataPulse 多阶段 Docker 构建
# Stage 1: 前端构建
# Stage 2: 后端 + 前端产物合并
# ============================================================

# --- Stage 1: 前端构建 ---
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# --- Stage 2: 后端运行 ---
FROM python:3.11-slim

LABEL org.opencontainers.image.title="DataPulse"
LABEL org.opencontainers.image.description="生产级数据采集分析平台"
LABEL org.opencontainers.image.version="0.3.1"

WORKDIR /app

# Playwright 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    libasound2 libatspi2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && playwright install chromium --with-deps 2>/dev/null || true

# 项目文件
COPY pyproject.toml datapulse.yaml ./
COPY backend/ ./backend/
COPY spider/ ./spider/

# 前端产物
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 静态文件服务（FastAPI 直接 serve）
COPY frontend/dist ./static

# 初始化
RUN mkdir -p /app/uploads /app/output \
    && python -c "from backend.seed import seed_all; seed_all()" || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
