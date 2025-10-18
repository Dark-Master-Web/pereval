from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from datetime import datetime, timedelta
from database import DatabaseManager
from auth import get_current_user, get_current_moderator, setup_auth_handler, auth_handler, UserLogin, UserRegister, \
    Token

app = FastAPI(
    title="Mountain Pass API",
    description="API для управления данными о горных перевалах",
    version="2.0.0"
)

# Конфигурация базы данных из переменных окружения
db_config = {
    "host": os.getenv("FSTR_DB_HOST", "localhost"),
    "port": os.getenv("FSTR_DB_PORT", "5432"),
    "dbname": os.getenv("FSTR_DB_NAME", "mountain_pass"),
    "user": os.getenv("FSTR_DB_USER", "postgres"),
    "password": os.getenv("FSTR_DB_PASSWORD", "password")
}

db_manager = DatabaseManager(db_config)


@app.on_event("startup")
async def startup_event():
    """Подключение к базе данных при запуске приложения"""
    if not db_manager.connect():
        raise Exception("Failed to connect to database")

    # Инициализация системы аутентификации
    setup_auth_handler(db_manager)


# Модели Pydantic
class User(BaseModel):
    email: str
    phone: str
    fam: str
    name: str
    otc: str


class Coords(BaseModel):
    latitude: float
    longitude: float
    height: int


class Level(BaseModel):
    winter: Optional[str] = ""
    summer: Optional[str] = ""
    autumn: Optional[str] = ""
    spring: Optional[str] = ""


class Image(BaseModel):
    data: str  # URL или base64 encoded image
    title: str


class PerevalCreate(BaseModel):
    beauty_title: str
    title: str
    other_titles: str
    connect: str
    user: User
    coords: Coords
    level: Level
    images: List[Image]


class PerevalUpdate(BaseModel):
    beauty_title: Optional[str] = None
    title: Optional[str] = None
    other_titles: Optional[str] = None
    connect: Optional[str] = None
    coords: Optional[Coords] = None
    level: Optional[Level] = None
    images: Optional[List[Image]] = None


class StatusUpdate(BaseModel):
    status: str
    change_reason: Optional[str] = ""


# Эндпоинты аутентификации

@app.post("/auth/register", response_model=Dict[str, Any])
async def register_moderator(user_data: UserRegister):
    """
    Регистрация нового модератора
    """
    result = auth_handler.register_moderator(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )

    if result["success"]:
        return {"status": "success", "message": result["message"], "moderator_id": result["moderator_id"]}
    else:
        raise HTTPException(status_code=400, detail=result["message"])


@app.post("/auth/login", response_model=Token)
async def login_moderator(user_data: UserLogin):
    """
    Аутентификация модератора и получение JWT токена
    """
    moderator = auth_handler.authenticate_moderator(user_data.username, user_data.password)
    if not moderator:
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль"
        )

    access_token = auth_handler.create_access_token(
        data={"moderator_id": moderator["moderator_id"], "username": moderator["username"]}
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Публичные эндпоинты API

@app.post("/submitData")
async def submit_data(pereval_data: PerevalCreate):
    """
    Добавление нового перевала в базу данных
    """
    try:
        result = db_manager.add_pereval(pereval_data.dict())
        if result["status"] == 200:
            return {"status": 200, "message": "Отправлено успешно", "id": result["id"]}
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении данных: {str(e)}")


@app.get("/submitData/{pereval_id}", response_model=Dict[str, Any])
async def get_pereval(pereval_id: int):
    """
    Получить информацию о перевале по ID
    """
    pereval_data = db_manager.get_pereval_by_id(pereval_id)
    if not pereval_data:
        raise HTTPException(status_code=404, detail="Перевал не найден")
    return pereval_data


@app.patch("/submitData/{pereval_id}")
async def update_pereval(pereval_id: int, pereval_data: PerevalUpdate):
    """
    Обновить существующий перевал
    Можно редактировать только записи со статусом 'new'
    Нельзя изменять ФИО, email и телефон пользователя
    """
    result = db_manager.update_pereval(pereval_id, pereval_data.dict(exclude_unset=True))
    if result["state"] == 0:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.get("/submitData/", response_model=List[Dict[str, Any]])
async def get_user_perevals(user__email: str = Query(..., alias="user__email")):
    """
    Получить все перевалы, отправленные пользователем с указанным email
    """
    perevals = db_manager.get_perevals_by_user_email(user__email)
    return perevals


@app.get("/pereval/{pereval_id}")
async def get_pereval_legacy(pereval_id: int):
    """
    Легаси эндпоинт для получения перевала по ID
    """
    return await get_pereval(pereval_id)


@app.get("/user/{email}/perevals")
async def get_user_perevals_legacy(email: str):
    """
    Легаси эндпоинт для получения перевалов пользователя
    """
    perevals = db_manager.get_perevals_by_user_email(email)
    return perevals


@app.get("/health")
async def health_check():
    """
    Проверка здоровья приложения
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# Эндпоинты модерации (требуют аутентификации)

@app.get("/moderation/perevals")
async def get_pending_perevals(current_moderator: dict = Depends(get_current_moderator)):
    """
    Получить список перевалов для модерации
    Требует аутентификации модератора
    """
    perevals = db_manager.get_pending_perevals()
    return perevals


@app.patch("/moderation/pereval/{pereval_id}/status")
async def update_pereval_status(
        pereval_id: int,
        status_update: StatusUpdate,
        current_moderator: dict = Depends(get_current_moderator)
):
    """
    Обновить статус перевала (accepted/rejected)
    Требует аутентификации модератора
    """
    new_status = status_update.status
    change_reason = status_update.change_reason

    if new_status not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Статус должен быть 'accepted' или 'rejected'")

    result = db_manager.update_pereval_status(
        pereval_id,
        new_status,
        current_moderator["moderator_id"],
        change_reason
    )

    if result["success"]:
        return {"status": "success", "message": f"Статус обновлен на {new_status}"}
    else:
        raise HTTPException(status_code=400, detail=result["message"])


# Эндпоинт для проверки аутентификации
@app.get("/auth/me")
async def get_current_user_info(current_moderator: dict = Depends(get_current_moderator)):
    """
    Получить информацию о текущем аутентифицированном модераторе
    """
    return current_moderator


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)