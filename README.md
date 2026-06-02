<p align="center">
  <img src="https://img.shields.io/badge/DataPulse-v0.3.4-blue?style=for-the-badge" alt="DataPulse">
</p>

<p align="center">
  <b>All-in-One Data Scraping, Analysis & Visualization Platform</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python">
  <img src="https://img.shields.io/badge/License-MIT-green">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-teal?logo=fastapi">
  <img src="https://img.shields.io/badge/Vue.js-3-brightgreen?logo=vue.js">
  <img src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker">
  <img src="https://img.shields.io/badge/files-58-orange">
  <img src="https://img.shields.io/badge/code-6500%2B_lines-blue">
  <img src="https://img.shields.io/badge/tests-30%2B_passing-green">
</p>

---

## Overview

DataPulse is an open-source Python data scraping and analysis platform, providing a complete workflow from crawler development, data cleaning, statistical analysis to visualization dashboards. **One Docker command to launch all services.**

**Use cases:** E-commerce price monitoring, news sentiment analysis, competitive research, academic data collection, enterprise data hub

---

## Core Features

### 🕷️ Spider Engine

| Feature | Description |
|---|---|
| **Async Engine (aiohttp)** | High-speed static page crawling with concurrency control |
| **Browser Engine (Playwright)** | JS rendering for SPA apps (Vue/React) |
| **Stealth Anti-Bot** | Hides WebDriver fingerprint, spoofs browser characteristics, random UA/resolution |
| **Human Behavior Simulation** | Random mouse movement, scrolling patterns, request delays |
| **Proxy Pool** | Round-robin/random/weighted strategies, auto health check, failure removal |
| **Distributed Crawling** | Master-Worker architecture with Redis queues, horizontal scaling |
| **Auto Pagination** | Link-based, numeric, and Next-button pagination detection |
| **Plugin System** | `@register_parser` decorator for custom parsers |
| **Middleware Chain** | Random delay, UA rotation, auto retry, URL dedup |

### 🧠 AI Capabilities

**Smart Extraction** — Describe what you want in natural language, AI generates extraction rules automatically
```python
from spider import auto_extract
data = await auto_extract("https://example.com/products", "Extract all product names and prices")
```

**JS Reverse Engineering** (experimental) — AI-assisted signature algorithm analysis, auto-translate JS → Python
```python
from spider import try_reverse
result = await try_reverse("https://example.com/api", "_sign")
# Returns confidence score + auto-generated Python signing function
```

- Supports **Ollama** (local & free) and **OpenAI API**
- Honest confidence assessment (high/medium/low)

### 📊 Data Analysis

| Feature | Description |
|---|---|
| **Data Cleaning** | Missing value imputation, outlier detection (Z-Score), text cleaning |
| **Descriptive Statistics** | Mean/variance/median/distribution, column-level stats |
| **Correlation Analysis** | Numeric column correlation matrix |
| **KMeans Clustering** | Auto customer segmentation, product tier classification |
| **Text Analysis** | Chinese word segmentation, word frequency, TF-IDF keywords, sentiment analysis |
| **Report Generation** | One-click Markdown / HTML data reports |

### 📈 Dashboard

- Built with **Vue.js 3 + Element Plus**
- **ECharts charts**: bar charts (numeric comparison), pie charts (category distribution), summary cards, correlation heatmaps, cluster distribution
- Dataset management: upload, preview, select, analyze
- Scraper task monitoring: create tasks, real-time progress, history
- Data export: CSV / Excel / JSON
- **Swagger API docs**: interactive debugging

### 🔐 Authentication

- JWT token auth (zero-dependency PBKDF2 + HMAC-SHA256)
- Register / Login / Logout / Token refresh
- All endpoints public by default (personal mode)
- Default admin: **admin / admin123**

### ⚙️ Production Infrastructure

| Feature | Description |
|---|---|
| **pip install** | `pip install -e .` with `datapulse` CLI |
| **YAML Config** | `datapulse.yaml` unified config, env var override |
| **Multi-stage Docker** | Frontend build + backend runtime in one image |
| **Health Checks** | `/api/health` `/healthz` liveness + `/api/ready` readiness |
| **Rate Limiting** | 60 req/min global rate limit |
| **Error Handling** | Layered exception system + global exception handler |
| **Logging** | Structured JSON logging with rotating files |
| **Makefile** | `make test/lint/build/run/clean/dev` |

---

## Quick Start

### 🐳 Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/huiliyi122/datapulse.git
cd datapulse

# One-command startup
docker-compose up -d

# Open in browser
# Dashboard: http://localhost:3000
# API Docs: http://localhost:8000/docs
# Health: http://localhost:8000/api/health
```

### 📦 Production Deploy

```bash
# Multi-stage build
docker build -t datapulse .
docker run -d -p 8000:8000 datapulse
# → http://localhost:8000 (frontend included)
```

### 💻 Development

```bash
# Option 1: pip install
pip install -e .
datapulse serve          # Start web service

# Option 2: from source
cd backend
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

### 🛠️ CLI

```bash
# Crawl a website
datapulse crawl https://example.com

# Start web server
datapulse serve

# Analyze a local file
datapulse analyze data.csv
```

---

