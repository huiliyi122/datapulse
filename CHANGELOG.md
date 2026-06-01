# Changelog

## v0.3.1 (2026-06-01)

### 新增
- 📦 **pip install 支持**: `pip install datapulse` 可安装，`datapulse crawl/serve/analyze` CLI 可用
- ⚙️ **YAML 配置文件**: `datapulse.yaml` 统一配置，环境变量可覆盖
- 🐳 **多阶段 Dockerfile**: 前端构建 + 后端运行合并到一个镜像
- 🏥 **健康检查**: `/api/health`、`/healthz` 存活探针、`/api/ready` 就绪探针
- 🛡️ **API 限流**: slowapi 60 req/min 全局限流
- 🧪 **Pydantic 数据校验**: 所有 Request model 字段级校验
- 📋 **Makefile**: `make test/lint/build/run/clean/dev`
- 🔧 **全局异常处理器**: 统一错误响应格式

### 改进
- 🔄 worker.py: print() 全部替换为结构化 logging
- 🔄 settings.py: 支持 YAML 文件 + 环境变量三层读取
- 🔄 API 版本号统一为 0.3.1

---

## v0.3.0 (2026-06-01)

### 新增
- 🧠 **AI 智能解析**: LLM 自动生成提取规则，一句话描述即可提取数据
- 🔀 **分布式爬取**: Master-Worker 架构 + Redis 队列，水平扩展
- 📄 **自动翻页检测**: 三种翻页模式（链接/数字/Next）
- 🔐 **用户认证**: JWT Token 认证，注册/登录/退出
- 🌐 **Playwright 引擎**: JS 渲染页面 + Stealth 反反爬
- 🔄 **代理池**: 轮询/随机/加权策略，健康检查自动剔除
- 🐭 **人类行为模拟**: 随机鼠标移动、滚动、延迟
- 📊 **ECharts 图表**: 柱状图/饼图/数据摘要卡片
- 🏗️ **生产级基础设施**: 结构化日志、分层异常、配置管理
- 🧪 **30+ 测试**: pytest + 持续集成

### 改进
- 🔧 API 真实爬虫引擎执行（替换模拟数据）
- 📝 全新 README：功能表/API 速查/4 个代码示例
- 🐳 Docker 一键部署 + 演示数据自动初始化

---

## v0.1.0 (初始版本)

- 🕷️ aiohttp 异步爬虫引擎 + 中间件链
- 📊 数据分析管道（清洗/去重/过滤/导出）
- 📈 统计分析、KMeans 聚类、文本分析
- 🖥️ Vue.js 3 可视化看板
- 🔌 插件系统 + CLI 工具
