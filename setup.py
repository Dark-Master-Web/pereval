import subprocess
import sys


def install_requirements():
    """Установка зависимостей проекта"""
    print("Установка зависимостей...")

    # Базовые зависимости без жестких версий
    requirements = [
        "fastapi",
        "uvicorn[standard]",
        "psycopg",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-dotenv",
        "pytest",
        "requests",
        "pydantic"
    ]

    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Установлен: {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки {package}: {e}")
            # Попробуем установить без зависимостей
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--no-deps"])
                print(f"✅ Установлен (без зависимостей): {package}")
            except:
                print(f"❌ Критическая ошибка установки: {package}")

    print("\nЗависимости установлены!")


if __name__ == "__main__":
    install_requirements()