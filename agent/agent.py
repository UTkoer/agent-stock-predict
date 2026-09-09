"""Multi-model stock predictor using local data and an MCP Markdown writer."""

import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = PROJECT_ROOT / "mcp" / "mcp_server.py"
AGENT_CONFIG = Path(__file__).resolve().parent / "agent_config.json"
PROJECT_CONFIG = PROJECT_ROOT / "config.json"
SYMBOLS_CONFIG = PROJECT_ROOT / "data" / "symbols.json"
PROMPTS_CONFIG = Path(__file__).resolve().parent / "prompt" / "addtional_prompt.json"
STOCKS_DIR = PROJECT_ROOT / "data" / "stocks"
PREDICT_DIR = PROJECT_ROOT / "data" / "predict"


def default_date_range() -> tuple[str, str]:
    # ``auto`` means the next calendar day (the day being predicted).
    end = date.today() + timedelta(days=1)
    return (end - timedelta(days=30)).strftime("%Y%m%d"), end.strftime("%Y%m%d")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return data


def load_enabled_models() -> list[dict[str, Any]]:
    models = _load_json(AGENT_CONFIG).get("models", [])
    enabled = [item for item in models if isinstance(item, dict) and item.get("enabled")]
    if not enabled:
        raise RuntimeError("No enabled models found in agent_config.json")
    return enabled


def resolve_prediction_config() -> tuple[str, list[str], str, int]:
    """Resolve rule_config before any model or MCP process is started."""
    # Runtime rules live in the project-level config.json; retain a fallback
    # to agent_config.json for backwards compatibility.
    config_source = PROJECT_CONFIG if PROJECT_CONFIG.exists() else AGENT_CONFIG
    rules = _load_json(config_source).get("rule_config", {})
    symbols_config = _load_json(SYMBOLS_CONFIG)
    prompts_config = _load_json(PROMPTS_CONFIG)
    if not isinstance(rules, dict):
        raise ValueError("rule_config must be an object")
    date_rule = rules.get("predict_date", "auto")
    predict_date = (date.today() + timedelta(days=1)).strftime("%Y%m%d") if date_rule == "auto" else str(date_rule)
    datetime.strptime(predict_date, "%Y%m%d")
    stock_rule = rules.get("predict_stocks", "default_symbols")
    symbols = symbols_config.get("default_symbols", []) if stock_rule == "default_symbols" else stock_rule
    if not isinstance(symbols, list) or not all(isinstance(symbol, str) for symbol in symbols):
        raise ValueError("predict_stocks must be default_symbols or a list of stock codes")
    prompt_rule = rules.get("addtional_prompt", rules.get("additional_prompt", ""))
    prompt = prompts_config.get(prompt_rule, "") if isinstance(prompt_rule, str) else prompt_rule
    if not isinstance(prompt, str):
        raise ValueError("addtional_prompt must resolve to a string")
    lookback = rules.get("lookback_days", 30)
    if not isinstance(lookback, int) or lookback <= 0:
        raise ValueError("lookback_days must be a positive integer")
    return predict_date, symbols, prompt, lookback


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "model"


def query_recent_stock_data(stock_code: str, latest_date: str, limit: int = 30) -> str:
    try:
        cutoff = datetime.strptime(latest_date, "%Y%m%d")
    except ValueError:
        return json.dumps({"success": False, "error": "latest_date must be YYYYMMDD"})
    directory = STOCKS_DIR / stock_code.upper()
    if not directory.is_dir():
        return json.dumps({"success": False, "error": f"No data directory: {directory}"})
    records = []
    for path in sorted(directory.glob("*.json")):
        if re.fullmatch(r"\d{8}", path.stem) and datetime.strptime(path.stem, "%Y%m%d") <= cutoff:
            records.append(json.loads(path.read_text(encoding="utf-8")))
    records = records[-limit:]
    return json.dumps({"success": bool(records), "stock_code": stock_code.upper(),
                       "count": len(records), "data": records}, ensure_ascii=False)


def latest_local_date(stock_code: str, predict_date: str) -> str:
    directory = STOCKS_DIR / stock_code.upper()
    cutoff = datetime.strptime(predict_date, "%Y%m%d")
    dates = [path.stem for path in directory.glob("*.json") if re.fullmatch(r"\d{8}", path.stem)
             and datetime.strptime(path.stem, "%Y%m%d") <= cutoff]
    if not dates:
        raise FileNotFoundError(f"No local data for {stock_code} on or before {predict_date}")
    return max(dates)


def _prediction_from_object(value: Any, fallback: str) -> tuple[str, float | None, str, str] | None:
    """Convert a valid model response object into the persisted prediction fields."""
    if not isinstance(value, dict):
        return None
    direction = str(value.get("prediction", "")).upper()
    if direction not in {"UP", "DOWN"}:
        return None
    raw_confidence = value.get("confidence")
    confidence: float | None = None
    if isinstance(raw_confidence, (int, float, str)) and not isinstance(raw_confidence, bool):
        try:
            confidence = float(raw_confidence)
        except ValueError:
            pass
    if confidence is not None and not 0 <= confidence <= 1:
        confidence = None
    return direction, confidence, str(value.get("reasoning", fallback)), str(value.get("report", ""))


