# AI 工具使用说明

这份说明基于本项目的真实开发过程整理，提交前我会再按实际面试表达检查一遍，而不是把它当作一份通用的“AI 提效”模板。

## 1. 使用了哪些 AI 工具

本项目主要使用 Codex Desktop 协助完成需求拆解、代码生成、终端操作、单元测试、Docker 验证和本地页面视觉检查。模型与钉钉的能力边界由我先确定：前端使用 Vue 3，模型统一选择阿里云百炼的千问对话和 Embedding，IM 选择钉钉 Stream。

AI 比较适合处理重复且可验证的工作，例如生成 Pydantic/TypeScript 类型、Mock 数据、解析器测试和文档初稿。我保留了架构选择、密钥安全、拒答策略、状态机和每次提交范围的决定权。

## 2. 一个具体 Prompt 与修改过程

我给出的核心要求是：“Embedding 和 LLM 都使用千问，查官方文档并把配置弄好，之后对照招聘笔试题把全部功能开发出来，我自己填 API 测试。”

AI 生成了 OpenAI 兼容的千问客户端、文档向量化和 Agent Tool Calling 骨架。可以直接采用的是统一 `ChatService` 和 `AgentToolExecutor` 的方向，因为这样钉钉与 Web 能复用消息处理逻辑。

我要求继续修改的部分包括：

- 最初文档成功状态写成 `ready`，但题目明确要求 `indexed`，所以统一改为 `pending/indexing/indexed/failed`。
- 最初管理后台只展示模型，题目要求能够切换，所以增加了只修改模型名、不暴露密钥的 PATCH 接口。
- 最初 Nginx 使用默认缓冲，SSE 可能被攒成一块，所以关闭 `proxy_buffering` 并增加 `X-Accel-Buffering: no`。
- 最初概览在 1280px 宽度发生横向截断，通过真实浏览器截图发现后改成中屏两列，并给嵌套容器设置 `min-width: 0`。

## 3. AI 把我带沟里的一次经历

Agent 测试第一次在 Windows 失败。AI 直接使用 `ZoneInfo("Asia/Shanghai")`，默认假设系统存在 IANA 时区数据库；Windows 环境实际没有 `tzdata`，两条 Mock LLM 测试都抛出 `ZoneInfoNotFoundError`。我没有绕过测试或改成系统本地时间，而是补充 `tzdata` 为显式依赖，再同时验证 Windows 本机和 Linux Docker 镜像。

另一个问题是 Docker Desktop 从中文路径构建时偶发路径解析失败。最终用临时盘符映射完成本地验证，并在 README 建议 Windows 用户将仓库放到纯英文路径。这些问题说明 AI 生成的“跨平台代码”必须真的在目标平台运行。

## 4. 如何验证 AI 生成的代码

- 后端每个阶段都执行 pytest、Ruff check 和 Ruff format check，目前有 16 条离线测试。
- Mock LLM 测试验证模型先选择工具、接收工具结果再作答；另一条测试故意让模型编造 CEO 地址，确认系统层会覆盖成拒答。
- 前端执行严格 TypeScript 检查和 Vite 生产构建。
- Docker 中实际创建 pgvector 表，调用健康、上传、聊天、日志和设置接口。
- 通过 Nginx 调用 SSE，确认收到多段 `delta` 后再收到 `done`。
- 用浏览器检查 DOM 与截图，发现并修复了横向溢出。
- 额外提供 20 条真实 API Evals，填入 Key 后可计算通过率。

## 5. 如果再做一遍

我会先把题目中的验收问题变成 Evals，再从测试倒推数据和工具 schema；同时第一天就确定事件协议，让 Web SSE 和钉钉卡片都消费统一的 `delta/tool/citation/done` 事件。数据库方面会从第一版就使用 Alembic，而不是原型阶段用 `create_all`。最后，我会更早做 1280px 和移动端视觉检查，减少功能完成后的样式返工。
