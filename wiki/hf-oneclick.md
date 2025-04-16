# huggingface单文件自动更新版

## 前言
1. 从这里开始默认你已有Huggingface账号且懂文件上传or复制space，如果不会去看其他教程学明白了再来
2. 你可以直接复制我的huggingface space或者自己上传项目根目录下hf文件夹里的Dockerfile文件

### 自行上传dockerfile
* 新建space，创建后依次点击files、add file、upload files
* 上传项目目录下hf文件夹内的Dockerfile，不要上传build文件夹的dockerfile
* 之后按标准huggingface教程配置环境变量即可
### 这是第二种方法
* 当然你也可以选择点击files、add file、create a new file
* 文件名填'Dockerfile'，文件内容填
```
FROM ghcr.io/rzline/hajimi:latest

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```
* 之后按标准huggingface教程配置环境变量即可

### 复制space
* [space地址](https://huggingface.co/spaces/rzline/hajimi)
* 选择duplicate this space
* 按抱脸给出的模板填入环境变量即可