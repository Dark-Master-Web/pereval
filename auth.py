from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
from database import DatabaseManager

# Конфигурация из переменных окружения
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Инициализация
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# Модели для аутентификации
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


class AuthHandler:
    def __init__(self, db_manager: DatabaseManager):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.db_manager = db_manager

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    def register_moderator(self, username: str, email: str, password: str) -> dict:
        """Регистрация нового модератора"""
        try:
            # Проверяем, существует ли уже пользователь с таким username или email
            with self.db_manager.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM moderators WHERE username = %s OR email = %s",
                    (username, email)
                )
                existing_user = cursor.fetchone()

                if existing_user:
                    return {"success": False, "message": "Пользователь с таким именем или email уже существует"}

                # Хэшируем пароль и создаем пользователя
                hashed_password = self.get_password_hash(password)
                cursor.execute(
                    """INSERT INTO moderators (username, email, password_hash) 
                    VALUES (%s, %s, %s) RETURNING id""",
                    (username, email, hashed_password)
                )
                moderator_id = cursor.fetchone()[0]
                self.db_manager.connection.commit()

                return {
                    "success": True,
                    "message": "Модератор успешно зарегистрирован",
                    "moderator_id": moderator_id
                }

        except Exception as e:
            self.db_manager.connection.rollback()
            return {"success": False, "message": f"Ошибка при регистрации: {str(e)}"}

    def authenticate_moderator(self, username: str, password: str) -> Optional[dict]:
        """Аутентификация модератора"""
        try:
            with self.db_manager.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, password_hash FROM moderators WHERE username = %s",
                    (username,)
                )
                moderator = cursor.fetchone()

                if not moderator:
                    return None

                moderator_id, db_username, email, hashed_password = moderator

                # Проверяем пароль
                if not self.verify_password(password, hashed_password):
                    return None

                return {
                    "moderator_id": moderator_id,
                    "username": db_username,
                    "email": email
                }

        except Exception as e:
            print(f"Authentication error: {e}")
            return None


# Зависимость для проверки токена
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = auth_handler.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# Зависимость для проверки модератора
async def get_current_moderator(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = auth_handler.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем, что пользователь является модератором
    if "moderator_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    return payload


# Глобальный экземпляр auth_handler (будет инициализирован в main.py)
auth_handler = None


def setup_auth_handler(db_manager: DatabaseManager):
    """Инициализация auth_handler с db_manager"""
    global auth_handler
    auth_handler = AuthHandler(db_manager)