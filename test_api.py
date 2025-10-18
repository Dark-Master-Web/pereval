import requests
import json
from datetime import datetime

# Конфигурация тестов
BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"test_user_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"


class TestMountainPassAPI:
    """Тесты для API горных перевалов"""

    def __init__(self):
        self.results = []
        self.pereval_id = None

    def sample_pereval_data(self):
        """Тестовые данные перевала"""
        return {
            "beauty_title": "Тестовый перевал",
            "title": "Горный тестовый маршрут",
            "other_titles": "Дополнительное тестовое название",
            "connect": "Тестовое соединение",
            "user": {
                "email": TEST_EMAIL,
                "phone": "+79990000000",
                "fam": "Тестовов",
                "name": "Тест",
                "otc": "Тестович"
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
                    "data": "https://example.com/test_image.jpg",
                    "title": "Тестовое изображение"
                }
            ]
        }

    def run_test(self, test_name, test_func):
        """Запуск отдельного теста"""
        try:
            result = test_func()
            self.results.append((test_name, "✅ УСПЕХ", ""))
            return result
        except Exception as e:
            self.results.append((test_name, "❌ ОШИБКА", str(e)))
            return None

    def test_health_check(self):
        """Тест проверки здоровья приложения"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        return True

    def test_submit_data(self):
        """Тест добавления нового перевала"""
        sample_data = self.sample_pereval_data()
        response = requests.post(
            f"{BASE_URL}/submitData",
            json=sample_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        assert data["message"] == "Отправлено успешно"
        assert "id" in data

        # Сохраняем ID для последующих тестов
        self.pereval_id = data["id"]
        return data["id"]

    def test_get_pereval_by_id(self):
        """Тест получения перевала по ID"""
        if not self.pereval_id:
            self.test_submit_data()

        response = requests.get(f"{BASE_URL}/submitData/{self.pereval_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self.pereval_id
        assert data["status"] == "new"
        return True

    def test_update_pereval(self):
        """Тест обновления перевала"""
        if not self.pereval_id:
            self.test_submit_data()

        update_data = {
            "title": "Обновленное название",
            "coords": {
                "latitude": 46.5678,
                "longitude": 91.1234,
                "height": 2600
            }
        }

        response = requests.patch(
            f"{BASE_URL}/submitData/{self.pereval_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == 1
        assert "успешно" in data["message"].lower()
        return True

    def test_get_user_perevals(self):
        """Тест получения перевалов пользователя по email"""
        response = requests.get(
            f"{BASE_URL}/submitData/",
            params={"user__email": TEST_EMAIL}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        return True

    def test_legacy_endpoints(self):
        """Тест легаси эндпоинтов"""
        if not self.pereval_id:
            self.test_submit_data()

        # Легаси эндпоинт получения перевала
        response = requests.get(f"{BASE_URL}/pereval/{self.pereval_id}")
        assert response.status_code == 200

        # Легаси эндпоинт получения перевалов пользователя
        response = requests.get(f"{BASE_URL}/user/{TEST_EMAIL}/perevals")
        assert response.status_code == 200
        return True

    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 ЗАПУСК ТЕСТОВ MOUNTAIN PASS API")
        print("=" * 50)

        tests = [
            ("Проверка здоровья приложения", self.test_health_check),
            ("Добавление нового перевала", self.test_submit_data),
            ("Получение перевала по ID", self.test_get_pereval_by_id),
            ("Обновление перевала", self.test_update_pereval),
            ("Получение перевалов пользователя", self.test_get_user_perevals),
            ("Проверка легаси эндпоинтов", self.test_legacy_endpoints),
        ]

        for test_name, test_func in tests:
            print(f"Выполняется: {test_name}...")
            self.run_test(test_name, test_func)

        # Вывод результатов
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("=" * 50)

        for test_name, result, error in self.results:
            print(f"{test_name}: {result}")
            if error:
                print(f"   Ошибка: {error}")

        # Статистика
        success_count = sum(1 for _, result, _ in self.results if "✅" in result)
        total_count = len(self.results)

        print(f"\nИтого: {success_count}/{total_count} тестов пройдено успешно")

        if success_count == total_count:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print("⚠️  Некоторые тесты не пройдены")


def main():
    """Основная функция запуска тестов"""
    try:
        tester = TestMountainPassAPI()
        tester.run_all_tests()
    except requests.exceptions.ConnectionError:
        print("❌ ОШИБКА: Не удалось подключиться к серверу")
        print("Убедитесь, что сервер запущен на http://localhost:8000")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    main()