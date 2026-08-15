# 千问模型配置

小苏的对话生成与文本向量统一使用阿里云百炼，避免同时维护两套供应商凭证。

## 默认模型

| 用途 | 模型 | 选择原因 |
|---|---|---|
| 对话和 Agent | `qwen3.7-plus` | 支持 Function Calling，适合知识库与内部工具调度 |
| 文本向量 | `qwen3.7-text-embedding` | 百炼当前推荐的高质量纯文本向量模型 |
| 向量维度 | `1024` | 通用场景下兼顾检索质量、存储和计算成本 |

## 本地配置

复制 `.env.example` 为 `.env`，只在本地填写：

    DASHSCOPE_API_KEY=你的百炼API-Key

默认使用华北 2（北京）的兼容地址：

    DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

如果创建 API Key 时控制台显示了专属的 API Host，应以控制台显示的地址为准，例如：

    https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1

API Key 与服务地域必须匹配。切换模型或向量维度后，已有文档向量必须全部重新生成。

## 安全要求

- API Key 只能写入 `.env` 或部署平台 Secret。
- `.env` 已被 Git 忽略，不得使用强制参数提交。
- 日志和管理接口只能展示“已配置/未配置”，不能返回密钥原文。
- 对话与 Embedding 使用同一把百炼 API Key，不在多个字段重复保存。

## 官方资料

- Function Calling：https://help.aliyun.com/zh/model-studio/qwen-function-calling
- Embedding：https://help.aliyun.com/zh/model-studio/embedding
- 获取 API Key：https://help.aliyun.com/zh/model-studio/get-api-key
