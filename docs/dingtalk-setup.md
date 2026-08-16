# 钉钉 Stream 长连接机器人接入指南

本项目采用钉钉官方最新的 **Stream 模式（长连接 WebSocket）**，机器人主动向钉钉开放平台建立双向长连接，**完全无需公网 IP、无需域名、无需内网穿透**，本机或 Docker 容器即可直接稳定运行。

---

## 一、钉钉开发者后台配置步骤

1. **创建企业内部应用**：
   - 登录 [钉钉开放平台](https://open-dev.dingtalk.com/) ➡️ 进入 **「开发者后台」** ➡️ 选择企业组织 ➡️ 点击 **「创建内部应用」**。
   - 应用名称填写 `小苏企业智能助手`，应用描述填写 `企业制度、员工、考勤与订单智能问答助手`。
2. **添加机器人能力**：
   - 在应用详情左侧导航栏点击 **「添加应用能力」** ➡️ 选择 **「机器人」** 并确认添加。
   - 在机器人配置页面中，消息接收模式必须选择 **【Stream 模式】**（无需填写任何公网 Webhook 回调地址）。
3. **获取凭证信息**：
   - 进入 **「凭证与基础信息」** 页面，复制 **`AppKey` (即 Client ID)** 与 **`AppSecret` (即 Client Secret)**。
4. **发布应用版本**：
   - 在 **「版本管理与发布」** 中创建新版本，设置使用范围为“全部员工”或测试部门，点击发布上线。

---

## 二、项目本地配置 (`.env`)

在项目根目录的 `.env` 中填入钉钉凭证：

```dotenv
# 钉钉应用 AppKey 与 AppSecret
DINGTALK_CLIENT_ID=dingxxxxxxxxxxxxxxxx
DINGTALK_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 前端 Web 访问根地址（用于在钉钉中生成可点击的原文定位直达链接）
PUBLIC_BASE_URL=http://localhost:5173
```

---

## 三、启动与运行状态检查

1. **一键启动机器人服务**：
   ```bash
   docker compose --profile dingtalk up -d --build bot
   ```
2. **查看机器人连接与运行日志**：
   ```bash
   docker compose logs -f bot
   ```
   当看到 `[Stream] connected to dingtalk gateway successfully` 时，即代表已成功连接钉钉云端网关。
3. **管理后台心跳监测**：
   - 登录 Web 管理后台 ➡️ **「系统设置」** 页面；
   - 查看「钉钉 IM 集成」卡片，系统会实时展示 **凭证状态（已配置）**、**运行状态（正在运行）** 以及 **最近心跳时间**。

---

## 四、钉钉群聊与单聊测试

1. **单聊测试**：在钉钉工作台搜索 `小苏企业智能助手`，直接发送：“公司员工有几天年假？”、“张伟上周出勤了几天？”。
2. **群聊测试**：将机器人拉入企业内部群聊，在群内 `@小苏企业智能助手` 发送提问，机器人将自动调用相关知识库/内部系统工具，并携带高亮原文链接进行结构化回复。
