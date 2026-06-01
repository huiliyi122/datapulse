# Changelog

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
