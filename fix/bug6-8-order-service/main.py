import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx

app = FastAPI(title="OrderService")

AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8001")
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://localhost:8002")

ORDERS: list[dict] = []


class OrderRequest(BaseModel):
    """Модель для запиту створення замовлення"""
    productId: int
    qty: int


@app.post("/orders")
async def create_order(
    payload: OrderRequest,
    authorization: str | None = Header(default=None)
):
    """
    FIX БАГ 6: Додана перевірка авторизації
    FIX БАГ 7: Додана перевірка існування товару
    FIX БАГ 8: Додана перевірка запасів

    Створює замовлення з повною валідацією
    """
    async with httpx.AsyncClient() as client:
        # FIX БАГ 6: Перевірка авторизації
        try:
            auth_response = await client.get(
                f"{AUTH_URL}/whoami",
                params={"authorization": authorization or ""}
            )

            # Перевіряємо статус відповіді
            if auth_response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid or missing token"
                )

            # Отримуємо email користувача
            user_data = auth_response.json()
            user_email = user_data.get("email")

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Auth service unavailable: {str(e)}"
            )

        # FIX БАГ 7: Перевірка існування товару
        try:
            product_response = await client.get(
                f"{PRODUCT_URL}/products/{payload.productId}"
            )

            if product_response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with ID {payload.productId} not found"
                )

            if product_response.status_code != 200:
                raise HTTPException(
                    status_code=503,
                    detail="Product service error"
                )

            product = product_response.json()

        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Product service unavailable: {str(e)}"
            )

        # FIX БАГ 8: Перевірка запасів
        in_stock = product.get("inStock", 0)
        if in_stock < payload.qty:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {in_stock}, requested: {payload.qty}"
            )

    # Створюємо замовлення
    order = {
        "order_id": len(ORDERS) + 1,
        "product_id": payload.productId,
        "quantity": payload.qty,
        "status": "created",
        "user_email": user_email  # Додаємо інформацію про користувача
    }
    ORDERS.append(order)

    return JSONResponse(order, status_code=201)


@app.get("/orders")
async def list_orders():
    """Отримати список всіх замовлень"""
    return {"orders": ORDERS}