## API Reference

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Register |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/data/datasets` | List datasets |
| POST | `/api/data/upload` | Upload data file |
| POST | `/api/analyze` | Run data analysis |
| POST | `/api/analyze/text` | Text analysis |
| POST | `/api/scrape/start` | Start scraper task |
| GET | `/api/scrape/tasks` | List scraper tasks |
| GET | `/api/scrape/results/{id}` | Get scrape results |
| POST | `/api/ai/extract` | AI smart extraction |
| POST | `/api/export` | Export data |
| POST | `/api/report/generate` | Generate report |
| POST | `/api/auth/logout` | Logout |
| POST | `/api/ai/jsreverse` | AI JS reverse engineering |
| GET | `/api/health` | Liveness check |
| GET | `/healthz` | K8s health probe |
| GET | `/api/ready` | Readiness probe |

---

## Project Structure

```
datapulse/
├── backend/               # FastAPI backend
│   ├── api.py             # RESTful API (rate limit/validation/error handling)
│   ├── analysis.py        # Data analysis engine
│   ├── auth.py            # JWT authentication
│   ├── settings.py        # Unified config (YAML + env vars)
│   ├── logging_config.py  # Structured logging
│   ├── task_store.py      # Task persistence
│   ├── seed.py            # Demo data initialization
│   └── requirements.txt
├── spider/                # Spider engine (15 modules)
│   ├── engine.py          # aiohttp async engine
│   ├── browser_engine.py  # Playwright + Stealth engine
│   ├── ai_parser.py       # AI smart extraction
│   ├── js_reverse.py      # AI JS reverse engineering (experimental)
│   ├── master.py          # Distributed Master node
│   ├── worker.py          # Distributed Worker node
│   ├── pagination.py      # Auto pagination detection
│   ├── proxy_pool.py      # Proxy pool
│   ├── pipelines.py       # Data pipelines
│   ├── plugin.py          # Plugin system
│   ├── cli.py             # CLI tool
│   └── plugins/           # Built-in parsers
├── frontend/              # Vue.js 3 frontend
│   └── src/views + components (AnalysisChart / ScraperConfig)
├── tests/                 # 30+ test cases
├── Dockerfile             # Multi-stage production build
├── docker-compose.yml     # Dev environment one-click deploy
├── Makefile               # test/lint/build/run
├── datapulse.yaml         # Config template
├── pyproject.toml         # pip install support
└── README.md
```

---

## Examples

### Example 1: Quick Crawl + Export

```python
from spider import SpiderEngine, CrawlRequest
from spider.pipelines import DataPipelineManager, JsonExportPipeline, DedupPipeline

engine = SpiderEngine(concurrent=5)
pipeline = DataPipelineManager()
pipeline.add_pipeline(DedupPipeline())
pipeline.add_pipeline(JsonExportPipeline(output_dir="./output"))

result = engine.run(["https://example.com/list"])
pipeline.close()
print(f"Success: {result['stats']['success']}, Elapsed: {result['elapsed']:.1f}s")
```

### Example 2: Anti-Bot + Stealth Mode

```python
from spider import PlaywrightEngine, BrowserConfig, ProxyPool

pool = ProxyPool(["http://proxy1:8080", "http://proxy2:3128"])

engine = PlaywrightEngine(BrowserConfig(
    stealth=True,           # Hide automation traces
    simulate_human=True,    # Simulate human behavior
    proxy_pool=pool,        # Auto proxy rotation
))

await engine.start()
result = await engine.fetch("https://example.com")
await engine.stop()
```

### Example 3: Distributed Crawling

```python
from spider import distributed_crawl

async def parse_product(url):
    # Your parsing logic
    return {"url": url, "data": "..."}

result = await distributed_crawl(
    urls=["https://example.com/page1", "https://example.com/page2"],
    worker_func=parse_product,
    redis_url="redis://localhost:6379/0",
    concurrent=5,
)
print(f"Total: {result['total']}, Success: {result['success']}")
```

### Example 4: Auto Pagination

```python
from spider import PaginationDetector, SpiderEngine

detector = PaginationDetector()
engine = SpiderEngine(concurrent=1)

# Auto-crawl all pages
all_pages = await detector.crawl_all("https://example.com/list?page=1", engine, max_pages=10)
print(f"Crawled {len(all_pages)} pages")
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Spider Engine** | Python, aiohttp, Playwright, BeautifulSoup |
| **AI** | Ollama / OpenAI API |
| **Backend** | FastAPI, Celery, Redis |
| **Data Analysis** | Pandas, NumPy, Scikit-learn, jieba |
| **Frontend** | Vue.js 3, Element Plus, ECharts |
| **Database** | SQLite (dev), PostgreSQL (optional), MongoDB (optional) |
| **Deployment** | Docker, Docker Compose, Nginx |

---

## Contributing

Issues and Pull Requests are welcome!

1. Fork the repo
2. Create a branch: `git checkout -b feature/amazing`
3. Commit changes: `git commit -m "feat: your feature"`
4. Push: `git push origin feature/amazing`
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

Open sourced under the MIT License. See [LICENSE](LICENSE).

---

<p align="center">
  <b>If DataPulse helps you, please give it a ⭐️</b>
</p>
