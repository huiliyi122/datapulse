# 贡献指南

感谢你有兴趣为 DataPulse 贡献代码！

## 开发环境搭建

```bash
# 克隆项目
git clone https://gitee.com/huiliyi122/datapulse.git
cd datapulse

# 使用 Docker
docker-compose up -d

# 或手动安装
pip install -e .
pip install -r requirements-dev.txt
```

## 提 Issue

- **Bug 报告**: 使用 Bug Report 模板，描述复现步骤和环境信息
- **功能请求**: 使用 Feature Request 模板，说明使用场景

## 提 Pull Request

1. Fork 项目
2. 创建分支: `git checkout -b feature/your-feature`
3. 添加测试
4. 确保测试通过: `pytest tests/`
5. 提交改动: `git commit -m "feat: your feature description"`
6. 推送分支: `git push origin feature/your-feature`
7. 提交 Pull Request

## 代码规范

- 命名: snake_case for variables/functions, CamelCase for classes
- 使用类型注解
- 添加必要的 docstring
- 使用 ruff 检查代码风格

## 提交信息格式

使用 Conventional Commits:
- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `refactor:` 重构
- `test:` 测试
- `chore:` 构建/工具变动

## 许可证

贡献意味着你同意将代码以 MIT 许可证授权。
