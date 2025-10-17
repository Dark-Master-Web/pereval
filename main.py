from fastapi import FastAPI, HTTPException, Query, Depends, status
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from enum import Enum
import database
from auth import auth_handler, get_current_moderator
from datetime import datetime
import base64
import os

app = FastAPI(
    title="Mountain Pass API",
    description="API для управления данными о горных перевалах с системой модерации",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Инициализируем менеджер БД
db = database.DatabaseManager()


# --- Модели запросов/ответов ---
class PerevalStatus(str, Enum):
    NEW = "new"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Coord(BaseModel):
    latitude: float
    longitude: float
    height: int

    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

    @validator('height')
    def validate_height(cls, v):
        if v < 0 or v > 10000:
            raise ValueError('Height must be between 0 and 10000 meters')
        return v


class Level(BaseModel):
    winter: Optional[str] = ""
    summer: Optional[str] = ""
    autumn: Optional[str] = ""
    spring: Optional[str] = ""

    @validator('*')
    def validate_level(cls, v):
        if v and v not in ['', '1A', '1B', '2A', '2B', '3A', '3B']:
            raise ValueError('Invalid difficulty level')
        return v


class User(BaseModel):
    email: EmailStr
    phone: str
    fam: str
    name: str
    otc: Optional[str] = ""

    @validator('phone')
    def validate_phone(cls, v):
        if not v.strip():
            raise ValueError('Phone number is required')
        return v

    @validator('fam', 'name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name fields are required')
        return v


class ImageBase64(BaseModel):
    data: str  # base64 encoded image
    title: str


class PerevalRequest(BaseModel):
    beauty_title: str
    title: str
    other_titles: Optional[str] = ""
    connect: Optional[str] = ""
    user: User
    coords: Coord
    level: Level
    images: List[ImageBase64] = []

    @validator('beauty_title', 'title')
    def validate_required_fields(cls, v):
        if not v.strip():
            raise ValueError('This field is required')
        return v


class PerevalResponse(BaseModel):
    id: int
    beauty_title: str
    title: str
    other_titles: Optional[str]
    connect: Optional[str]
    status: str
    add_time: datetime
    user: Dict[str, Any]
    coords: Dict[str, Any]
    level: Dict[str, Any]
    images: List[Dict[str, Any]]


class StatusUpdate(BaseModel):
    status: PerevalStatus
    reject_reason: Optional[str] = None


class ModeratorLogin(BaseModel):
    email: str
    password: str


class ModeratorCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
    version: str


# --- Эндпоинты аутентификации ---
@app.post("/auth/register", response_model=Dict[str, Any])
async def register_moderator(moderator: ModeratorCreate):
    """Регистрация нового модератора."""
    # Проверяем, не существует ли уже модератор с таким email
    existing_moderator = db.get_moderator_by_email(moderator.email)
    if existing_moderator:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Moderator with this email already exists"
        )

    password_hash = auth_handler.get_password_hash(moderator.password)
    success = db.create_moderator(moderator.username, moderator.email, password_hash)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create moderator"
        )

    return {"message": "Moderator successfully registered"}


