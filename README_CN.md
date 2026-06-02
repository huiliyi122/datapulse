<p align="center">
  <img src="https://img.shields.io/badge/DataPulse-v0.3.3-blue?style=for-the-badge" alt="DataPulse">
</p>

<p align="center">
  <b>一站式数据采集、分析与可视化平台</b>
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

## 项目简介

DataPulse 是一个开源的 Python 数据采集分析平台，提供从爬虫开发、数据清洗、统计分析到可视化看板的完整工作流。**一条 Docker 命令即可启动全部服务。**

**适用场景：** 电商价格监控、新闻舆情分析、竞品数据调研、学术数据采集、企业内部数据中台

---

## 核心功能

### 🕷️ 爬虫引擎

| 功能 | 说明 |
|---|---|
| **异步引擎 (aiohttp)** | 高速爬取静态页面，支持并发控制 |
| **浏览器引擎 (Playwright)** | JS 渲染页面，支持 Vue/React 等 SPA 应用 |
| **Stealth 反反爬** | 隐藏 WebDriver 指纹、伪造浏览器特征、随机 UA/分辨率 |
| **人类行为模拟** | 随机鼠标移动、滚动模式、请求延迟 |
| **代理池** | 轮询/随机/加权三种策略，自动健康检查，失败剔除 |
| **分布式爬取** | Master-Worker 架构，Redis 队列通信，水平扩展 |
| **自动翻页检测** | 链接翻页、数字翻页、Next 按钮自动识别 |
| **插件系统** | `@register_parser` 装饰器注册自定义解析器 |
| **中间件链** | 随机延迟、UA 轮换、自动重试、URL 去重 |

### 🧠 AI 能力

**智能解析** — 自然语言描述需求，AI 自动生成提取规则
```python
from spider import auto_extract
data = await auto_extract("https://example.com/products", "提取所有商品名和价格")
```

**JS 逆向引擎** (实验性) — AI 辅助解析签名算法，自动翻译 JS → Python
```python
from spider import try_reverse
result = await try_reverse("https://example.com/api", "_sign")
# 返回 confidence + 自动生成的 Python 签名函数
```

- 支持 **Ollama**（本地免费）和 **OpenAI API**
- 诚实的置信度评估（high/medium/low）

### 📊 数据分析

| 功能 | 说明 |
|---|---|
| **数据清洗** | 缺失值填充、异常值检测（Z-Score）、文本清洗 |
| **描述统计** | 均值/方差/中位数/分布，字段级别统计 |
| **相关性分析** | 数值列相关系数矩阵 |
| **KMeans 聚类** | 自动客户分群、商品档次分类 |
| **文本分析** | 中文分词、词频统计、TF-IDF 关键词、情感分析 |
| **报告生成** | 一键生成 HTML 数据报告，弹窗预览 + 下载 |

### 📈 可视化看板

- **Vue.js 3 + Element Plus** 构建
- **ECharts 图表**：柱状图、饼图、相关性热力图、聚类分布图、数据摘要卡片
- 数据集管理：上传、预览、选择、分析
- 爬虫任务监控：创建任务、实时进度、历史记录
- 数据导出：CSV / Excel / JSON
- **Swagger API 文档**：在线调试

### 🔐 用户认证

- JWT Token 认证（PBKDF2 + HMAC-SHA256）
- 注册 / 登录 / 退出 / Token 刷新
- 所有接口默认公开（纯个人模式）
- 默认管理员：**admin / admin123**

### ⚙️ 生产级基础设施

| 能力 | 说明 |
|---|---|
| **pip install** | `pip install -e .` 安装，`datapulse` CLI 命令可用 |
| **YAML 配置** | `datapulse.yaml` 统一配置，环境变量可覆盖 |
| **多阶段 Docker** | 前端构建 + 后端运行合并一个镜像 |
| **健康检查** | `/api/health` `/healthz` 存活 + `/api/ready` 就绪探针 |
| **API 限流** | 60 req/min 全局限流 |
| **异常处理** | 分层异常体系 + 全局异常处理器 |
| **日志** | 结构化 JSON logging，滚动文件 |
| **Makefile** | `make test/lint/build/run/clean/dev` |

---

## 快速开始

### 🐳 Docker 部署（推荐）

```bash
git clone https://gitee.com/huiliyi122/datapulse.git
cd datapulse

# 一键启动
docker-compose up -d

# 打开浏览器
# 前端看板: http://localhost:3000
# API 文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/api/health
```

### 📦 生产部署

```bash
docker build -t datapulse .
docker run -d -p 8000:8000 datapulse
# → http://localhost:8000 (含前端)
```

### 💻 开发模式

