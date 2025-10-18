import pytest
import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_get_pereval_by_id():
    """Тест получения перевала по ID"""
    print("Testing GET /submitData/{id}...")

    # Сначала создаем тестовый перевал
    test_data = {
        "beauty_title": "Test Pass",
        "title": "Test Mountain Pass",
        "other_titles": "Test",
        "connect": "",
        "user": {
            "email": "test_get@example.com",
            "phone": "+79998887766",
            "fam": "Иванов",
            "name": "Иван",
            "otc": "Иванович"
        },
        "coords": {
            "latitude": 45.1234,
            "longitude": 46.5678,
            "height": 3000
        },
        "level": {
            "winter": "1A",
            "summer": "",
            "autumn": "",
            "spring": ""
        },
        "images": [
            {
                "data": "https://example.com/test.jpg",
                "title": "Test Image"
            }
        ]
    }

    # Создаем перевал
    response = requests.post(f"{BASE_URL}/submitData", json=test_data)
    assert response.status_code == 200, f"Failed to create pereval: {response.text}"
    pereval_id = response.json().get("id")
    assert pereval_id is not None, "No ID returned from creation"

    # Получаем его по ID
    response = requests.get(f"{BASE_URL}/submitData/{pereval_id}")
    assert response.status_code == 200, f"Failed to get pereval: {response.text}"
    data = response.json()

    assert data["id"] == pereval_id
    assert data["title"] == "Test Mountain Pass"
    assert data["status"] == "new"
    assert data["user"]["email"] == "test_get@example.com"
    assert len(data["images"]) == 1

    print("✅ GET /submitData/{id} test passed!")


def test_update_pereval():
    """Тест обновления перевала"""
    print("Testing PATCH /submitData/{id}...")

    # Создаем тестовый перевал
    test_data = {
        "beauty_title": "Original Pass",
        "title": "Original Title",
        "other_titles": "Original",
        "connect": "",
        "user": {
            "email": "test_update@example.com",
            "phone": "+79998887755",
            "fam": "Петров",
            "name": "Петр",
            "otc": "Петрович"
        },
        "coords": {
            "latitude": 45.0000,
            "longitude": 46.0000,
            "height": 2500
        },
        "level": {
            "winter": "",
            "summer": "1B",
            "autumn": "",
            "spring": ""
        },
        "images": []
    }

    response = requests.post(f"{BASE_URL}/submitData", json=test_data)
    assert response.status_code == 200, f"Failed to create pereval: {response.text}"
    pereval_id = response.json().get("id")
    assert pereval_id is not None, "No ID returned from creation"

    # Обновляем перевал
    update_data = {
        "beauty_title": "Updated Pass",
        "title": "Updated Title",
        "other_titles": "Updated",
        "connect": "Updated connection",
        "coords": {
            "latitude": 45.1111,
            "longitude": 46.1111,
            "height": 2600
        },
        "level": {
            "winter": "2A",
            "summer": "1B",
            "autumn": "1A",
            "spring": ""
        },
        "images": [
            {
                "data": "https://example.com/updated.jpg",
                "title": "Updated Image"
            }
        ]
    }

    response = requests.patch(f"{BASE_URL}/submitData/{pereval_id}", json=update_data)
    assert response.status_code == 200, f"Failed to update pereval: {response.text}"
    result = response.json()
    assert result["state"] == 1, f"Update failed: {result.get('message')}"

    # Проверяем, что данные обновились
    response = requests.get(f"{BASE_URL}/submitData/{pereval_id}")
    assert response.status_code == 200, f"Failed to get updated pereval: {response.text}"
    data = response.json()

    assert data["title"] == "Updated Title"
    assert data["beauty_title"] == "Updated Pass"
    assert data["coords"]["latitude"] == 45.1111
    assert data["level"]["winter"] == "2A"
    assert len(data["images"]) == 1
    assert data["images"][0]["title"] == "Updated Image"

    # Проверяем, что пользовательские данные не изменились
    assert data["user"]["email"] == "test_update@example.com"
    assert data["user"]["fam"] == "Петров"

    print("✅ PATCH /submitData/{id} test passed!")


def test_get_user_perevals():
    """Тест получения перевалов пользователя по email"""
    print("Testing GET /submitData/?user__email=...")

    test_email = "test_user_perevals@example.com"

    # Создаем несколько перевалов для одного пользователя
    for i in range(2):
        test_data = {
            "beauty_title": f"User Pass {i}",
            "title": f"User Mountain Pass {i}",
            "other_titles": f"User {i}",
            "connect": "",
            "user": {
                "email": test_email,
                "phone": "+79998886655",
                "fam": "Сидоров",
                "name": "Сидор",
                "otc": "Сидорович"
            },
            "coords": {
                "latitude": 45.0000 + i,
                "longitude": 46.0000 + i,
                "height": 2000 + i * 100
            },
            "level": {
                "winter": "",
                "summer": "1A",
                "autumn": "",
                "spring": ""
            },
            "images": []
        }

        response = requests.post(f"{BASE_URL}/submitData", json=test_data)
        assert response.status_code == 200, f"Failed to create pereval {i}: {response.text}"
        time.sleep(0.1)  # Небольшая задержка для разных временных меток

    # Получаем все перевалы пользователя
    response = requests.get(f"{BASE_URL}/submitData/", params={"user__email": test_email})
    assert response.status_code == 200, f"Failed to get user perevals: {response.text}"
    data = response.json()

    assert len(data) >= 2, f"Expected at least 2 perevals, got {len(data)}"

    for item in data:
        assert item["user"]["email"] == test_email
        assert "Сидоров" in item["user"]["fam"]

    print("✅ GET /submitData/?user__email= test passed!")


def test_update_non_new_pereval():
    """Тест попытки обновления перевала не в статусе 'new'"""
    print("Testing update of non-new pereval...")

    # Для этого теста нужно создать перевал и изменить его статус через модерацию
    # Пока просто проверяем, что API возвращает корректную ошибку для несуществующего ID
    response = requests.patch(f"{BASE_URL}/submitData/999999", json={"title": "Updated"})
    assert response.status_code == 400
    result = response.json()
    assert "detail" in result

    print("✅ Update non-new pereval test passed!")


if __name__ == "__main__":
    try:
        test_get_pereval_by_id()
        test_update_pereval()
        test_get_user_perevals()
        test_update_non_new_pereval()
        print("\n🎉 All new endpoint tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise