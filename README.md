# 小苏企业智能助手 (Xiaosu Enterprise AI Assistant)

面向企业内部场景的生产级智能问答与多工具协同 Agent 系统。员工可在钉钉群聊/单聊中以自然语言查询公司制度、员工档案、考勤打卡、订单流水与实时时钟；管理员可通过现代化 Vue 3 Web 控制台进行知识库全生命周期管理、原文高亮定位、多模型热切换以及全要素审计。

---

## 🌟 核心特性与亮点

- 🚀 **多模型供应商热切换（核心加分项）**：
  - 抽象适配层原生支持 **阿里百炼（通义千问 Qwen3.7/Max）** 与 **智谱清言（GLM-4 系列）**；
  - 管理后台一键热切换，RAG 向量索引完美解耦，彻底避免跨模型空间失效。
- 📚 **生产级企业知识库 RAG**：
  - 支持 **Markdown / TXT / PDF / Word** 4 种主流格式上传、解析与自动切片；
  - 同名文件 SHA-256 智能去重与版本更新，删除文档级联清除向量切片；
  - 引用附带文档名称、章节标题、页码与段落序号，支持**原文弹窗高亮定位跳转**；
  - 相似度低于阈值（0.35）时触发系统级严格拒答，杜绝模型虚构信息。
- 🔧 **原生 Function Calling 智能体工具协同**：
  - 注册 6 项结构化工具（知识库检索、员工姓名查询、员工详情、考勤打卡、订单销售汇总、当前时间）；
  - 大模型根据自然语言意图自主多步协同调用，严禁 if-else 关键字路由。
- 💬 **钉钉 Stream 免穿透集成**：
  - 采用钉钉官方最新的 Stream 双向长连接模式，**免公网 IP、免域名、免内网穿透**，本地/容器即可稳定收发消息。
- ⚡ **极致流式打字与审计追踪**：
  - FastAPI SSE 原生流式打字机逐字输出，Nginx 关闭缓冲确保丝滑；
  - 全要素审计日志记录时间、用户、提问、答案、工具参数与结果、Token 消耗、预估费用与耗时。
- 🛡️ **工程规范与容器化**：
  - 全项目代码单文件 ≤ 500 行，单目录 ≤ 8 个文件，包含 23 项全自动化单元测试；
  - 提供 `docker compose up --build` 一键交付。

---

## 🛠️ 技术栈选型

- **后端开发**：Python 3.12+ / FastAPI / SQLAlchemy (Asyncpg) / pgvector / Pydantic v2
- **大模型生态**：OpenAI SDK 协议兼容 / 阿里云百炼（通义千问） / 智谱清言（GLM-4）
- **前端开发**：Vue 3 / Vite / TypeScript / Element Plus / Marked / DOMPurify
- **数据库与向量存储**：PostgreSQL 16 + pgvector 向量扩展
- **IM 客户端**：DingTalk Stream Client (Python SDK)
- **部署环境**：Docker & Docker Compose / Nginx 反向代理

---

## 🚀 快速上手与本地部署

### 1. 克隆代码与配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env
```

编辑根目录下的 `.env` 文件，填入模型 API Key 与管理员密码（详见 `.env.example` 说明）：
```dotenv
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ZHIPUAI_API_KEY=xxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxx
ADMIN_PASSWORD=xiaosu_admin_secret
```

### 2. Docker Compose 一键启动

```bash
# 启动核心服务 (PostgreSQL + API + Web 前端)
docker compose up -d --build

# 若需同时启动钉钉机器人，添加 --profile dingtalk
docker compose --profile dingtalk up -d --build
```

启动完成后访问：
- **Web 管理后台**：`http://localhost:5173`（默认账号：`admin`，密码见 `.env` 中的 `ADMIN_PASSWORD`）
- **FastAPI 接口文档**：`http://localhost:8000/docs`

---

## 🧪 自动化测试与质量保障

项目内置 23 项全量离线自动化测试，覆盖 Mock LLM 状态机、工具拦截、时区计算及多厂商适配：

```bash
# 进入 API 目录执行测试
cd apps/api
pytest -v
```

---

## 📖 核心文档导航

- 📘 [自评与设计总结 (自评.md)](file:///c:/Users/stone/Desktop/xiaosu/自评.md)
- 📝 [AI 工具使用说明 (AI_USAGE.md)](file:///c:/Users/stone/Desktop/xiaosu/AI_USAGE.md)
- 🔍 [笔试题目要求与交付功能逐项对照表 (docs/requirements-audit.md)](file:///c:/Users/stone/Desktop/xiaosu/docs/requirements-audit.md)
- ⚙️ [多模型供应商配置与管理指南 (docs/model-configuration.md)](file:///c:/Users/stone/Desktop/xiaosu/docs/model-configuration.md)
- 🤖 [钉钉 Stream 长连接机器人接入指南 (docs/dingtalk-setup.md)](file:///c:/Users/stone/Desktop/xiaosu/docs/dingtalk-setup.md)
- 🛠️ [开发问题与架构演进复盘记录 (docs/development-retrospective.md)](file:///c:/Users/stone/Desktop/xiaosu/docs/development-retrospective.md)
