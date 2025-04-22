# 使用 Docker 部署 Gemini 轮询魔改版教程 由 **[北极星星](https://github.com/beijixingxing)** 编写

> # docker部署教程
> - ## 首先下载docker部署所必须的配置文件
> - ### [.env文件下载](https://github.com/beijixingxing/hajimi/blob/main/wiki/.env)
> - ### [docker-compose.yaml文件下载](https://github.com/beijixingxing/hajimi/blob/main/wiki/docker-compose.yaml)
> 
> ## 本地部署（桌面版）
> ### 准备工作
> 安装Docker：从[官方下载](https://www.docker.com/)并按提示完成安装。
> ### 3步快速部署
> 1. **创建项目文件夹**
>     - Mac/Linux：在终端执行`mkdir ~/Desktop/hajimi-app`
>     - Windows：在命令提示符或PowerShell执行`mkdir C:\Users\<用户名>\Desktop\hajimi-app`（替换`<用户名>`）
>     - **也可直接在桌面创建hajimi-app文件夹，将下载后的配置文件解压，上传到hajimi文件夹中**
> 2. **配置环境变量(.env)**：修改`hajimi-app`文件夹.env文件，主要修改以下内容
> ```env
> GEMINI_API_KEYS = key1,key2,key3 #替换为真实密钥，用逗号分隔
> PASSWORD = your_login_password # 设置登录密码
> ```
> 3. **修改端口/代理及并发请求配置**：在`hajimi-app`文件夹打开docker-compose.yaml文件按需修改
> ```yaml
> ports:
>   - "7860:7860" #端口冲突时改左侧端口
> environment:
>  HTTP_PROXY: "http://127.0.0.1:7890" # 启用代理，按需修改
>  HTTPS_PROXY: "http://127.0.0.1:7890" # 启用代理，按需修改
### 启用vertex
>   ENABLE_VERTEX=true 
### 填入完整的Google凭证JSON，注意填写进英文分号中间。
>   GOOGLE_CREDENTIALS_JSON='json密钥' 
 ### 启动服务
> 在终端执行（修改成自己的文件夹路径）
> ```bash
> cd ~/Desktop/hajimi-app 
> docker-compose up -d 
> ```
> 访问`http://localhost:7860`
> 
> ## 服务器部署（SSH版）
> 1. 用SSH工具连接到服务器
> 2. 执行`mkdir -p /volume1/docker/hajimi-app && cd $_` 创建并进入目录（改成自己的文件夹路径，也可直接创建）
> 3. 上传.env和docker-compose.yaml配置文件后执行`docker-compose up -d`启动服务 **（配置文件修改同桌面版一致）** 

> ## Compose部署（NAS版）
> 1.在docker文件夹内创建hajimi文件夹
> 2.上传.env和docker-compose.yaml配置文件 **（配置文件修改同桌面版一致）** 
> 3.进入Compose选择hajimi文件夹导入docker-compose.yaml
文件点击部署并运行

**登录`http://localhost:7860`验证，正常则通过`http://<服务器IP>:7860`（替换IP）外网访问**
> 
> ## 常见问题
> ### Q1:端口冲突
> - Mac/Linux：`lsof -i :7860`
> - Windows：`netstat -ano | findstr "7860"`
> **解决方案**：修改`docker-compose.yaml`中的`7860`为其他端口，如`17860`
> ### Q2:代理设置
> - 不需要代理：删除或注释`HTTP_PROXY`相关配置
> - 需要修改：替换为实际代理地址，如`http://192.168.1.100:8080`
> 
## 更新指南
### docker-compose.yaml文件已内置自动更新容器，默认每一小时检测一次，有更新会自动更新。

### 手动更新如下（文件夹路径修改成自己的）：
```
# 进入 docker-compose.yaml 所在目录
cd /volume3/docker/hajimi

# 停止并删除容器、网络等资源，同时删除所有相关镜像
docker-compose down --rmi all

# 拉取最新镜像（此时已清除旧镜像）
docker-compose pull

# 重新创建容器并启动
docker-compose up -d
```
> **提示**：首次部署用默认配置，稳定后再调整参数。
