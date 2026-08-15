# 小苏企业智能助手

小苏是一个面向企业员工的内部 AI 助手。员工可以通过钉钉询问公司制度、查询员工和考勤信息、统计订单数据；管理员通过 Web 后台管理知识库并查看对话日志。

## 当前状态

项目处于基础骨架阶段，已经包含：

- Vue 3、TypeScript、Vite 和 Element Plus 管理后台。
- FastAPI 服务及健康检查接口。
- PostgreSQL 与 pgvector 开发环境。
- Docker Compose 一条命令启动入口。
- Python 和前端基础自动化检查。

## 技术栈

- Web：Vue 3、TypeScript、Vite、Element Plus、Pinia
- API：FastAPI、Pydantic、SQLAlchemy
- Database：PostgreSQL、pgvector
- Tooling：pnpm、uv、pytest、Ruff、Docker Compose
- IM：钉钉 Stream 机器人

## 快速开始

1. 复制 .env.example 为 .env，并填写需要的配置。
2. 执行 ./scripts/start.sh。
3. 打开 http://localhost:5173。
4. 后端接口文档位于 http://localhost:8000/docs。

## 本地开发

后端依赖：

    cd apps/api
    uv sync
    uv run uvicorn xiaosu.main:app --reload

前端依赖：

    pnpm install
    pnpm --filter @xiaosu/web dev

## 测试

    ./scripts/test.sh

## Roadmap

- [ ] Mock 员工、考勤和订单 API
- [ ] 多格式文档解析与增量索引
- [ ] 基于 pgvector 的知识库检索与引用
- [ ] Agent 工具调用与多轮对话
- [ ] 文档、日志和设置后台
- [ ] 钉钉 Stream 机器人
- [ ] 自动化 Evals 与在线 Demo

