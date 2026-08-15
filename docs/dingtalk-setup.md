# 钉钉 Stream 机器人接入

## 1. 创建应用

1. 登录钉钉开放平台，进入开发者后台。
2. 在测试组织中创建“企业内部应用”。
3. 应用名称可填写“小苏企业智能助手”，描述可填写“查询公司制度、员工、考勤和订单数据的内部 AI 助手”。
4. 在应用能力中添加机器人，消息接收模式选择 **Stream 模式**。
5. 保存应用的 Client ID 与 Client Secret，只写入本机 `.env`。

## 2. 权限与版本

启用机器人收发消息所需权限，在“版本管理与发布”中新建版本，选择可见范围并发布。未发布版本时，后台修改不会对测试组织生效。

## 3. 本地配置

```dotenv
DINGTALK_CLIENT_ID=dingxxxxxxxx
DINGTALK_CLIENT_SECRET=xxxxxxxx
PUBLIC_BASE_URL=https://demo.example.com
```

`PUBLIC_BASE_URL` 用于把知识引用转换成钉钉中可点击的管理后台链接。本地联调可以保留 `http://localhost:5173`，但其他人的钉钉客户端无法访问你的 localhost。

## 4. 启动和验证

```bash
docker compose --profile dingtalk up --build -d
docker compose logs -f bot
```

日志出现 `Starting DingTalk Stream client` 表示开始连接。在钉钉中私聊机器人或在群中 @ 小苏，依次测试：

1. `员工 001 是哪个部门的？`
2. `他上周来上班几天？`
3. `员工每年有几天年假？`
4. `现在几点？`

## 5. 常见问题

- 收不到消息：确认机器人版本已发布、可见范围包含测试用户、Stream 模式已开启。
- 一直提示模型异常：检查 `DASHSCOPE_API_KEY` 与 Base URL 是否属于同一地域。
- 引用打不开：将 `PUBLIC_BASE_URL` 改成钉钉客户端可访问的 HTTPS 域名。
- 修改 `.env` 不生效：执行 `docker compose --profile dingtalk up -d --force-recreate api bot`。

参考：[钉钉 Stream SDK Python](https://github.com/open-dingtalk/dingtalk-stream-sdk-python)。
