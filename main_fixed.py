from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from datetime import datetime
import json

app = FastAPI(
    title="Mountain Pass API",
    description="API для управления данными о горных перевалах",
    version="2.0.0"
)

# Временное хранилище в памяти для тестирования
temp_storage = {
    "perevals": {},
    "users": {},
    "next_id": 1
}


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
    data: str
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


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class StatusUpdate(BaseModel):
    status: str
    change_reason: Optional[str] = ""


# Эндпоинты аутентификации (упрощенные)
@app.post("/auth/register", response_model=Dict[str, Any])
async def register_moderator(user_data: UserRegister):
    """Упрощенная регистрация модератора"""
    return {
        "status": "success",
        "message": "Модератор зарегистрирован (демо)",
        "moderator_id": 1
    }


@app.post("/auth/login", response_model=Token)
async def login_moderator(user_data: UserLogin):
    """Упрощенная аутентификация"""
    return {
        "access_token": "demo-token-12345",
        "token_type": "bearer"
    }


# Публичные эндпоинты API
@app.post("/submitData")
async def submit_data(pereval_data: PerevalCreate):
    """Добавление нового перевала"""
    pereval_id = temp_storage["next_id"]

    # Сохраняем пользователя если его нет
    user_email = pereval_data.user.email
    if user_email not in temp_storage["users"]:
        temp_storage["users"][user_email] = pereval_data.user.dict()

    # Сохраняем перевал
    temp_storage["perevals"][pereval_id] = {
        **pereval_data.dict(),
        "id": pereval_id,
        "status": "new",
        "add_time": datetime.now().isoformat()
    }

    temp_storage["next_id"] += 1

    return {"status": 200, "message": "Отправлено успешно", "id": pereval_id}


@app.get("/submitData/{pereval_id}", response_model=Dict[str, Any])
async def get_pereval(pereval_id: int):
    """Получить информацию о перевале по ID"""
    pereval = temp_storage["perevals"].get(pereval_id)
    if not pereval:
        raise HTTPException(status_code=404, detail="Перевал не найден")
    return pereval


@app.patch("/submitData/{pereval_id}")
async def update_pereval(pereval_id: int, pereval_data: PerevalUpdate):
    """Обновить существующий перевал"""
    pereval = temp_storage["perevals"].get(pereval_id)
    if not pereval:
        return {"state": 0, "message": "Перевал не найден"}

    if pereval["status"] != "new":
        return {"state": 0, "message": "Можно редактировать только записи со статусом 'new'"}

    # Обновляем только предоставленные поля
    update_data = pereval_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            if key == 'coords' and isinstance(value, dict):
                pereval['coords'].update(value)
            elif key == 'level' and isinstance(value, dict):
                pereval['level'].update(value)
            elif key == 'images' and isinstance(value, list):
                pereval['images'] = value
            else:
                pereval[key] = value

    return {"state": 1, "message": "Запись успешно обновлена"}


@app.get("/submitData/", response_model=List[Dict[str, Any]])
async def get_user_perevals(user__email: str = Query(..., alias="user__email")):
    """Получить все перевалы пользователя по email"""
    user_perevals = []
    for pereval in temp_storage["perevals"].values():
        if pereval["user"]["email"] == user__email:
            user_perevals.append(pereval)
    return user_perevals


@app.get("/pereval/{pereval_id}")
async def get_pereval_legacy(pereval_id: int):
    """Легаси эндпоинт для получения перевала по ID"""
    return await get_pereval(pereval_id)


@app.get("/user/{email}/perevals")
async def get_user_perevals_legacy(email: str):
    """Легаси эндпоинт для получения перевалов пользователя"""
    return await get_user_perevals(email)


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# Эндпоинты модерации (демо версия)
@app.get("/moderation/perevals")
async def get_pending_perevals():
    """Получить список перевалов для модерации"""
    pending_perevals = []
    for pereval in temp_storage["perevals"].values():
        if pereval["status"] == "new":
            pending_perevals.append({
                "id": pereval["id"],
                "beauty_title": pereval["beauty_title"],
                "title": pereval["title"],
                "add_time": pereval["add_time"],
                "user_name": f"{pereval['user']['fam']} {pereval['user']['name']} {pereval['user']['otc']}",
                "user_email": pereval["user"]["email"]
            })
    return pending_perevals


@app.patch("/moderation/pereval/{pereval_id}/status")
async def update_pereval_status(pereval_id: int, status_update: StatusUpdate):
    """Обновить статус перевала"""
    pereval = temp_storage["perevals"].get(pereval_id)
    if not pereval:
        raise HTTPException(status_code=404, detail="Перевал не найден")

    new_status = status_update.status
    if new_status not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Статус должен быть 'accepted' или 'rejected'")

    pereval["status"] = new_status
    return {"status": "success", "message": f"Статус обновлен на {new_status}"}


@app.get("/auth/me")
async def get_current_user_info():
    """Получить информацию о текущем модераторе (демо)"""
    return {"moderator_id": 1, "username": "demo_moderator"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")