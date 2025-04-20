# 🚀 HAJIMI Gemini API Proxy

这是一个基于 FastAPI 构建的 Gemini API 代理，旨在提供一个简单、安全且可配置的方式来访问 Google 的 Gemini 模型。适用于在 Hugging Face Spaces 上部署，并支持openai api格式的工具集成。

# 本项目基于CC BY-NC 4.0许可开源，需遵守以下规则
- 您必须给出适当的署名，提供指向本协议的链接，并指明是否（对原作）作了修改。您可以以任何合理方式进行，但不得以任何方式暗示许可方认可您或您的使用。
- 您不得将本作品用于商业目的，包括但不限于任何形式的商业倒卖、SaaS、API 付费接口、二次销售、打包出售、收费分发或其他直接或间接盈利行为。

### 如需商业授权，请联系原作者获得书面许可。违者将承担相应法律责任。

### 感谢[@warming-afternoon](https://github.com/warming-afternoon)，[@任梓樂](https://github.com/rzline)在技术上的大力支持

###  使用文档
- [Claw Cloud部署的使用文档（推荐，免费，手机电脑均可使用）](./wiki/claw.md) 感谢[@IDeposit](https://github.com/IDeposit)编写
- [docker部署的使用文档（服务器自建使用）](./wiki/docker.md) 感谢[@北极星星](https://github.com/beijixingxing)编写
- [termux部署的使用文档（手机使用）](./wiki/Termux.md) 感谢[@天命不又](https://github.com/tmby)编写
- [zeabur部署的使用文档(需付费)](./wiki/zeabur.md) 感谢**墨舞ink**编写
- [huggingface部署的使用文档](./wiki/huggingface.md)
- [vertex模式的使用文档](./wiki/vertex.md)

###  更新日志
* v0.1.5
    * 实现vertex热切换，现在在前端面板就可以切换vertex模式与ai studio模式了
    * 为vertex模式实现假流式，环境变量与ai studio模式的假流式相同，均为`FAKE_STREAMING`
    * 优化前端界面
    * 修复若干bug
* v0.1.4beta
    * 为大部分配置项适配热更新，可实时调整配置
    * 前端界面新增适配热更新相关ui界面，可直接调整配置（在前端界面修改的数据在重启后会失效）
    * 适配 vertex ai（基于gzzhongqi/vertex2openai项目开发），在启用vertex模式并配置vertex凭证后，项目将切换为vertex请求模式
    * 新增环境变量`ENABLE_VERTEX`用于启用vertex模式，初始默认为false
    * 新增环境变量`GOOGLE_CREDENTIALS_JSON`用于配置vertex凭证，默认为空



* 历史版本更新日志请查看[update](./wiki/update.md)

## ✨ 主要功能：

### 🔑 API 密钥轮询和管理

### 📑 模型列表接口

### 💬 聊天补全接口：

*   提供 `/v1/chat/completions` 接口，支持流式（streaming）和非流式响应，与 OpenAI API 格式兼容。
*   自动将 OpenAI 格式的请求转换为 Gemini 格式。

### 🔒 密码保护（可选）：

*   通过 `PASSWORD` 环境变量设置密码。
*   提供默认密码 `"123"`。

### 🚦 速率限制和防滥用：

*   通过环境变量自定义限制：
    *   `MAX_REQUESTS_PER_MINUTE`：每分钟最大请求数（默认 30）。
    *   `MAX_REQUESTS_PER_DAY_PER_IP`：每天每个 IP 最大请求数（默认 600）。
*   超过速率限制时返回 429 错误。

### 🧩 服务兼容

*   提供的接口与 OpenAI API 格式兼容,便于接入各种服务

## ⚠️ 注意事项：

*   **强烈建议在生产环境中设置 `PASSWORD` 环境变量，并使用强密码。**
*   根据你的使用情况调整速率限制相关的环境变量。
*   确保你的 Gemini API 密钥具有足够的配额。
