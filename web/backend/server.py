from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = ROOT / "web"
for path in (ROOT, WEB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from backend.services.mcp_tools import list_tools
from backend.services.models import list_models
from backend.services.predictions import read_predictions
from backend.services.prompts import read_prompt
from backend.services.stocks import list_symbols, read_stock

app = FastAPI(title="Agent Stock Predict API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/symbols")
def symbols():
    return {"symbols": list_symbols()}


@app.get("/api/stocks/{symbol}")
def stock_data(symbol: str, start_date: str | None = Query(None), end_date: str | None = Query(None)):
    try:
        return {"symbol": symbol, "data": read_stock(symbol, start_date, end_date)}
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/api/models")
def models():
    return {"models": list_models()}


@app.get("/api/mcp-tools")
def mcp_tools():
    return {"tools": list_tools()}


@app.get("/api/predictions")
def predictions(symbol: str | None = Query(None), model: str | None = Query(None)):
    return {"predictions": read_predictions(symbol, model)}


@app.get("/api/prompts")
def prompts():
    return read_prompt()


FRONT_DIR = WEB_DIR / "front"
app.mount("/", StaticFiles(directory=FRONT_DIR, html=True), name="front")
