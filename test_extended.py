import requests
import json

BASE_URL = "http://localhost:8000"


def test_all_endpoints():
    """Тестирование всех новых эндпоинтов"""

    # 1. Сначала создаем перевал
    test_data = {
        "beauty_title": "Расширенный тест",
        "title": "Тест новых эндпоинтов",
        "other_titles": "Новая функциональность",
        "connect": "Тестовое соединение",
        "user": {
            "email": "extended_test@example.com",
            "phone": "+79995556677",
            "fam": "Расширенный",
            "name": "Тест",
            "otc": "Новый"
        },
        "coords": {
            "latitude": 45.6789,
            "longitude": 41.2345,
            "height": 3200
        },
        "level": {
            "winter": "2A",
            "summer": "1B",
            "autumn": "2B",
            "spring": "3A"
        },
        "images": []
    }

    print("1. 📝 Тестируем создание перевала...")
    response = requests.post(f"{BASE_URL}/submitData", json=test_data)
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Response: {result}")

    if response.status_code == 200:
        pereval_id = result["id"]
        user_email = test_data["user"]["email"]

        # 2. Получаем созданный перевал
        print(f"\n2. 🔍 Тестируем получение перевала ID {pereval_id}...")
        response = requests.get(f"{BASE_URL}/pereval/{pereval_id}")
        print(f"   Status: {response.status_code}")
        print(f"   Response keys: {list(response.json().keys())}")

        # 3. Получаем перевалы пользователя
        print(f"\n3. 👤 Тестируем получение перевалов пользователя {user_email}...")
        response = requests.get(f"{BASE_URL}/user/{user_email}/perevals")
        print(f"   Status: {response.status_code}")
        perevals = response.json()
        print(f"   Найдено перевалов: {len(perevals)}")

        # 4. Обновляем статус
        print(f"\n4. ⚡ Тестируем обновление статуса...")
        update_data = {"status": "accepted"}
        response = requests.patch(f"{BASE_URL}/pereval/{pereval_id}/status", json=update_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

    print(f"\n5. 🏥 Проверка здоровья...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")


if __name__ == "__main__":
    print("🚀 Запуск расширенных тестов API...\n")
    test_all_endpoints()
    print("\n✅ Все тесты завершены!")