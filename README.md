markdown
# Mountain Pass API

REST API для управления данными о горных перевалах. Проект предоставляет функциональность для добавления, получения и редактирования информации о перевалах, а также систему модерации.

## 📋 Оглавление

- [Функциональность](#функциональность)
- [Технологии](#технологии)
- [Установка и запуск](#установка-и-запуск)
- [Переменные окружения](#переменные-окружения)
- [API Endpoints](#api-endpoints)
- [Примеры использования](#примеры-использования)
- [Структура базы данных](#структура-базы-данных)
- [Разработка](#разработка)

## 🚀 Функциональность

### Основные возможности:
- ✅ Добавление новых перевалов
- ✅ Получение информации о перевалах по ID
- ✅ Редактирование перевалов (только со статусом "new")
- ✅ Получение всех перевалов пользователя по email
- ✅ Система модерации с JWT аутентификацией
- ✅ Проверка здоровья приложения

### Статусы перевалов:
- `new` - новая запись (можно редактировать)
- `pending` - на модерации
- `accepted` - принят
- `rejected` - отклонен

## 🛠 Технологии

- **Python 3.8+**
- **FastAPI** - современный веб-фреймворк
- **PostgreSQL** - реляционная база данных
- **Psycopg 3** - драйвер для PostgreSQL
- **JWT** - аутентификация
- **Pydantic** - валидация данных

## ⚙️ Установка и запуск

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd mountain-pass-api
2. Установка зависимостей
bash
pip install -r requirements.txt
3. Настройка базы данных
bash
# Создание базы данных и таблиц
psql -f init_database.sql
4. Настройка переменных окружения
Создайте файл .env в корневой директории:

env
FSTR_DB_HOST=localhost
FSTR_DB_PORT=5432
FSTR_DB_NAME=mountain_pass
FSTR_DB_USER=postgres
FSTR_DB_PASSWORD=password
JWT_SECRET_KEY=your-secret-key
5. Запуск приложения
bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
Приложение будет доступно по адресу: http://localhost:8000

🔧 Переменные окружения
Переменная	Описание	По умолчанию
FSTR_DB_HOST	Хост базы данных	localhost
FSTR_DB_PORT	Порт базы данных	5432
FSTR_DB_NAME	Имя базы данных	mountain_pass
FSTR_DB_USER	Пользователь БД	postgres
FSTR_DB_PASSWORD	Пароль БД	password
JWT_SECRET_KEY	Секретный ключ для JWT	-
📡 API Endpoints
Публичные endpoints (не требуют аутентификации)
🟢 POST /submitData
Добавление нового перевала.

Тело запроса:

json
{
  "beauty_title": "Перевал",
  "title": "Горный перевал",
  "other_titles": "Дополнительное название",
  "connect": "Соединение с другими перевалами",
  "user": {
    "email": "user@example.com",
    "phone": "+79991234567",
    "fam": "Иванов",
    "name": "Иван",
    "otc": "Петрович"
  },
  "coords": {
    "latitude": 45.1234,
    "longitude": 90.5678,
    "height": 2500
  },
  "level": {
    "winter": "1A",
    "summer": "1B",
    "autumn": "2A",
    "spring": "2B"
  },
  "images": [
    {
      "data": "https://example.com/image1.jpg",
      "title": "Вид на перевал"
    }
  ]
}
Ответ:

json
{
  "status": 200,
  "message": "Отправлено успешно",
  "id": 123
}
🔵 GET /submitData/{id}
Получение информации о перевале по ID.

Ответ:

json
{
  "id": 123,
  "beauty_title": "Перевал",
  "title": "Горный перевал",
  "other_titles": "Дополнительное название",
  "connect": "Соединение с другими перевалами",
  "add_time": "2024-01-15T10:30:00",
  "status": "new",
  "user": {
    "email": "user@example.com",
    "phone": "+79991234567",
    "fam": "Иванов",
    "name": "Иван",
    "otc": "Петрович"
  },
  "coords": {
    "latitude": 45.1234,
    "longitude": 90.5678,
    "height": 2500
  },
  "level": {
    "winter": "1A",
    "summer": "1B",
    "autumn": "2A",
    "spring": "2B"
  },
  "images": [
    {
      "data": "https://example.com/image1.jpg",
      "title": "Вид на перевал"
    }
  ]
}
🟡 PATCH /submitData/{id}
Редактирование существующего перевала (только со статусом "new").

Тело запроса (только изменяемые поля):

json
{
  "beauty_title": "Обновленное название",
  "coords": {
    "latitude": 45.5678,
    "longitude": 90.1234,
    "height": 2600
  },
  "level": {
    "winter": "2A"
  }
}
Ответ:

json
{
  "state": 1,
  "message": "Запись успешно обновлена"
}
Ошибка:

json
{
  "state": 0,
  "message": "Можно редактировать только записи со статусом 'new'"
}
🔵 GET /submitData/?user__email={email}
Получение всех перевалов пользователя по email.

Ответ:

json
[
  {
    "id": 123,
    "beauty_title": "Перевал",
    "title": "Горный перевал",
    "other_titles": "Дополнительное название",
    "connect": "Соединение с другими перевалами",
    "add_time": "2024-01-15T10:30:00",
    "status": "new",
    "user": {
      "email": "user@example.com",
      "phone": "+79991234567",
      "fam": "Иванов",
      "name": "Иван",
      "otc": "Петрович"
    },
    "coords": {
      "latitude": 45.1234,
      "longitude": 90.5678,
      "height": 2500
    }
  }
]
🟢 GET /health
Проверка здоровья приложения.

Ответ:

json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00.123456"
}
Эндпоинты модерации (требуют аутентификации)
🔐 POST /auth/register
Регистрация модератора.

🔐 POST /auth/login
Аутентификация модератора.

🔐 GET /moderation/perevals
Получение списка перевалов для модерации.

🔐 PATCH /moderation/pereval/{id}/status
Обновление статуса перевала.

📊 Примеры использования
Добавление нового перевала
bash
curl -X POST "http://localhost:8000/submitData" \
  -H "Content-Type: application/json" \
  -d '{
    "beauty_title": "Горный перевал",
    "title": "Высокогорный маршрут",
    "other_titles": "Альпийский перевал",
    "connect": "Соединяет две долины",
    "user": {
      "email": "alpinist@example.com",
      "phone": "+79991234567",
      "fam": "Петров",
      "name": "Алексей",
      "otc": "Сергеевич"
    },
    "coords": {
      "latitude": 43.1234,
      "longitude": 42.5678,
      "height": 3456
    },
    "level": {
      "winter": "2B",
      "summer": "1B",
      "autumn": "2A",
      "spring": "2B"
    },
    "images": [
      {
        "data": "https://example.com/photo1.jpg",
        "title": "Вид с севера"
      }
    ]
  }'
Получение перевала по ID
bash
curl -X GET "http://localhost:8000/submitData/123"
Редактирование перевала
bash
curl -X PATCH "http://localhost:8000/submitData/123" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Обновленное название перевала",
    "coords": {
      "latitude": 43.5678,
      "longitude": 42.1234,
      "height": 3500
    }
  }'
Получение перевалов пользователя
bash
curl -X GET "http://localhost:8000/submitData/?user__email=alpinist@example.com"
🗄️ Структура базы данных
Основные таблицы:
users - информация о пользователях

coords - географические координаты

pereval_added - основная информация о перевалах

pereval_levels - уровни сложности по сезонам

images - изображения перевалов

pereval_images - связь перевалов с изображениями

moderators - модераторы системы

status_logs - история изменения статусов

🔬 Документация API
После запуска приложения доступна интерактивная документация:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

🧪 Тестирование
Для запуска тестов выполните:

bash
python test_api.py
python test_moderation.py
📈 Разработка
Git workflow:
Создавайте feature-ветки для новой функциональности

Делайте частые коммиты с понятными сообщениями

После завершения feature сливайте ветку в master

Структура проекта:
text
mountain-pass-api/
├── main.py              # FastAPI приложение
├── database.py          # Менеджер базы данных
├── auth.py              # Аутентификация JWT
├── requirements.txt     # Зависимости проекта
├── .env                # Переменные окружения
├── init_database.sql   # SQL для инициализации БД
├── test_api.py         # Тесты API
├── test_moderation.py  # Тесты модерации
└── README.md           # Документация
🤝 Вклад в проект
Форкните репозиторий

Создайте feature-ветку (git checkout -b feature/amazing-feature)

Закоммитьте изменения (git commit -m 'Add amazing feature')

Запушьте ветку (git push origin feature/amazing-feature)

Откройте Pull Request

📄
Примечание: Для работы с эндпоинтами модерации требуется JWT аутентификация. Обратитесь к администратору для получения учетных данных модератора.
