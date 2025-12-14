from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="ProductService")

# FIX БАГ 4: price тепер float замість string
PRODUCTS = [
    {"product_id": 100, "name": "Keyboard", "price": 59.99, "inStock": 5},
    {"product_id": 101, "name": "Mouse", "price": 29.99, "inStock": 0},
]


@app.get("/products")
async def list_products():
    return {"items": PRODUCTS}


@app.get("/products/{pid}")
async def get_product(pid: int):
    """
    FIX БАГ 5: Повертає 404 для неіснуючого товару

    Було: status_code=200 для не знайденого
    Стало: status_code=404 Not Found
    """
    for p in PRODUCTS:
        if p["product_id"] == pid:
            return p

    # FIX: Змінено 200 на 404
    return JSONResponse(
        {"message": "not found"},
        status_code=404
    )
