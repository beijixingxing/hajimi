# 使用 Docker 部署 Gemini 轮询魔改版教程 由 **北极星星** 编写

> # docker部署教程
> - [配置文件下载]([https://discord.com/channels/1134557553011998840/1358123054307217485/1363527369284911224](https://github.com/beijixingxing/hajimi/releases/download/%E6%96%87%E4%BB%B6/docker.zip))
> 
> ## 本地部署（桌面版）
> ### 准备工作
> 安装Docker：从[官方下载](https://www.docker.com/)并按提示完成安装。
> ### 3步快速部署
> 1. **创建项目文件夹**
>     - Mac/Linux：在终端执行`mkdir ~/Desktop/hajimi-app`
>     - Windows：在命令提示符或PowerShell执行`mkdir C:\Users\<用户名>\Desktop\hajimi-app`（替换`<用户名>`）
> 2. **配置环境变量(.env)**：在`hajimi-app`文件夹创建.env文件，内容如下
> ```env
> GEMINI_API_KEYS = key1,key2,key3 #替换为真实密钥，用逗号分隔
> PASSWORD = your_login_password #设置登录密码
> ```
> 3. **修改端口/代理及并发请求配置(docker-compose.yaml)**：在`hajimi-app`文件夹找到该文件按需修改
> ```yaml
> ports:
>   - "7860:7860" #端口冲突时改左侧端口
> environment:
>   #HTTP_PROXY: "http://localhost:7890"  #取消注释启用代理
>   #HTTPS_PROXY: "http://localhost:7890"
>   CONCURRENT_REQUESTS: 2 #默认并发请求数，按需修改次数。
>   INCREASE_CONCURRENT_ON_FAILURE: 1 #失败时增加的并发数，按需修改次数。
>   MAX_CONCURRENT_REQUESTS: 5 #最大并发请求数，按需修改次数。
> ```
> ### 启动服务
> 在终端执行
> ```bash
> cd ~/Desktop/hajimi-app 
> docker-compose up -d 
> ```
> 访问`http://localhost:7860`
> 
> ## 服务器部署（SSH版）
> 1. 用SSH工具连接到服务器
> 2. 执行`mkdir -p /volume1/docker/hajimi-app && cd $_` 创建并进入目录（改成自己的文件夹路径）
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
> ## 更新指南
```进入项目文件夹，根据需求在SSH终端输入下面指令：
#从 Docker 镜像仓库拉取最新的镜像，更新到最新版本
docker-compose pull
#管理的所有容器，完成更新部署
docker-compose up -d```
> ```
> **提示**：首次部署用默认配置，稳定后再调整参数。
