from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

app = FastAPI(title="AuthService")

# Простеньке "сховище" користувачів у пам'яті (для навчальних цілей)
USERS = {
    "alice@example.com": {"password": "alice123", "id": 1},
    "bob@example.com": {"password": "bob123", "id": 2},
}


@app.get("/login")
async def login(email: str, password: str, response: Response):
    user = USERS.get(email)
    if not user or user["password"] != password:
        return JSONResponse({"message": "invalid credentials"}, status_code=200)

    # TOKЕН спрощений (НЕ використовуйте так у проді!)
    token = f"fake-token-for-{email}"

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
