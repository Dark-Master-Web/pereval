import requests
import json

BASE_URL = "http://localhost:8000"


def test_moderation_flow():
    """Тестирование системы модерации"""

    print("🚀 Запуск тестов системы модерации...\n")

    # 1. Создаем тестовый перевал
    test_data = {
        "beauty_title": "Тест модерации",
        "title": "Перевал для проверки модерации",
        "other_titles": "Модерационный тест",
        "connect": "Тестовое соединение для модерации",
        "user": {
            "email": "moderation_test@example.com",
            "phone": "+79997776655",
            "fam": "Модерационный",
            "name": "Тест",
            "otc": "Системный"
        },
        "coords": {
            "latitude": 46.1234,
            "longitude": 42.5678,
            "height": 2800
        },
        "level": {
            "winter": "1A",
            "summer": "1B",
            "autumn": "2A",
            "spring": "1A"
        },
        "images": []
    }

    print("1. 📝 Создаем тестовый перевал...")
    try:
        response = requests.post(f"{BASE_URL}/submitData", json=test_data)
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Response: {result}")

        if response.status_code == 200:
            pereval_id = result["id"]
            print(f"   ✅ Перевал создан, ID: {pereval_id}")

            # 2. Пытаемся получить список для модерации без авторизации
            print("\n2. 🔒 Пытаемся получить список модерации без токена...")
            response = requests.get(f"{BASE_URL}/moderation/perevals")
            print(f"   Status (ожидается 401): {response.status_code}")

            # 3. Тестируем публичные эндпоинты
            print("\n3. 🌐 Тестируем публичные эндпоинты...")

            # Получаем информацию о перевале
            response = requests.get(f"{BASE_URL}/pereval/{pereval_id}")
            print(f"   GET /pereval/{pereval_id}: {response.status_code}")

            # Получаем перевалы пользователя
            response = requests.get(f"{BASE_URL}/user/moderation_test@example.com/perevals")
            print(f"   GET /user/.../perevals: {response.status_code}")

            # Проверяем здоровье API
            response = requests.get(f"{BASE_URL}/health")
            print(f"   GET /health: {response.status_code}")

        print(f"\n✅ Тесты публичных эндпоинтов завершены!")
        print("💡 Для тестирования модерации нужно сначала создать модератора через /auth/register")

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        print("💡 Убедитесь, что сервер запущен: uvicorn main:app --reload")


if __name__ == "__main__":
    test_moderation_flow()