def _parse_prediction(text: str) -> tuple[str, float | None, str, str]:
    """Parse a prediction even when a provider wraps JSON in reasoning tags."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S)
    try:
        parsed = _prediction_from_object(json.loads(cleaned), text)
        if parsed:
            return parsed
    except json.JSONDecodeError:
        pass

    # Some reasoning-capable providers emit the requested object inside
    # ``<reasoning>``. Decode each object candidate rather than persisting it
    # verbatim as the short reasoning field.
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", cleaned):
        try:
            value, _ = decoder.raw_decode(cleaned[match.start():])
        except json.JSONDecodeError:
            continue
        parsed = _prediction_from_object(value, text)
        if parsed:
            return parsed

    # A provider may stream an otherwise complete object without its final
    # closing brace. Recover only the known response fields, with JSON string
    # decoding retained for escaped report content.
    direction_match = re.search(r'"prediction"\s*:\s*"(UP|DOWN)"', cleaned, re.I)
    if direction_match:
        def string_field(name: str) -> str:
            match = re.search(rf'"{name}"\s*:\s*("(?:\\.|[^"\\])*")', cleaned, re.S)
            if not match:
                return ""
            try:
                return str(json.loads(match.group(1)))
            except json.JSONDecodeError:
                return ""

        confidence_match = re.search(r'"confidence"\s*:\s*(-?(?:\d+(?:\.\d*)?|\.\d+))', cleaned)
        try:
            confidence = float(confidence_match.group(1)) if confidence_match else None
        except ValueError:
            confidence = None
        if confidence is not None and not 0 <= confidence <= 1:
            confidence = None
        return direction_match.group(1).upper(), confidence, string_field("reasoning") or text, string_field("report")
    return "UNKNOWN", None, text, ""


def _save_result(model: str, stock: str, predict_date: str, direction: str,
                 confidence: float | None, reasoning: str) -> None:
    path = PREDICT_DIR / _safe_name(model) / "results" / f"{_safe_name(stock)}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    except (OSError, json.JSONDecodeError):
        existing = []
    records = [item for item in existing if isinstance(item, dict)] if isinstance(existing, list) else []
    old = next((item for item in records if item.get("predict_date") == predict_date), {})
    records = [item for item in records if item.get("predict_date") != predict_date]
    records.append({"predict_date": predict_date, "prediction": direction, "confidence": confidence,
                    "reasoning": reasoning, "actual": old.get("actual"), "correct": old.get("correct"),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


async def build_agent(model_config: dict[str, Any], internal_tool):
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent
    from pydantic import SecretStr

    key_env = model_config.get("api_key_env", "OPENAI_API_KEY")
    api_key = os.getenv(key_env)
    model_id = model_config.get("basemodel") or model_config.get("signature")
    if not isinstance(api_key, str) or not api_key or not isinstance(model_id, str):
        raise RuntimeError(f"Invalid API configuration for {model_config.get('name', 'model')}")
    model = ChatOpenAI(model=model_id, api_key=SecretStr(api_key),
                       base_url=model_config.get("openai_base_url"), temperature=0)
    # Reports are persisted by this module after parsing the final response.
    # Do not expose the writer to the model: it otherwise chooses arbitrary
    # paths and may save a report before its structured response is complete.
    return create_react_agent(model, [internal_tool])


async def predict_stock(stock_code: str | None = None, start_date: str | None = None,
                        end_date: str | None = None, model_name: str | None = None) -> dict[str, str]:
    from langchain_core.tools import tool

    print("Reading prediction configuration...")
    config_date, config_symbols, additional_prompt, lookback = resolve_prediction_config()
    predict_date = end_date or config_date
    symbols = [stock_code] if stock_code else config_symbols
    print(f"Loaded {len(symbols)} stock symbol(s); lookback: {lookback} days.")

    @tool
    def query_stock_data(code: str, latest_date: str) -> str:
        """读取指定股票在截止日期前的最近交易日数据。"""
        return query_recent_stock_data(code, latest_date, lookback)

    models = load_enabled_models()
    if model_name:
        models = [item for item in models if item.get("name") == model_name]
    if not models:
        raise ValueError("No matching enabled models")
    from contextlib import AsyncExitStack
    from langchain_mcp_adapters.tools import load_mcp_tools
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    print("正在启动MCP服务（本批次任务共用）...")
    server_parameters = StdioServerParameters(command=sys.executable, args=[str(MCP_SERVER)])
    stack = AsyncExitStack()
    read_stream, write_stream = await stack.enter_async_context(stdio_client(server_parameters))
    session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
    await session.initialize()
    mcp_tools = await load_mcp_tools(session, server_name="writer")
    writer = next((item for item in mcp_tools if getattr(item, "name", "") == "md_write"), None)
    if writer is None:
        await stack.aclose()
        raise RuntimeError("md_write MCP tool is unavailable")
    predictions: dict[str, str] = {}
    for stock in symbols:
        latest_date = latest_local_date(stock, predict_date)
        for config in models:
            label = str(config.get("name") or config.get("basemodel"))
            key = f"{stock}:{label}"
            try:
                print(f"预测进行中：{stock}，模型：{label}...")
                agent = await build_agent(config, query_stock_data)
                prompt = f"""你是一名股票技术分析专家。请先使用内部工具 query_stock_data 读取股票 {stock} 截止 {latest_date} 的最近 {lookback} 个交易日数据。
