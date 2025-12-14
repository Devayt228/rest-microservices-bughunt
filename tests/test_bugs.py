"""
Тести для виявлення помилок у мікросервісній системі
Кожен тест перевіряє одну конкретну помилку
"""
import pytest
import httpx

# Базові URL сервісів
BASE_AUTH = "http://localhost:8001"
BASE_PRODUCT = "http://localhost:8002"
BASE_ORDER = "http://localhost:8003"


# ============================================
# AUTH SERVICE BUGS
# ============================================

@pytest.mark.asyncio
async def test_bug1_password_in_url_get_request():
    """
    БАГ 1 (КРИТИЧНИЙ): Пароль передається через URL у GET запиті

    Проблема: GET /login з паролем у query параметрах
    Ризик: Паролі потрапляють у логи, історію браузера, proxy логи
    Очікування: Має бути POST запит з body
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_AUTH}/login",
            params={"email": "alice@example.com", "password": "alice123"}
        )

        # Перевірка 1: Пароль у URL (це погано!)
        request_url = str(response.request.url)
        assert "password=alice123" in request_url, "Пароль має бути в URL (це баг!)"

        # Перевірка 2: Використовується GET (має бути POST)
        assert response.request.method == "GET", "Використовується GET (має бути POST)"

        print(f"❌ БАГ 1: Пароль у URL: {request_url}")


@pytest.mark.asyncio
async def test_bug2_wrong_status_code_for_invalid_credentials():
    """
    БАГ 2 (ВИСОКИЙ): Повертає 200 для невалідних credentials

    Проблема: Повертає 200 OK замість 401 Unauthorized
    Ризик: Клієнт не може відрізнити успіх від помилки
    Очікування: 401 Unauthorized
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_AUTH}/login",
            params={"email": "wrong@example.com", "password": "wrongpass"}
        )

        # Має бути 401, але повертає 200
        assert response.status_code == 200, f"Повертає 200 замість 401"

        data = response.json()
        assert data.get("message") == "invalid credentials"

        print(
            f"❌ БАГ 2: Невалідні credentials повертають {response.status_code} (має бути 401)")


@pytest.mark.asyncio
async def test_bug3_whoami_returns_200_without_token():
    """
    БАГ 3 (ВИСОКИЙ): /whoami повертає 200 без токена

    Проблема: Повертає 200 OK замість 401 Unauthorized при відсутності токена
    Ризик: Порушення REST контракту, неправильна обробка помилок
    Очікування: 401 Unauthorized
    """
    async with httpx.AsyncClient() as client:
        # Запит без Authorization header
        response = await client.get(f"{BASE_AUTH}/whoami")

        # Має бути 401, але повертає 200
        assert response.status_code == 200, f"Повертає 200 замість 401"

        data = response.json()
        assert "error" in data

        print(
            f"❌ БАГ 3: Відсутній токен повертає {response.status_code} (має бути 401)")


# ============================================
# PRODUCT SERVICE BUGS
# ============================================

@pytest.mark.asyncio
async def test_bug4_price_is_string_not_number():
    """
    БАГ 4 (СЕРЕДНІЙ): Ціна зберігається як string замість числа

    Проблема: price має тип str замість float
    Ризик: Проблеми з математичними операціями, несумісність типів
    Очікування: price має бути float
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_PRODUCT}/products")

        assert response.status_code == 200
        data = response.json()
        products = data.get("items", [])

        assert len(products) > 0, "Має бути хоча б один товар"

        # Перевіряємо тип price
        first_product = products[0]
        price = first_product.get("price")

        assert isinstance(
            price, str), f"Price має тип {type(price).__name__} (це баг!)"

        print(f"❌ БАГ 4: Price має тип 'str': {price} (має бути float)")


@pytest.mark.asyncio
async def test_bug5_wrong_status_code_for_missing_product():
    """
    БАГ 5 (ВИСОКИЙ): Повертає 200 для неіснуючого товару

    Проблема: Повертає 200 OK замість 404 Not Found
    Ризик: Порушення REST контракту, клієнт не може відрізнити помилку
    Очікування: 404 Not Found
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_PRODUCT}/products/9999")

        # Має бути 404, але повертає 200
        assert response.status_code == 200, f"Повертає 200 замість 404"

        data = response.json()
        assert data.get("message") == "not found"

        print(
            f"❌ БАГ 5: Неіснуючий товар повертає {response.status_code} (має бути 404)")


