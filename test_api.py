import requests
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Тест проверки здоровья API"""
    print("🧪 Тестируем /health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_submit_data():
    """Тест добавления перевала"""
    print("🧪 Тестируем /submitData...")

    test_data = {
        "beauty_title": "Автоматический тест",
        "title": "Тестовый перевал из скрипта",
        "other_titles": "Автотест долина",
        "connect": "Соединяет тестовые долины",
        "user": {
            "email": "autotest@example.com",
            "phone": "+79990001122",
            "fam": "Тестов",
            "name": "Автомат",
            "otc": "Скриптович"
        },
        "coords": {
            "latitude": 44.1234,
            "longitude": 41.5678,
            "height": 3000
        },
        "level": {
            "winter": "1A",
            "summer": "1B",
            "autumn": "2A",
            "spring": "2B"
        },
        "images": []
    }

    response = requests.post(
        f"{BASE_URL}/submitData",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_validation_errors():
    """Тест валидации ошибок"""
    print("🧪 Тестируем валидацию ошибок...")

    # Неполные данные (без обязательных полей)
    invalid_data = {
        "beauty_title": "Неполный перевал",
        "title": "Тест без пользователя",
        # Нет обязательных полей user, coords и т.д.
    }

    response = requests.post(
        f"{BASE_URL}/submitData",
        json=invalid_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status (ожидается ошибка): {response.status_code}")
    if response.status_code != 200:
        print("✅ Валидация работает - ошибка поймана")
    else:
        print("❌ Валидация не сработала")
    print()


if __name__ == "__main__":
    print("🚀 Запуск тестов API...\n")

    try:
        test_health()
        test_submit_data()
        test_validation_errors()
        print("✅ Все тесты завершены!")
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        print("Убедитесь, что сервер запущен: uvicorn main:app --reload")