```bash
# 方式一：pip install
pip install -e .
datapulse serve          # 启动 Web 服务

# 方式二：源码运行
cd backend
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

### 🛠️ CLI 命令行

```bash
datapulse crawl https://example.com   # 爬取网页
datapulse serve                       # 启动 Web 服务
datapulse analyze data.csv            # 分析本地文件
```

---

## API 接口速查

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 当前用户信息 |
| GET | `/api/data/datasets` | 数据集列表 |
| POST | `/api/data/upload` | 上传数据文件 |
| POST | `/api/analyze` | 执行数据分析 |
| POST | `/api/analyze/text` | 文本分析 |
| POST | `/api/scrape/start` | 启动爬虫任务 |
| GET | `/api/scrape/tasks` | 爬虫任务列表 |
| GET | `/api/scrape/results/{id}` | 爬取结果 |
| POST | `/api/ai/extract` | AI 智能解析 |
| POST | `/api/export` | 导出数据 |
| POST | `/api/report/generate` | 生成报告 |
| POST | `/api/auth/logout` | 退出登录 |
| POST | `/api/ai/jsreverse` | AI JS逆向分析 |
| GET | `/api/health` | 存活检查 |
| GET | `/healthz` | K8s 健康探针 |
| GET | `/api/ready` | 就绪探针 |

---

## 项目结构

```
datapulse/
├── backend/               # FastAPI 后端
│   ├── api.py             # RESTful API（限流/校验/异常处理）
│   ├── analysis.py        # 数据分析引擎
│   ├── auth.py            # JWT 认证系统
│   ├── settings.py        # 统一配置（YAML+环境变量）
│   ├── logging_config.py  # 结构化日志
│   ├── task_store.py      # 任务持久化
│   ├── seed.py            # 演示数据初始化
│   └── requirements.txt
├── spider/                # 爬虫引擎 (15 模块)
│   ├── engine.py          # aiohttp 异步引擎
│   ├── browser_engine.py  # Playwright + Stealth 引擎
│   ├── ai_parser.py       # AI 智能解析
│   ├── js_reverse.py      # AI JS 逆向引擎 (实验性)
│   ├── master.py          # 分布式 Master 节点
│   ├── worker.py          # 分布式 Worker 节点
│   ├── pagination.py      # 自动翻页检测
│   ├── proxy_pool.py      # 代理池
│   ├── pipelines.py       # 数据管道
│   ├── plugin.py          # 插件系统
│   ├── cli.py             # 命令行工具
│   └── plugins/           # 内置解析器
├── frontend/              # Vue.js 3 前端
│   └── src/views + components (AnalysisChart / ScraperConfig)
├── tests/                 # 29 测试全部通过
├── Dockerfile             # 多阶段生产构建
├── docker-compose.yml     # 开发环境一键部署
├── Makefile               # test/lint/build/run
├── datapulse.yaml         # 配置模板
├── pyproject.toml         # pip install 支持
└── README.md
```

---

## 使用示例

### 示例 1: 快速爬取 + 导出

```python
from spider import SpiderEngine, CrawlRequest
from spider.pipelines import DataPipelineManager, JsonExportPipeline, DedupPipeline

engine = SpiderEngine(concurrent=5)
pipeline = DataPipelineManager()
pipeline.add_pipeline(DedupPipeline())
pipeline.add_pipeline(JsonExportPipeline(output_dir="./output"))

result = engine.run(["https://example.com/list"])
pipeline.close()
print(f"成功: {result['stats']['success']}, 耗时: {result['elapsed']:.1f}s")
```

### 示例 2: 反反爬 + Stealth 模式

```python
from spider import PlaywrightEngine, BrowserConfig, ProxyPool

pool = ProxyPool(["http://proxy1:8080", "http://proxy2:3128"])

engine = PlaywrightEngine(BrowserConfig(
    stealth=True,           # 隐藏自动化痕迹
    simulate_human=True,    # 模拟人类行为
    proxy_pool=pool,        # 代理自动轮换
))

await engine.start()
result = await engine.fetch("https://example.com")
await engine.stop()
```

### 示例 3: 分布式爬取

```python
from spider import distributed_crawl

async def parse_product(url):
    return {"url": url, "data": "..."}

result = await distributed_crawl(
    urls=["https://example.com/page1", "https://example.com/page2"],
    worker_func=parse_product,
    redis_url="redis://localhost:6379/0",
    concurrent=5,
)
print(f"总计: {result['total']}, 成功: {result['success']}")
```

### 示例 4: 自动翻页

```python
from spider import PaginationDetector, SpiderEngine

detector = PaginationDetector()
engine = SpiderEngine(concurrent=1)

all_pages = await detector.crawl_all("https://example.com/list?page=1", engine, max_pages=10)
print(f"共爬取 {len(all_pages)} 页")
```

---

## 技术栈

| 层级 | 技术 |
|---|---|
| **爬虫引擎** | Python, aiohttp, Playwright, BeautifulSoup |
| **AI** | Ollama / OpenAI API |
| **后端** | FastAPI, Celery, Redis |
| **数据分析** | Pandas, NumPy, Scikit-learn, jieba |
| **前端** | Vue.js 3, Element Plus, ECharts |
| **数据库** | SQLite (开发), PostgreSQL (可选), MongoDB (可选) |
| **部署** | Docker, Docker Compose, Nginx |

---

## 参与贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建分支: `git checkout -b feature/amazing`
3. 提交改动: `git commit -m "feat: your feature"`
4. 推送分支: `git push origin feature/amazing`
5. 提交 Pull Request

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 许可证

基于 MIT 许可证开源，详见 [LICENSE](LICENSE)

---

<p align="center">
  <b>如果 DataPulse 对你有帮助，请给它一个 ⭐️</b>
</p>
