<p align="center">
  <img src="https://img.shields.io/badge/DataPulse-v0.1.0-blue?style=for-the-badge" alt="DataPulse">
</p>

<p align="center">
  <b>🌐 开箱即用的数据采集 · 分析 · 可视化平台</b>
</p>

<p align="center">
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  </a>
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/FastAPI-0.104+-teal?logo=fastapi" alt="FastAPI">
  </a>
  <a href="https://vuejs.org/">
    <img src="https://img.shields.io/badge/Vue.js-3-4FC08D?logo=vue.js" alt="Vue.js">
  </a>
  <a href="https://www.docker.com/">
    <img src="https://img.shields.io/badge/Docker-ready-2496ED?logo=docker" alt="Docker">
  </a>
  <img src="https://img.shields.io/badge/Status-Alpha-yellow" alt="Status">
</p>

---

## ✨ 特性

<table>
<tr>
  <td width="50%">
    <h3>🕷️ 双引擎爬虫</h3>
    <ul>
      <li>异步 aiohttp 引擎 - 高速爬取静态页面</li>
      <li>Playwright 引擎 - 支持 JavaScript 渲染页面</li>
      <li>中间件链：随机延迟、UA 轮换、代理切换</li>
      <li>自动重试 + URL 指纹去重</li>
      <li>插件系统：自定义解析器按需扩展</li>
    </ul>
  </td>
  <td width="50%">
    <h3>📊 数据分析管道</h3>
    <ul>
      <li>数据清洗：缺失值填充、异常值检测</li>
      <li>统计分析：描述统计、相关性矩阵</li>
      <li>机器学习：KMeans 聚类分析</li>
      <li>文本分析：中文分词、词频、情感分析</li>
      <li>一键生成 Markdown/HTML 数据报告</li>
    </ul>
  </td>
</tr>
<tr>
  <td width="50%">
    <h3>📈 可视化看板</h3>
    <ul>
      <li>Vue.js 3 + Element Plus 构建</li>
      <li>数据集管理：上传、预览、选择</li>
      <li>分析结果实时展示</li>
      <li>数据导出：CSV / Excel / JSON</li>
    </ul>
  </td>
  <td width="50%">
    <h3>🚀 开箱即用</h3>
    <ul>
      <li>一条 Docker 命令启动全部服务</li>
      <li>RESTful API + Swagger 文档</li>
      <li>预置示例数据集，启动即用</li>
      <li>CLI 工具：终端直接爬取和分析</li>
    </ul>
  </td>
</tr>
</table>

## 🖼️ 界面预览

```
┌─────────────────────────────────────────────────────────┐
│  数据采集与分析平台 Dashboard                              │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐               │
│  │数据集 │  │数据量 │  │爬虫任务│  │存储  │               │
│  │  3 个 │  │ 51条  │  │  3个  │  │2.3MB │               │
│  └──────┘  └──────┘  └──────┘  └──────┘               │
│  ┌────────────┐  ┌──────────────────────────────────┐  │
│  │ 数据集列表  │  │ 数据预览 / 分析结果               │  │
│  │ 📁 电子产品 │  │ 商品名称   价格   销量   评分     │  │
│  │ 📁 电商销售 │  │ iPhone   9999  15200  4.8      │  │
│  │ 📁 用户评论 │  │ 华为Mate 6999  28500  4.9      │  │
│  └────────────┘  └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 使用 Docker（推荐）

```bash
# 克隆项目
git clone https://gitee.com/huiliyi122/datapulse.git
cd datapulse

# 一键启动
docker-compose up -d

# 打开浏览器
open http://localhost:3000   # 前端看板
open http://localhost:8000/docs  # API 文档
```

### 手动启动

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn api:app --reload --port 8000

# 前端（另一个终端）
cd frontend
npm install
npm run dev
```

### 使用 CLI

```bash
# 爬取网页
datapulse crawl https://example.com

# 启动 Web 服务
datapulse serve

# 分析本地 CSV
datapulse analyze data.csv
```

## 📦 技术栈

| 层级 | 技术 |
|---|---|
| **爬虫引擎** | Python, aiohttp, Playwright, BeautifulSoup |
| **后端** | FastAPI, Celery, Redis |
| **数据分析** | Pandas, NumPy, Scikit-learn, jieba |
| **前端** | Vue.js 3, Element Plus, ECharts |
| **数据库** | PostgreSQL, MongoDB, SQLite |
| **部署** | Docker, Docker Compose, Nginx |

## 🗂️ 项目结构

```
datapulse/
├── backend/              # FastAPI 后端
│   ├── api.py            # RESTful API
│   ├── analysis.py       # 数据分析引擎
│   ├── tasks.py          # Celery 异步任务
│   └── requirements.txt
├── spider/               # 爬虫引擎
│   ├── engine.py         # 双引擎核心（aiohttp + Playwright）
│   ├── pipelines.py      # 数据处理管道
│   ├── plugin.py         # 插件系统
│   ├── cli.py            # 命令行工具
│   └── plugins/          # 内置解析器
├── frontend/             # Vue.js 前端
│   ├── src/              # 源码
│   └── package.json
├── tests/                # 测试
├── docker-compose.yml    # 一键部署
├── pyproject.toml        # 项目元数据
└── README.md
```

## 🤝 参与贡献

欢迎贡献代码！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing`)
3. 提交改动 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing`)
5. 提交 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源，详见 [LICENSE](LICENSE) 文件。

---

<p align="center">
  <b>如果 DataPulse 对你有帮助，请给它一个 ⭐️</b>
</p>