@app.post("/auth/login", response_model=TokenResponse)
async def login_moderator(login_data: ModeratorLogin):
    """Аутентификация модератора."""
    moderator = db.get_moderator_by_email(login_data.email)

    if not moderator or not auth_handler.verify_password(login_data.password, moderator["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = auth_handler.create_access_token(
        data={"sub": moderator["email"], "moderator_id": moderator["id"]}
    )

    return {"access_token": access_token, "token_type": "bearer"}


# --- Защищенные эндпоинты (модерация) ---
@app.get("/moderation/perevals", response_model=Dict[str, Any])
async def get_perevals_for_moderation(
        status: Optional[PerevalStatus] = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        current_user: dict = Depends(get_current_moderator)
):
    """Получение списка перевалов для модерации."""
    result = db.get_perevals_paginated(
        status=status.value if status else None,
        skip=skip,
        limit=limit
    )
    return result


@app.patch("/moderation/pereval/{pereval_id}/status")
async def update_pereval_status_moderation(
        pereval_id: int,
        status_update: StatusUpdate,
        current_user: dict = Depends(get_current_moderator)
):
    """Обновление статуса перевала (только для модераторов)."""
    success = db.update_pereval_status(
        pereval_id=pereval_id,
        status=status_update.status.value,
        moderator_id=current_user.get("moderator_id"),
        reject_reason=status_update.reject_reason
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pereval not found or update error"
        )

    return {
        "status": 200,
        "message": f"Pereval status updated to '{status_update.status.value}'",
        "id": pereval_id
    }


@app.get("/moderation/pereval/{pereval_id}/history")
async def get_pereval_status_history(
        pereval_id: int,
        current_user: dict = Depends(get_current_moderator)
):
    """Получение истории изменений статуса перевала."""
    history = db.get_status_history(pereval_id)
    return {"history": history}


# --- Публичные эндпоинты ---
@app.post("/submitData", response_model=Dict[str, Any])
async def submit_data(pereval: PerevalRequest):
    """Основной метод для добавления данных о перевале."""
    try:
        print("📥 Получен запрос на добавление перевала...")

        # 1. Добавляем пользователя
        user_id = db.add_user(
            email=pereval.user.email,
            phone=pereval.user.phone,
            fam=pereval.user.fam,
            name=pereval.user.name,
            otc=pereval.user.otc
        )

        # 2. Добавляем координаты
        coord_id = db.add_coords(
            latitude=pereval.coords.latitude,
            longitude=pereval.coords.longitude,
            height=pereval.coords.height
        )

        # 3. Добавляем перевал
        pereval_id = db.add_pereval(
            beauty_title=pereval.beauty_title,
            title=pereval.title,
            other_titles=pereval.other_titles,
            connect=pereval.connect,
            user_id=user_id,
            coord_id=coord_id
        )

        # 4. Добавляем уровни сложности
        db.add_levels(
            pereval_id=pereval_id,
            winter=pereval.level.winter,
            summer=pereval.level.summer,
            autumn=pereval.level.autumn,
            spring=pereval.level.spring
        )

        # 5. Добавляем изображения (base64)
        image_ids = []
        for image in pereval.images:
            try:
                image_id = db.add_image_base64(image.data, image.title)
                db.link_image_to_pereval(pereval_id, image_id)
                image_ids.append(image_id)
            except Exception as e:
                print(f"⚠️ Ошибка при добавлении изображения: {e}")
                # Продолжаем обработку даже если с изображением ошибка

        return {
            "status": 200,
            "message": "Data submitted successfully",
            "id": pereval_id,
            "images_added": len(image_ids)
        }

    except Exception as e:
        print(f"❌ Ошибка при обработке запроса: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@app.get("/pereval/{pereval_id}", response_model=PerevalResponse)
async def get_pereval(pereval_id: int):
    """Получение информации о перевале по ID."""
    pereval_data = db.get_pereval_by_id(pereval_id)

    if not pereval_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pereval not found"
        )

    # Форматируем ответ
    response = {
        "id": pereval_data["id"],
        "beauty_title": pereval_data["beauty_title"],
        "title": pereval_data["title"],
        "other_titles": pereval_data["other_titles"],
        "connect": pereval_data["connect"],
        "status": pereval_data["status"],
        "add_time": pereval_data["add_time"],
        "user": {
            "email": pereval_data["email"],
            "phone": pereval_data["phone"],
            "fam": pereval_data["fam"],
            "name": pereval_data["name"],
            "otc": pereval_data["otc"]
        },
        "coords": {
            "latitude": float(pereval_data["latitude"]),
            "longitude": float(pereval_data["longitude"]),
            "height": pereval_data["height"]
        },
        "level": {
            "winter": pereval_data["winter"],
            "summer": pereval_data["summer"],
            "autumn": pereval_data["autumn"],
            "spring": pereval_data["spring"]
        },
        "images": pereval_data.get("images", [])
    }

    return response


@app.get("/user/{user_email}/perevals", response_model=List[Dict[str, Any]])
async def get_user_perevals(user_email: str):
    """Получение всех перевалов, добавленных пользователем."""
    perevals = db.get_perevals_by_user(user_email)
    return perevals


@app.get("/", response_model=Dict[str, Any])
async def root():
    return {
        "message": "Mountain Pass API v2.0",
        "version": "2.0.0",
        "documentation": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья API и подключения к БД"""
    try:
        with db.conn.cursor() as cur:
            cur.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now(),
            "version": "2.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now(),
            "version": "2.0.0"
        }


# Обработчики ошибок
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)