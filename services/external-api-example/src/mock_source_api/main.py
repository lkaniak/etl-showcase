import json
import os
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Query
from typing import Annotated

app = FastAPI(title="Mock Source API")
_seed_env = os.getenv("SEED_MOCK_API_PATH")
SEED_PATH = Path(_seed_env) if _seed_env else Path(__file__).resolve().parents[4] / "scripts" / "seed_mock_api.json"
DATA = json.loads(SEED_PATH.read_text()) if SEED_PATH.exists() else {"orders": {}, "traffic": {}, "products": {}}


def _in_range(value: str, start: str, end: str) -> bool:
    return start <= value <= end


@app.get("/sellers/{seller_id}/orders")
def get_orders(
    seller_id: str,
    from_date: Annotated[str, Query(alias="from")] = "",
    to: str = "",
):
    orders = DATA.get("orders", {}).get(seller_id, [])
    filtered = [row for row in orders if _in_range(str(row.get("date", ""))[:10], from_date, to)]
    return filtered


@app.get("/sellers/{seller_id}/traffic")
def get_traffic(
    seller_id: str,
    from_date: Annotated[str, Query(alias="from")] = "",
    to: str = "",
):
    traffic = DATA.get("traffic", {}).get(seller_id, [])
    filtered = [row for row in traffic if _in_range(str(row.get("date", ""))[:10], from_date, to)]
    return filtered


@app.get("/sellers/{seller_id}/products")
def get_products(
    seller_id: str,
    from_date: Annotated[str, Query(alias="from")] = "",
    to: str = "",
):
    products = DATA.get("products", {}).get(seller_id, [])
    filtered = [row for row in products if _in_range(str(row.get("date", ""))[:10], from_date, to)]
    return filtered


@app.get("/health")
def health():
    return {"status": "ok", "date": date.today().isoformat()}
