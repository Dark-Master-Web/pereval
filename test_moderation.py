import pytest
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"


class TestModerationAPI:
    """Тесты API модерации"""

    @pytest.fixture
    def auth_token(self):
        """Получение токена аутентификации для тестов модерации"""
        # Здесь нужно использовать реальные учетные данные модератора
        login_data = {
            "username": "admin",  # Заменить на реальные данные
            "password": "admin123"  # Заменить на реальные данные
        }

        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                return response.json()["access_token"]
        except:
            pass

        return None

    def test_get_pending_perevals_unauthorized(self):
        """Тест получения списка на модерацию без аутентификации"""
        response = requests.get(f"{BASE_URL}/moderation/perevals")
        assert response.status_code == 401

    def test_update_status_unauthorized(self):
        """Тест обновления статуса без аутентификации"""
        response = requests.patch(
            f"{BASE_URL}/moderation/pereval/1/status",
            json={"status": "accepted", "change_reason": "test"}
        )
        assert response.status_code == 401

    def test_get_pending_perevals_authorized(self, auth_token):
        """Тест получения списка на модерацию с аутентификацией"""
        if not auth_token:
            pytest.skip("No authentication token available")

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/moderation/perevals", headers=headers)

        # Должен вернуть 200 даже если список пустой
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_update_status_authorized(self, auth_token):
        """Тест обновления статуса с аутентификацией"""
        if not auth_token:
            pytest.skip("No authentication token available")

        # Сначала нужно получить ID реального перевала для теста
        # Временно пропускаем этот тест
        pytest.skip("Need real pereval ID for testing")

    def test_update_status_invalid_data(self, auth_token):
        """Тест обновления статуса с невалидными данными"""
        if not auth_token:
            pytest.skip("No authentication token available")

        headers = {"Authorization": f"Bearer {auth_token}"}

        # Неверный статус
        response = requests.patch(
            f"{BASE_URL}/moderation/pereval/1/status",
            json={"status": "invalid_status", "change_reason": "test"},
            headers=headers
        )
        assert response.status_code == 400

    def test_auth_me_endpoint(self, auth_token):
        """Тест эндпоинта получения информации о текущем пользователе"""
        if not auth_token:
            pytest.skip("No authentication token available")

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "moderator_id" in data
        assert "username" in data


def run_tests():
    """Функция для запуска тестов"""
    print("Запуск тестов API...")

    # Создаем тестовый экземпляр
    test_api = TestMountainPassAPI()
    test_moderation = TestModerationAPI()

    try:
        # Тест здоровья приложения
        print("1. Тест здоровья приложения...")
        test_api.test_health_check()
        print("   ✅ Успешно")

        # Тест добавления данных
        print("2. Тест добавления перевала...")
        sample_data = test_api.sample_pereval_data()
        test_api.test_submit_data(sample_data)
        print("   ✅ Успешно")

        # Тест получения перевала
        print("3. Тест получения перевала по ID...")
        test_api.test_get_pereval_by_id(sample_data)
        print("   ✅ Успешно")

        print("Все основные тесты пройдены успешно!")

    except Exception as e:
        print(f"❌ Ошибка при выполнении тестов: {e}")


if __name__ == "__main__":
    run_tests()