# ============================================
# ORDER SERVICE BUGS
# ============================================

@pytest.mark.asyncio
async def test_bug6_no_authentication_verification():
    """
    БАГ 6 (КРИТИЧНИЙ): Відсутня перевірка результату авторизації

    Проблема: order-service не перевіряє status_code від /whoami
    Ризик: Неавторизовані користувачі можуть створювати замовлення
    Очікування: Має відхилити запит з невалідним токеном
    """
    async with httpx.AsyncClient() as client:
        # Спроба створити замовлення з НЕВАЛІДНИМ токеном
        response = await client.post(
            f"{BASE_ORDER}/orders",
            json={"productId": 100, "qty": 1},
            headers={"Authorization": "Bearer totally-invalid-token-12345"}
        )

        # Замовлення створюється навіть з невалідним токеном!
        assert response.status_code == 201, "Замовлення створено з невалідним токеном (це баг!)"

        print(
            f"❌ БАГ 6: Замовлення створено з невалідним токеном (статус {response.status_code})")


@pytest.mark.asyncio
async def test_bug7_no_product_existence_check():
    """
    БАГ 7 (ВИСОКИЙ): Можна створити замовлення на неіснуючий товар

    Проблема: order-service не перевіряє існування товару
    Ризик: Замовлення на неіснуючі товари, проблеми з виконанням
    Очікування: Має відхилити замовлення неіснуючого товару
    """
    async with httpx.AsyncClient() as client:
        token = "Bearer fake-token-for-alice@example.com"

        # Спроба замовити неіснуючий товар (ID 9999)
        response = await client.post(
            f"{BASE_ORDER}/orders",
            json={"productId": 9999, "qty": 1},
            headers={"Authorization": token}
        )

        # Замовлення створюється для неіснуючого товару!
        assert response.status_code == 201, "Замовлення створено для неіснуючого товару (це баг!)"

        data = response.json()
        assert data.get("product_id") == 9999

        print(f"❌ БАГ 7: Створено замовлення на неіснуючий товар ID=9999")


@pytest.mark.asyncio
async def test_bug8_no_stock_availability_check():
    """
    БАГ 8 (ВИСОКИЙ): Можна замовити більше, ніж є на складі

    Проблема: order-service не перевіряє inStock перед створенням
    Ризик: Замовлення товарів без запасів, неможливість виконання
    Очікування: Має відхилити замовлення при недостатніх запасах
    """
    async with httpx.AsyncClient() as client:
        token = "Bearer fake-token-for-alice@example.com"

        # Товар 101 (Mouse) має inStock: 0
        # Спроба замовити 5 штук
        response = await client.post(
            f"{BASE_ORDER}/orders",
            json={"productId": 101, "qty": 5},
            headers={"Authorization": token}
        )

        # Замовлення створюється навіть при відсутності товару!
        assert response.status_code == 201, "Замовлення створено при нульових запасах (це баг!)"

        data = response.json()
        assert data.get("product_id") == 101
        assert data.get("quantity") == 5

        print(f"❌ БАГ 8: Створено замовлення на 5 одиниць товару з inStock=0")


# ============================================
# ДОДАТКОВІ ТЕСТИ ДЛЯ ПЕРЕВІРКИ ПРАВИЛЬНОЇ РОБОТИ
# ============================================

@pytest.mark.asyncio
async def test_valid_login_should_work():
    """Перевірка, що валідний логін працює"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_AUTH}/login",
            params={"email": "alice@example.com", "password": "alice123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert data["userId"] == 1
        print("✅ Валідний логін працює")


@pytest.mark.asyncio
async def test_valid_whoami_should_work():
    """Перевірка, що whoami з валідним токеном працює"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_AUTH}/whoami",
            params={"authorization": "Bearer fake-token-for-alice@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"] == "alice@example.com"
        print("✅ Whoami з валідним токеном працює")


@pytest.mark.asyncio
async def test_get_existing_product_should_work():
    """Перевірка, що отримання існуючого товару працює"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_PRODUCT}/products/100")

        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == 100
        assert data["name"] == "Keyboard"
        print("✅ Отримання існуючого товару працює")