预测日期为 {predict_date}（下一个交易日）。只能依据工具返回的数据，不得编造任何价格、成交量或日期。
额外要求：{additional_prompt}

必须严格输出一个 JSON 对象，不得使用 Markdown 代码围栏，不得输出 JSON 之外的任何文字：
{{
  "prediction": "UP 或 DOWN",
  "confidence": 0.0到1.0之间的数字,
  "reasoning": "不超过80字的简短分析",
  "report": "完整的中文 Markdown 技术分析报告"
}}

其中 reasoning 只能是简短结论；report 必须严格遵循以下模板，标题、顺序、字段名称和层级不得有任何变化，只填写具体数据。不得增加或删除章节，不得改变标点：
# {stock}技术分析报告
**分析日期：yymmdd**  
**数据范围：yymmdd-yymmdd（n个交易日）**

## 一、数据概览

### 价格走势分析
- **最新收盘价**：
- **n日价格区间**：
- **价格位置**：
- **趋势特征**：
### 成交量分析
- **平均成交量**：
- **最大成交量**：
- **量价关系**：
- **资金流向**：

## 二、技术信号分析

### 趋势分析
1. **短期趋势**：
2. **关键价位**：
   - 支撑位：
   - 阻力位：
3. **K线形态**：

### 量价关系深度分析
- **日期**：成交量和涨跌幅，并说明量价特征

### 技术指标解读
1. **动量指标**：
2. **支撑验证**：
3. **阻力测试**：

## 三、预测结论

### 短期走势判断
**看涨理由：**
1. **技术突破**：
2. **量价健康**：
3. **趋势形成**：
4. **空间存在**：

### 风险因素
1. **宏观影响**：
2. **技术阻力**：
3. **市场情绪**：

### 综合评估
基于技术分析，给出综合判断并列出关键信号：
- 
- 
- 
- 

**预测方向**：说明下一个交易日的走势判断及目标位。"""
                result = await agent.ainvoke({"messages": [("user", prompt)]})
                messages = result.get("messages", [])
                raw = messages[-1].content if messages else "Agent returned no result."
                raw = raw if isinstance(raw, str) else str(raw)
                direction, confidence, reasoning, report = _parse_prediction(raw)
                _save_result(label, stock, predict_date, direction, confidence, reasoning)
                report_path = PREDICT_DIR / _safe_name(label) / "markdown" / _safe_name(stock) / f"{datetime.strptime(predict_date, '%Y%m%d'):%y%m%d}.md"
                if not report.strip():
                    report = (f"# {stock}技术分析报告\n**分析日期：{predict_date[2:]}**  \n"
                              f"**数据范围：{latest_date[2:]}-{latest_date[2:]}（1个交易日）**\n\n"
                              "## 一、数据概览\n\n### 价格走势分析\n- **最新收盘价**：数据不足\n- **n日价格区间**：数据不足\n- **价格位置**：数据不足\n- **趋势特征**：数据不足\n### 成交量分析\n- **平均成交量**：数据不足\n- **最大成交量**：数据不足\n- **量价关系**：数据不足\n- **资金流向**：数据不足\n\n"
                              "## 二、技术信号分析\n\n### 趋势分析\n1. **短期趋势**：数据不足\n2. **关键价位**：\n   - 支撑位：数据不足\n   - 阻力位：数据不足\n3. **K线形态**：数据不足\n\n### 量价关系深度分析\n- **日期**：数据不足\n\n### 技术指标解读\n1. **动量指标**：数据不足\n2. **支撑验证**：数据不足\n3. **阻力测试**：数据不足\n\n"
                              "## 三、预测结论\n\n### 短期走势判断\n**看涨理由：**\n1. **技术突破**：数据不足\n2. **量价健康**：数据不足\n3. **趋势形成**：数据不足\n4. **空间存在**：数据不足\n\n"
                              "### 风险因素\n1. **宏观影响**：请结合市场环境复核\n2. **技术阻力**：数据不足\n3. **市场情绪**：数据不足\n\n### 综合评估\n" + reasoning + "\n- 数据有限，需谨慎解读\n- 建议结合更多交易日复核\n- 关注支撑与阻力变化\n- 本报告仅供参考\n\n**预测方向**：" + direction)
                await writer.ainvoke({"file_path": str(report_path), "content": report})
                predictions[key] = raw
            except Exception as error:
                predictions[key] = f"Model failed: {error}"
    await stack.aclose()
    return predictions
