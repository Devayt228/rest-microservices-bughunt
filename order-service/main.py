import os
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
import httpx

app = FastAPI(title="OrderService")

AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8001")
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://localhost:8002")

ORDERS: list[dict] = []


@app.post("/orders")
async def create_order(payload: dict, authorization: str | None = Header(default=None)):
    """
    Очікуваний payload: {"productId": int, "qty": int}
    """
    # (Намагаємось) перевірити токен
    async with httpx.AsyncClient() as client:
        _ = await client.get(f"{AUTH_URL}/whoami", headers={"Authorization": authorization or ""})

    order = {
        "order_id": len(ORDERS) + 1,
        "product_id": payload.get("productId"),
        "quantity": payload.get("qty"),
        "status": "created",
    }
    ORDERS.append(order)
    return JSONResponse(order, status_code=201)


@app.get("/orders")
async def list_orders():
    return {"orders": ORDERS}
