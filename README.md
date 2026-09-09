# Agent stock prediction 
# 智能体股票预测

---
## 目前主要功能
### 1. 自选标的下载
### 2. 未来股票预测
---

## 快速开始
### 1. 下载压缩包或运行以下命令将仓库保存至本地:
``` shell
git clone https://github.com/UTkoer/agent-stock-predict.git
```

### 2. 环境创建与依赖下载
使用你喜欢的工具创建虚拟环境`python=3.12`.

在根目录`agent-stock-predict\`下运行:

``` shell
pip install -r requirements.txt
``` 
此命令将安装所需的外部库

打开`.env.example`文件,填写所需api_key后将此文件名称改为`.env`

### 3. 打开可视化界面

在根目录`agent-stock-predict\`下运行:
```shell
uvicorn web.backend.server:app --reload --port 8000
```

---
## 项目结构


