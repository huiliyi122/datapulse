# DataPulse Makefile — test / lint / build / run / clean

.PHONY: help install test lint clean build run dev docker-build docker-run

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装项目
	pip install -e ".[dev]"

test: ## 运行测试
	python -m pytest tests/ -v --tb=short

lint: ## 代码检查
	ruff check spider/ backend/

cov: ## 测试覆盖率
	python -m pytest tests/ --cov=spider --cov=backend --cov-report=term

clean: ## 清理构建产物
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

run: ## 启动服务
	uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload

dev: ## 开发模式（前后端）
	@echo "启动后端: http://localhost:8000"
	uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload &
	@echo "启动前端: http://localhost:3000"
	cd frontend && npm install && npm run dev

build: ## 构建 Docker 镜像
	docker build -t datapulse:latest .

docker-run: ## 运行 Docker 容器
	docker run -d -p 8000:8000 --name datapulse datapulse:latest
	@echo "http://localhost:8000"

docker-stop: ## 停止 Docker 容器
	docker stop datapulse && docker rm datapulse

publish: clean test lint build ## 发布前检查
	@echo "✅ 所有检查通过，可以发布"
