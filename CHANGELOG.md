# Changelog

## v0.3.4 (2026-06-02)

### Technical Debt
- slowapi per-route rate limiting (auth 5/min, scrape 10/min, analyze 30/min)
- Unified config system: api.py + auth.py both use settings module
- Git history: all commit messages English, Co-Authored-By removed
- Test coverage: 29 → 49 cases (test_api.py + test_auth.py added)

### Frontend Refactoring
- vue-router with hash history and auth guards
- Sidebar navigation (Dashboard / Scraper / AI Extract / Text Analysis)
- Login & Register pages with token-based auth flow
- AI Smart Extract page (URL + description → schema + data)
- Text Analysis page (word frequency / keywords / sentiment + charts)
- Frontend now covers 100% of backend API endpoints
- Removed orphaned ScraperConfig.vue and DataDashboard.vue

### WebSocket
- scraper progress broadcast to all connected clients
- real-time status updates on task completion/failure

### Infrastructure
- Version bumped to 0.3.4 across all files
- INSERT OR REPLACE for duplicate token handling
- vite proxy: backend → localhost for local dev

## v0.3.3 (2026-06-02)

### 致命修复
- 文件下载永远404：相对路径与绝对路径比较修复
- _sanitize 空字符串 fallback 路径穿越绕过修复
- JWT 登出后 token 仍有效修复（增加 token 撤销校验）
- CLI Pipeline 从未被喂数据修复（去重/JSON导出现在生效）
- AI 智能解析 infer→extract 全链路断裂修复（移除 class 名 hash）
- Stealth 反反爬 JS 注入竞态修复
- @retry 装饰器对连接错误不生效修复
- asyncio.gather 单任务失败取消全批次修复
- URL 去重竞态条件修复
- docker-compose 构建失败修复

### 高危修复
- remove_outliers 零方差列静默丢弃全部数据修复
- 聚类标签 dropna() 后与原始数据不对齐修复
- Worker Windows SIGTERM 崩溃修复
- Worker Ctrl+C 信号处理失效修复
- Worker engine 未绑定防御修复
- js_reverse LLM 调用缺少 HTTP 状态码检查修复
- CsvExportPipeline 不同 key 写坏数据修复
- render_page/infer_sync 异步上下文崩溃修复

### 改进
- SSRF 防护：用 ipaddress 模块替代字符串比较，覆盖 IPv6 所有变体
- FilterPipeline 支持 regex 操作符
- HTML 报告 XSS 防护（html.escape）
- MongoPipeline 缺 pymongo 时报清晰的 ImportError
- 翻页检测移除单字符误匹配，增强 URL 模式匹配
- 代理池轮询修复跳过首个代理
- engine.run() 自动关闭 session 防泄漏
- CLI --delay 参数接入 RandomDelayMiddleware
- 所有 asyncio.gather 改用 return_exceptions=True
- celery 导入改为延迟加载
- pytest-cov 加入 dev 依赖
- 版本号统一为 0.3.3

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>

## v0.3.2 (2026-06-02)

### 安全修复
- JWT 签名由原始 SHA256 改为标准 HMAC-SHA256（符合 RFC 7519）
- Base64 padding 计算修复 `(4 - n%4) % 4`，避免 padding 多余
- 密码验证改用 `hmac.compare_digest` 常数时间比较，防时序攻击
- 文件下载路径穿越修复：`normpath` + 前缀校验 + `..` 拦截
- CORS `allow_origins=["*"]` + `allow_credentials=True` 互斥修复，改为环境变量可配
- 管理员创建从模块 import 副作用移入 `ensure_default_admin()` 显式调用

### 崩溃修复
- `describe_column` 单行数据 std() 返回 NaN → `_safe_num()` 转 null，避免 JSON 序列化崩溃
- numpy int64/float64 类型 `_py_val()` 转 Python 原生类型，确保 JSON 可序列化
- HTML 报告格式化 `None` 值崩溃 → `_nf()` 安全格式化
- `soup.title.string` 含子元素返回 None → 改为 `get_text(strip=True)`

