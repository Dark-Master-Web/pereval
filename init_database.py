import psycopg
import os
from datetime import datetime


def init_database():
    """Инициализация базы данных через Python"""

    # Параметры подключения
    db_config = {
        "host": "localhost",
        "port": 5432,
        "dbname": "postgres",  # Подключаемся к базе по умолчанию
        "user": "postgres",
        "password": "your_password"  # Замените на ваш пароль
    }

    try:
        # Подключаемся к PostgreSQL
        conn = psycopg.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()

        # Создаем базу данных если не существует
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'mountain_pass'")
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("CREATE DATABASE mountain_pass")
            print("✅ Database 'mountain_pass' created")
        else:
            print("✅ Database 'mountain_pass' already exists")

        cursor.close()
        conn.close()

        # Теперь подключаемся к нашей базе данных
        db_config["dbname"] = "mountain_pass"
        conn = psycopg.connect(**db_config)
        cursor = conn.cursor()

        # Читаем и выполняем SQL из файла
        with open("init_database.sql", "r", encoding="utf-8") as f:
            sql_script = f.read()

        # Разделяем скрипт на отдельные команды
        commands = sql_script.split(';')

        for command in commands:
            command = command.strip()
            if command:
                cursor.execute(command)

        conn.commit()
        print("✅ Database tables created successfully!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    init_database()