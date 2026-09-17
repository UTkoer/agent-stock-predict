# Agent stock prediction 
# 智能体股票预测

---
## 目前主要功能
### 1. 自选标的下载
### 2. 未来股票预测
---

## 快速开始
### 1. 本地部署:
``` shell
git clone https://github.com/UTkoer/agent-stock-predict.git
```
---
### 2. 环境创建与依赖下载
使用你喜欢的工具创建虚拟环境`python=3.12`.

在根目录`agent-stock-predict\`下运行:

``` shell
pip install -r requirements.txt
``` 
此命令将安装所需的外部库

打开`.env.example`文件,填写所需api_key后将此文件名称改为`.env`

---
### 3. 编辑标的

进入 `agent-stock-predict\data\`目录,打开`symbols.json`文件,文件内容如下:
```json
{
    "default_symbols":[
        "000975.SZ",
        "601166.SH",
        "600276.SH",
        "600030.SH"
    ]
}
```
<br>

可以直接在数组中新增标的分组:
```json
{
    "default_symbols":[
        "000975.SZ",
        "601166.SH",
        "600276.SH",
        "600030.SH"
    ],
    "custom_symbols_1":[
        "stock_code_1",
        "stock_code_2"
    ]
}
```
---
### 4. 下载股票数据
项目默认采用`tushare`和`akshare`两类数据源,优先调用`tushare`,调用失败后再自动切换使用`akshare`. 使用`tushare`数据源前请在`.env`中配置`TUSHARE_TOKEN`.
<br>
##### 数据下载:
进入目录`agent-stock-predict\data\`:
- 不带参数运行:
    ```
    python get_data.py
    ```
    这将下载`symbols.json`中所有股票从**本日**止默认**30**个交易日的日线数据.
<br>
- 指定起止时间运行:
    ```
    python get_data.py --start-date 20260801 --end-date 20260831
    ``` 
    这将下载从**2026年8月1日**到**2026年8月31日**内所有交易日的日线数据.
<br>
- 指定起始时间运行:
    ```
    python get_data.py --start-date 20260101
    ```
    这将下载从**2026年1月1日**到**本日**内所有交易日的日线数据.

下载的股票数据将保存在`agent-stock-predict\data\stocks\<股票代码>\`下以`<YYMMDD>.json`单文件格式保存.

---
### 5. 运行预测
---
### 6. 打开可视化界面

在根目录`agent-stock-predict\`下运行:
```shell
uvicorn web.backend.server:app --reload --port 8000
```
---
## 项目结构