### 逻辑修复
- `cli.py`: `engine.run()` 缺 `asyncio.run()` 包装，返回 coroutine 对象而非结果
- `pagination.py`: `isinstance(engine, type(self))` 永远为 False → 改为 `SpiderEngine`
- `worker.py`: 不存在的 `logging_config` 模块 → 改用标准 `logging.getLogger`
- `proxy_pool.py`: `requests.get` 同步阻塞事件循环 → 改为 `aiohttp` 异步
- `browser_engine.py`: stealth JS 对新建页面不注入（coroutine 未 await）→ 改为 async 函数
- `engine.py`: `_ensure_session` 竞态条件 → 加 `asyncio.Lock`
- `analysis.py`: HTML 报告 f-string 遗漏 → 补 `f` 前缀

### 数据完整性
- `pipelines.py`: JSON flush 每 100 条覆盖全部数据 → 改为累积到 close 时一次性写入
- `api.py`: CSV 读写编码不匹配（utf-8-sig 写 / utf-8 读导致 BOM 列名错乱）→ 统一 utf-8-sig
- `api.py`: `dataset_file` 字段与实际 CSV 文件名不一致 → 修复

### 前端增强
- 分析报告：从弹窗 500 字预览 → 完整 HTML 报告大弹窗 + 下载按钮
- 分析图表：新增相关性热力图、相关系数矩阵表、聚类分布图
- 爬虫进度：实时轮询 + 统计面板 + 结果表格
- 饼图优化：自动选择变量最多的分类列展示
- `el-upload` 增加 `on-error` 错误回调
- 端口硬编码 `localhost:8000` → 相对路径 `/api`
- `beforeUnmount` 清理 interval，修复内存泄漏
- 移除假趋势数值和假进度动画
- 修复 `DataAnalysis` 图标未 import 问题
- 添加 favicon 图标
- 假测试连接 → 真实 `/api/health` 请求

### 基础设施
- `Dockerfile`: 移除损坏的 `COPY frontend/dist ./static` 行
- `requirements.txt`: 补充缺失的 `pyyaml`、`slowapi`
- `.gitignore`: 清理重复条目，移除残留 dist 目录
- `api.py`: 健康检查 + 静态文件挂载调整到所有路由之后，修复路由劫持 404

### 已知限制
- slowapi 限流器已创建但未应用到各路由（需后续装饰器重构）
- settings.py 配置未被 api.py 使用（两套环境变量体系）
- 集群/分布式模块（master/worker/pagination）未经充分测试
- 测试覆盖率偏低（4个测试文件）

---

## v0.3.1 (2026-06-01)

### 新增
- pip install 支持: `pip install datapulse` 可安装，CLI 可用
- YAML 配置文件: `datapulse.yaml` 统一配置，环境变量可覆盖
- 多阶段 Dockerfile: 前端构建 + 后端运行合并到一个镜像
- 健康检查: `/api/health`、`/healthz`、`/api/ready` 就绪探针
- API 限流: slowapi 60 req/min 全局限流
- Pydantic 数据校验: 所有 Request model 字段级校验
- Makefile: `make test/lint/build/run/clean/dev`
- 全局异常处理器: 统一错误响应格式

### 改进
- worker.py: print() 替换为结构化 logging
- settings.py: YAML + 环境变量三层读取
- API 版本号统一为 0.3.1

---

## v0.3.0 (2026-06-01)

### 新增
- AI 智能解析: LLM 自动生成提取规则
- 分布式爬取: Master-Worker 架构 + Redis 队列
- 自动翻页检测
- 用户认证: JWT Token 认证
- Playwright 引擎 + Stealth 反反爬
- 代理池: 轮询/随机/加权策略
- 人类行为模拟
- ECharts 图表
- 生产级基础设施: 结构化日志、分层异常、配置管理
- 30+ 测试

---

## v0.1.0 (初始版本)

- aiohttp 异步爬虫引擎 + 中间件链
- 数据分析管道（清洗/去重/过滤/导出）
- 统计分析、KMeans 聚类、文本分析
- Vue.js 3 可视化看板
- 插件系统 + CLI 工具
