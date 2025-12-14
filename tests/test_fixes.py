"""
Тести для перевірки, що баги виправлено
Запускати ПІСЛЯ застосування виправлень
"""
import pytest
import httpx

BASE_AUTH = "http://localhost:8001"
BASE_PRODUCT = "http://localhost:8002"
BASE_ORDER = "http://localhost:8003"


@pytest.mark.asyncio
async def test_fix1_login_with_post():
    """FIXED: Логін через POST з body"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_AUTH}/login",
            json={"email": "alice@example.com", "password": "alice123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert "userId" in data
        print("✅ FIX 1: Логін через POST працює")


@pytest.mark.asyncio
async def test_fix2_invalid_credentials_returns_401():
    """FIXED: Невалідні credentials повертають 401"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_AUTH}/login",
            json={"email": "wrong@example.com", "password": "wrong"}
        )

        assert response.status_code == 401
        print("✅ FIX 2: Невалідні credentials повертають 401")


@pytest.mark.asyncio
async def test_fix3_whoami_returns_401_without_token():
    """FIXED: Whoami без токена повертає 401"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_AUTH}/whoami")

        assert response.status_code == 401
        print("✅ FIX 3: Whoami без токена повертає 401")


@pytest.mark.asyncio
async def test_fix4_price_is_float():
    """FIXED: Price тепер float"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_PRODUCT}/products")

        data = response.json()
        products = data["items"]

        for product in products:
            assert isinstance(product["price"], (int, float))

        print("✅ FIX 4: Price тепер числовий тип")


@pytest.mark.asyncio
async def test_fix5_missing_product_returns_404():
    """FIXED: Неіснуючий товар повертає 404"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_PRODUCT}/products/9999")

        assert response.status_code == 404
        print("✅ FIX 5: Неіснуючий товар повертає 404")


@pytest.mark.asyncio
async def test_fix6_unauthorized_order_rejected():
    """FIXED: Замовлення без токена відхиляється"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_ORDER}/orders",
            json={"productId": 100, "qty": 1}
        )

        assert response.status_code == 401
        print("✅ FIX 6: Замовлення без токена відхиляється")


@pytest.mark.asyncio
async def test_fix7_nonexistent_product_order_rejected():
    """FIXED: Замовлення неіснуючого товару відхиляється"""
    async with httpx.AsyncClient() as client:
        # Спочатку логін
        login_response = await client.post(
            f"{BASE_AUTH}/login",
            json={"email": "alice@example.com", "password": "alice123"}
        )
        token = login_response.json()["accessToken"]

        # Спроба замовити неіснуючий товар
        response = await client.post(
            f"{BASE_ORDER}/orders",
            json={"productId": 9999, "qty": 1},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        print("✅ FIX 7: Замовлення неіснуючого товару відхиляється")


@pytest.mark.asyncio
async def test_fix8_insufficient_stock_rejected():
    """FIXED: Замовлення при недостатніх запасах відхиляється"""
    async with httpx.AsyncClient() as client:
        # Логін
        login_response = await client.post(
            f"{BASE_AUTH}/login",
            json={"email": "alice@example.com", "password": "alice123"}
        )
        token = login_response.json()["accessToken"]

        # Товар 101 має inStock: 0
        # Спроба замовити 5 штук
        response = await client.post(
            f"{BASE_ORDER}/orders",
            json={"productId": 101, "qty": 5},
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Insufficient stock" in data["detail"]
        print("✅ FIX 8: Замовлення при недостатніх запасах відхиляється")


@pytest.mark.asyncio
async def test_successful_order_creation():
    """Перевірка успішного створення замовлення"""
    async with httpx.AsyncClient() as client:
        # Логін
        login_response = await client.post(
            f"{BASE_AUTH}/login",
            json={"email": "alice@example.com", "password": "alice123"}
        )
        token = login_response.json()["accessToken"]

        # Створення валідного замовлення
        response = await client.post(
            f"{BASE_ORDER}/orders",
            json={"productId": 100, "qty": 2},  # Keyboard, є 5 на складі
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == 100
        assert data["quantity"] == 2
        assert data["status"] == "created"
        print("✅ Успішне створення замовлення працює")
