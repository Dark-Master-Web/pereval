import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class SQLiteDatabaseManager:
    def __init__(self, db_path: str = "mountain_pass.db"):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Подключение к SQLite базе данных"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self._create_tables()
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False

    def _create_tables(self):
        """Создание таблиц в SQLite"""
        with self.connection:
            # Таблица пользователей
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT NOT NULL,
                    fam TEXT NOT NULL,
                    name TEXT NOT NULL,
                    otc TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица координат
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS coords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    height INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица перевалов
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS pereval_added (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    beauty_title TEXT,
                    title TEXT NOT NULL,
                    other_titles TEXT,
                    connect TEXT,
                    add_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER NOT NULL,
                    coord_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'pending', 'accepted', 'rejected')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (coord_id) REFERENCES coords (id)
                )
            """)

            # Таблица уровней сложности
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS pereval_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pereval_id INTEGER NOT NULL,
                    winter TEXT,
                    summer TEXT,
                    autumn TEXT,
                    spring TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pereval_id) REFERENCES pereval_added (id) ON DELETE CASCADE
                )
            """)

            # Таблица изображений
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,  # URL вместо BYTEA в SQLite
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Связующая таблица
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS pereval_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pereval_id INTEGER NOT NULL,
                    image_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pereval_id) REFERENCES pereval_added (id) ON DELETE CASCADE,
                    FOREIGN KEY (image_id) REFERENCES images (id) ON DELETE CASCADE
                )
            """)

            # Таблица модераторов
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS moderators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица логов статусов
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS status_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pereval_id INTEGER NOT NULL,
                    old_status TEXT,
                    new_status TEXT NOT NULL,
                    moderator_id INTEGER,
                    change_reason TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pereval_id) REFERENCES pereval_added (id) ON DELETE CASCADE
                )
            """)

    def add_pereval(self, data: Dict) -> Dict:
        """Добавление нового перевала в базу данных"""
        try:
            cursor = self.connection.cursor()

            # Проверяем существование пользователя
            user_data = data['user']
            cursor.execute("SELECT id FROM users WHERE email = ?", (user_data['email'],))
            user_result = cursor.fetchone()

            if user_result:
                user_id = user_result[0]
            else:
                # Создаем нового пользователя
                cursor.execute(
                    """INSERT INTO users (email, phone, fam, name, otc) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (user_data['email'], user_data['phone'], user_data['fam'],
                     user_data['name'], user_data['otc'])
                )
                user_id = cursor.lastrowid

            # Добавляем координаты
            coords = data['coords']
            cursor.execute(
                """INSERT INTO coords (latitude, longitude, height) 
                VALUES (?, ?, ?)""",
                (coords['latitude'], coords['longitude'], coords['height'])
            )
            coord_id = cursor.lastrowid

            # Добавляем основную информацию о перевале
            cursor.execute(
                """INSERT INTO pereval_added 
                (beauty_title, title, other_titles, connect, user_id, coord_id, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (data['beauty_title'], data['title'], data['other_titles'],
                 data['connect'], user_id, coord_id, 'new')
            )
            pereval_id = cursor.lastrowid

            # Добавляем уровни сложности
            level = data['level']
            cursor.execute(
                """INSERT INTO pereval_levels (pereval_id, winter, summer, autumn, spring) 
                VALUES (?, ?, ?, ?, ?)""",
                (pereval_id, level.get('winter', ''), level.get('summer', ''),
                 level.get('autumn', ''), level.get('spring', ''))
            )

            # Добавляем изображения
            for image in data['images']:
                cursor.execute(
                    "INSERT INTO images (data, title) VALUES (?, ?)",
                    (image['data'], image['title'])
                )
                image_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO pereval_images (pereval_id, image_id) VALUES (?, ?)",
                    (pereval_id, image_id)
                )

            self.connection.commit()
            return {"status": 200, "message": "Success", "id": pereval_id}

        except Exception as e:
            self.connection.rollback()
            return {"status": 500, "message": f"Ошибка при добавлении: {str(e)}"}

    def get_pereval_by_id(self, pereval_id: int) -> Optional[Dict]:
        """Получить перевал по ID"""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT 
                    pa.id, pa.beauty_title, pa.title, pa.other_titles, pa.connect, 
                    pa.add_time, pa.status,
                    u.email, u.phone, u.fam, u.name, u.otc,
                    c.latitude, c.longitude, c.height,
                    pl.winter, pl.summer, pl.autumn, pl.spring
                FROM pereval_added pa
                JOIN users u ON pa.user_id = u.id
                JOIN coords c ON pa.coord_id = c.id
                LEFT JOIN pereval_levels pl ON pa.id = pl.pereval_id
                WHERE pa.id = ?
            """, (pereval_id,))

            result = cursor.fetchone()
            if not result:
                return None

            # Изображения
            cursor.execute("""
                SELECT i.data, i.title 
                FROM images i
                JOIN pereval_images pi ON i.id = pi.image_id
                WHERE pi.pereval_id = ?
            """, (pereval_id,))

            images = [{"data": row[0], "title": row[1]} for row in cursor.fetchall()]

            pereval_data = {
                "id": result[0],
                "beauty_title": result[1],
                "title": result[2],
                "other_titles": result[3],
                "connect": result[4],
                "add_time": result[5],
                "status": result[6],
                "user": {
                    "email": result[7],
                    "phone": result[8],
                    "fam": result[9],
                    "name": result[10],
                    "otc": result[11]
                },
                "coords": {
                    "latitude": result[12],
                    "longitude": result[13],
                    "height": result[14]
                },
                "level": {
                    "winter": result[15],
                    "summer": result[16],
                    "autumn": result[17],
                    "spring": result[18]
                },
                "images": images
            }

            return pereval_data

        except Exception as e:
            print(f"Error getting pereval by id: {e}")
            return None

    # Остальные методы аналогично адаптируем для SQLite...

    def update_pereval(self, pereval_id: int, data: Dict) -> Dict[str, Any]:
        """Обновить существующий перевал"""
        try:
            cursor = self.connection.cursor()

            # Проверяем статус перевала
            cursor.execute("SELECT status FROM pereval_added WHERE id = ?", (pereval_id,))
            status_result = cursor.fetchone()

            if not status_result:
                return {"state": 0, "message": "Перевал не найден"}

            if status_result[0] != "new":
                return {"state": 0, "message": "Можно редактировать только записи со статусом 'new'"}

            # Обновляем координаты если они предоставлены
            if 'coords' in data:
                coords = data['coords']
                cursor.execute("""
                    UPDATE coords 
                    SET latitude = ?, longitude = ?, height = ?
                    WHERE id = (
                        SELECT coord_id FROM pereval_added WHERE id = ?
                    )
                """, (coords.get('latitude'), coords.get('longitude'), coords.get('height'), pereval_id))

            # Обновляем уровни сложности если они предоставлены
            if 'level' in data:
                level = data['level']
                cursor.execute("""
                    UPDATE pereval_levels 
                    SET winter = COALESCE(?, winter), 
                        summer = COALESCE(?, summer), 
                        autumn = COALESCE(?, autumn), 
                        spring = COALESCE(?, spring)
                    WHERE pereval_id = ?
                """, (level.get('winter'), level.get('summer'), level.get('autumn'),
                      level.get('spring'), pereval_id))

            # Обновляем основную информацию
            update_fields = []
            update_values = []

            for field in ['beauty_title', 'title', 'other_titles', 'connect']:
                if field in data and data[field] is not None:
                    update_fields.append(f"{field} = ?")
                    update_values.append(data[field])

            if update_fields:
                update_values.append(pereval_id)
                cursor.execute(f"""
                    UPDATE pereval_added 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, update_values)

            self.connection.commit()
            return {"state": 1, "message": "Запись успешно обновлена"}

        except Exception as e:
            self.connection.rollback()
            return {"state": 0, "message": f"Ошибка при обновлении: {str(e)}"}

    def get_perevals_by_user_email(self, email: str) -> List[Dict]:
        """Получить все перевалы пользователя по email"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    pa.id, pa.beauty_title, pa.title, pa.other_titles, pa.connect, 
                    pa.add_time, pa.status,
                    u.email, u.phone, u.fam, u.name, u.otc,
                    c.latitude, c.longitude, c.height
                FROM pereval_added pa
                JOIN users u ON pa.user_id = u.id
                JOIN coords c ON pa.coord_id = c.id
                WHERE u.email = ?
                ORDER BY pa.add_time DESC
            """, (email,))

            results = cursor.fetchall()
            perevals = []

            for result in results:
                pereval_data = {
                    "id": result[0],
                    "beauty_title": result[1],
                    "title": result[2],
                    "other_titles": result[3],
                    "connect": result[4],
                    "add_time": result[5],
                    "status": result[6],
                    "user": {
                        "email": result[7],
                        "phone": result[8],
                        "fam": result[9],
                        "name": result[10],
                        "otc": result[11]
                    },
                    "coords": {
                        "latitude": result[12],
                        "longitude": result[13],
                        "height": result[14]
                    }
                }
                perevals.append(pereval_data)

            return perevals

        except Exception as e:
            print(f"Error getting perevals by user email: {e}")
            return []

    def get_pending_perevals(self) -> List[Dict]:
        """Получить перевалы ожидающие модерации"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    pa.id, pa.beauty_title, pa.title, pa.add_time,
                    u.fam, u.name, u.otc, u.email
                FROM pereval_added pa
                JOIN users u ON pa.user_id = u.id
                WHERE pa.status = 'new'
                ORDER BY pa.add_time DESC
            """)

            results = cursor.fetchall()
            perevals = []

            for result in results:
                pereval_data = {
                    "id": result[0],
                    "beauty_title": result[1],
                    "title": result[2],
                    "add_time": result[3],
                    "user_name": f"{result[4]} {result[5]} {result[6]}",
                    "user_email": result[7]
                }
                perevals.append(pereval_data)

            return perevals

        except Exception as e:
            print(f"Error getting pending perevals: {e}")
            return []

    def update_pereval_status(self, pereval_id: int, new_status: str, moderator_id: int,
                              change_reason: str = "") -> Dict:
        """Обновить статус перевала (модерация)"""
        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT status FROM pereval_added WHERE id = ?", (pereval_id,))
            result = cursor.fetchone()

            if not result:
                return {"success": False, "message": "Перевал не найден"}

            old_status = result[0]

            cursor.execute(
                "UPDATE pereval_added SET status = ? WHERE id = ?",
                (new_status, pereval_id)
            )

            cursor.execute(
                """INSERT INTO status_logs 
                (pereval_id, old_status, new_status, moderator_id, change_reason) 
                VALUES (?, ?, ?, ?, ?)""",
                (pereval_id, old_status, new_status, moderator_id, change_reason)
            )

            self.connection.commit()
            return {"success": True, "message": "Статус успешно обновлен"}

        except Exception as e:
            self.connection.rollback()
            return {"success": False, "message": f"Ошибка при обновлении статуса: {str(e)}"}