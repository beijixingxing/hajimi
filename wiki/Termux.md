# Hajimi 项目部署指南（Termux + Ubuntu）

> 本文档旨在指导用户如何在 **Android 设备**上通过 **Termux + Ubuntu** 环境部署并使用 [Hajimi 项目](https://github.com/wyeeeee/hajimi)。

---

## 目录

1. [环境准备](#环境准备)  
2. [部署步骤](#部署步骤)  
3. [配置环境变量](#配置环境变量)  
4. [启动服务](#启动服务)  
5. [使用说明](#使用说明)  

---

## 环境准备

### 1. 下载并安装 Termux

请下载并安装以下版本的 Termux（支持 Android 7+）：

[termux-app_v0.119.0-beta.2.apk](https://github.com/termux/termux-app/releases/download/v0.119.0-beta.2/termux-app_v0.119.0-beta.2+apt-android-7-github-debug_arm64-v8a.apk)

### 2. 授权 Termux 权限

请务必授予 Termux 后台权限：

- **教程参考**：[轻弹窗](https://bearpopup.com/stable-guide)
- 其他权限请在手机系统设置中手动开启（如存储、悬浮窗等）。

---

## 部署步骤

### 步骤 1：安装 Ubuntu 系统

在 Termux 中执行以下命令：

```bash
apt update && apt --yes upgrade && apt --yes install wget curl proot tar && wget https://raw.githubusercontent.com/AndronixApp/AndronixOrigin/master/Installer/Ubuntu22/ubuntu22.sh -O ubuntu22.sh && chmod +x ubuntu22.sh && bash ubuntu22.sh
```

### 步骤 2：安装基本依赖

```bash
apt update && apt --yes upgrade && apt --yes install git python3 python3-pip
```

### 步骤 3：下载项目并安装依赖

```bash
git clone https://github.com/wyeeeee/hajimi && cd hajimi && pip install tzdata -r requirements.txt
```

---

## 配置环境变量

### 使用 **MT 管理器** 编辑 `.bashrc`

路径为：`ubuntu22-fs/root/.bashrc`  
在文件末尾添加如下环境变量配置，并根据实际需要修改值：

```bash
# 必填项
export GEMINI_API_KEYS=your_google_api_key1,your_google_api_key2

# 可选项
export PASSWORD=123
export MAX_REQUESTS_PER_MINUTE=30
export MAX_REQUESTS_PER_DAY_PER_IP=600
export FAKE_STREAMING=true
export API_KEY_DAILY_LIMIT=25
export BLOCKED_MODELS=gemini-2.5-pro-preview-03-25
export RANDOM_STRING=true
export RANDOM_STRING_LENGTH=20
export CONCURRENT_REQUESTS=1
export INCREASE_CONCURRENT_ON_FAILURE=1
export MAX_CONCURRENT_REQUESTS=3
export SEARCH_MODE=true
export SEARCH_PROMPT=使用搜索工具联网搜索，需要在content中结合搜索内容
```

---

### 环境变量说明

#### 必填环境变量

| 变量名            | 说明                                | 示例值                         |
|-------------------|-------------------------------------|-------------------------------|
| `GEMINI_API_KEYS` | Google AI Studio 获取的 API 密钥（可多个，用英文逗号分隔） | `key1,key2,key3`              |

#### 可选环境变量

| 变量名                         | 说明                                | 默认值    |
|-------------------------------|-------------------------------------|-----------|
| `PASSWORD`                    | 访问服务所需的密码                   | `123`     |
| `MAX_REQUESTS_PER_MINUTE`     | 每分钟最大请求数                     | `30`      |
| `MAX_REQUESTS_PER_DAY_PER_IP` | 每个 IP 每日请求上限                 | `600`     |
| `FAKE_STREAMING`              | 是否启用假流式传输模式               | `true`    |
| `API_KEY_DAILY_LIMIT`         | 单个 API 每天最大使用次数            | `25`      |
| `BLOCKED_MODELS`              | 屏蔽指定模型（多个用英文逗号分隔）   | 无        |
| `RANDOM_STRING`               | 是否启用伪装信息                     | `true`    |
| `RANDOM_STRING_LENGTH`        | 伪装信息的长度                       | `20`      |
| `CONCURRENT_REQUESTS`         | 默认并发请求数量                     | `1`       |
| `INCREASE_CONCURRENT_ON_FAILURE` | 请求失败后增加的并发数            | `1`       |
| `MAX_CONCURRENT_REQUESTS`     | 允许的最大并发请求数                 | `3`       |
| `SEARCH_MODE`                 | 是否启用联网搜索模式                 | `true`    |
| `SEARCH_PROMPT`               | 联网模式提示词（用于搜索上下文补充）| 自定义内容 |

> **提示**：表格可左右滑动查看完整内容（移动端）。

---

## 启动服务

### 步骤 1：进入 Ubuntu 系统

每次打开 Termux 后，执行以下命令进入 Ubuntu：

```bash
termux-wake-lock && chmod +x start-ubuntu22.sh && bash start-ubuntu22.sh
```

### 步骤 2：启动 Hajimi 服务

```bash
cd hajimi && git pull && uvicorn app.main:app --reload --host 127.0.0.1 --port 7860
```

> 可将以上两行命令保存为输入法快捷短语，方便快速启动。

---

## 使用说明

### 访问前端页面

打开浏览器，访问：

```
http://127.0.0.1:7860
```

> **注意**：该地址只能在本机访问。

### 接入 OpenAI 兼容前端（如酒馆）

在客户端中设置如下：

- **API 地址**：`http://127.0.0.1:7860/v1`
- **访问密码**：默认 `123`（可配置）
