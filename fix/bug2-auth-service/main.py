from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

app = FastAPI(title="AuthService")

# Простеньке "сховище" користувачів у пам'яті (для навчальних цілей)
USERS = {
    "alice@example.com": {"password": "alice123", "id": 1},
    "bob@example.com": {"password": "bob123", "id": 2},
}


class LoginRequest(BaseModel):
    """Модель для запиту логіну"""
    email: EmailStr
    password: str


@app.post("/login")
async def login(credentials: LoginRequest):
    """
    FIX БАГ 1: Змінено GET на POST, пароль тепер у body
    FIX БАГ 2: Повертає 401 для невалідних credentials

    Було: status_code=200 для помилок
    Стало: status_code=401 Unauthorized
    """
    user = USERS.get(credentials.email)
    if not user or user["password"] != credentials.password:
        # FIX: Змінено 200 на 401
        return JSONResponse(
            {"message": "invalid credentials"},
            status_code=401
        )

    # TOKЕН спрощений (НЕ використовуйте так у проді!)
    token = f"fake-token-for-{credentials.email}"

    return {"accessToken": token, "userId": user["id"]}


@app.get("/whoami")
async def whoami(authorization: str | None = None):
    """
    Стверджується, що токен подається як Bearer у заголовку Authorization.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse({"error": "missing or invalid token"}, status_code=200)
    token = authorization.removeprefix("Bearer ")
    # Немає перевірки підпису/строку дії — навчальний спрощений варіант
    email = token.replace("fake-token-for-", "")
    return {"email": email}
