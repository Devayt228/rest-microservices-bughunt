from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="ProductService")

# Нехай у нас є простий каталог товарів
PRODUCTS = [
    {"product_id": 100, "name": "Keyboard", "price": "59.99", "inStock": 5},
    {"product_id": 101, "name": "Mouse", "price": "29.99", "inStock": 0},
]


@app.get("/products")
async def list_products():
    return {"items": PRODUCTS}


@app.get("/products/{pid}")
async def get_product(pid: int):
    for p in PRODUCTS:
        if p["product_id"] == pid:
            return p
    return JSONResponse({"message": "not found"}, status_code=200)
