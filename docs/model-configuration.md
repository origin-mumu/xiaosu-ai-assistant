# 多模型供应商配置与管理指南

小苏智能助手采用标准适配器架构，原生支持 **阿里百炼（通义千问）** 与 **智谱清言（GLM 系列）** 两大主流大模型供应商，并支持在管理后台随时进行无缝热切换。

---

## 一、支持的供应商与默认模型

| 供应商 | 对话大模型（LLM） | 向量嵌入模型（Embedding） | 核心优势 |
|---|---|---|---|
| **阿里百炼 (DashScope)** | `qwen3.7-plus`（默认）<br>`qwen-max` / `qwen-plus` / `qwen-turbo` | `qwen3.7-text-embedding`（1024维） | Function Calling 极其敏捷，中文制度理解深刻，国内首选。 |
| **智谱清言 (ZhipuAI)** | `glm-4-plus`<br>`glm-4-air` / `glm-4-flash` / `glm-4-long` | `embedding-3`（1024维） | 强大的长文本推理能力与代码工具调用表现。 |

---

## 二、环境变量配置 (`.env`)

在项目根目录的 `.env` 中填入对应厂商的 API Key：

```dotenv
# ==========================================
# 阿里百炼 (DashScope) 配置
# ==========================================
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_CHAT_MODEL=qwen3.7-plus
DASHSCOPE_EMBEDDING_MODEL=qwen3.7-text-embedding

# ==========================================
# 智谱清言 (ZhipuAI) 配置
# ==========================================
ZHIPUAI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxx
ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
ZHIPUAI_CHAT_MODEL=glm-4-plus
ZHIPUAI_EMBEDDING_MODEL=embedding-3

# 当前默认启用的对话模型供应商 (dashscope / zhipuai)
LLM_PROVIDER=dashscope
```

---

## 三、管理后台热切换说明

1. 登录 Web 管理后台，进入 **「系统设置」** 页面；
2. 在 **「模型厂商」** 单选组中选择 `阿里百炼 (DashScope)` 或 `智谱清言 (ZhipuAI)`；
3. 在下拉框中选择具体的模型版本（如 `qwen3.7-plus` 或 `glm-4-plus`），也可直接手动输入自定义模型名；
4. 点击 **「保存并应用配置」**，后端将配置持久化至数据库，并在下一次 Web 聊天或钉钉对话中立即生效！

---

## 四、RAG 向量索引兼容性设计（核心架构）

* **解耦原则**：系统的**问答大模型（LLM）**与**向量索引（Embedding）**完全解耦。
* **向量空间保护**：当你在后台从通义千问切换为智谱 GLM-4 时，底层知识库检索自动保持与当前数据库切片（`qwen3.7-text-embedding` 1024 维）一致的向量客户端，避免因跨厂商向量空间正交而导致的检索失效，确保两家大模型均能 100% 调出知识库引用卡片。
