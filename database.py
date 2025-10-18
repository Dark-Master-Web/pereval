import psycopg
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class DatabaseManager:
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.connection = None

    def connect(self):
        """Установка соединения с базой данных"""
        try:
            self.connection = psycopg.connect(**self.db_config)
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False

    def add_pereval(self, data: Dict) -> Dict:
        """Добавление нового перевала в базу данных"""
        try:
            with self.connection.cursor() as cursor:
                # Проверяем существование пользователя
                user_data = data['user']
                cursor.execute(
                    "SELECT id FROM users WHERE email = %s",
                    (user_data['email'],)
                )
                user_result = cursor.fetchone()

                if user_result:
                    user_id = user_result[0]
                else:
                    # Создаем нового пользователя
                    cursor.execute(
                        """INSERT INTO users (email, phone, fam, name, otc) 
                        VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                        (user_data['email'], user_data['phone'], user_data['fam'],
                         user_data['name'], user_data['otc'])
                    )
                    user_id = cursor.fetchone()[0]

                # Добавляем координаты
                coords = data['coords']
                cursor.execute(
                    """INSERT INTO coords (latitude, longitude, height) 
                    VALUES (%s, %s, %s) RETURNING id""",
                    (coords['latitude'], coords['longitude'], coords['height'])
                )
                coord_id = cursor.fetchone()[0]

                # Добавляем основную информацию о перевале
                cursor.execute(
                    """INSERT INTO pereval_added 
                    (beauty_title, title, other_titles, connect, add_time, user_id, coord_id, status) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (data['beauty_title'], data['title'], data['other_titles'],
                     data['connect'], datetime.now(), user_id, coord_id, 'new')
                )
                pereval_id = cursor.fetchone()[0]

                # Добавляем уровни сложности
                level = data['level']
                cursor.execute(
                    """INSERT INTO pereval_levels (pereval_id, winter, summer, autumn, spring) 
                    VALUES (%s, %s, %s, %s, %s)""",
                    (pereval_id, level.get('winter', ''), level.get('summer', ''),
                     level.get('autumn', ''), level.get('spring', ''))
                )

                # Добавляем изображения
                for image in data['images']:
                    cursor.execute(
                        "INSERT INTO images (data, title) VALUES (%s, %s) RETURNING id",
                        (image['data'], image['title'])
                    )
                    image_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO pereval_images (pereval_id, image_id) VALUES (%s, %s)",
                        (pereval_id, image_id)
                    )

                self.connection.commit()
                return {"status": 200, "message": "Success", "id": pereval_id}

        except Exception as e:
            self.connection.rollback()
            print(f"Error adding pereval: {e}")
            return {"status": 500, "message": f"Ошибка при добавлении: {str(e)}"}

    def get_pereval_by_id(self, pereval_id: int) -> Optional[Dict]:
        """Получить перевал по ID"""
        try:
            with self.connection.cursor() as cursor:
                # Основная информация о перевале
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
                    WHERE pa.id = %s
                """, (pereval_id,))

                result = cursor.fetchone()
                if not result:
                    return None

                # Изображения
                cursor.execute("""
                    SELECT i.data, i.title 
                    FROM images i
                    JOIN pereval_images pi ON i.id = pi.image_id
                    WHERE pi.pereval_id = %s
                """, (pereval_id,))

                images = [{"data": row[0], "title": row[1]} for row in cursor.fetchall()]

                # Формируем ответ
                pereval_data = {
                    "id": result[0],
                    "beauty_title": result[1],
                    "title": result[2],
                    "other_titles": result[3],
                    "connect": result[4],
                    "add_time": result[5].isoformat() if result[5] else None,
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

    def update_pereval(self, pereval_id: int, data: Dict) -> Dict[str, Any]:
        """Обновить существующий перевал"""
        try:
            with self.connection.cursor() as cursor:
                # Проверяем статус перевала
                cursor.execute("SELECT status FROM pereval_added WHERE id = %s", (pereval_id,))
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
                        SET latitude = %s, longitude = %s, height = %s
                        WHERE id = (
                            SELECT coord_id FROM pereval_added WHERE id = %s
                        )
                    """, (coords.get('latitude'), coords.get('longitude'), coords.get('height'), pereval_id))

                # Обновляем уровни сложности если они предоставлены
                if 'level' in data:
                    level = data['level']
                    cursor.execute("""
                        UPDATE pereval_levels 
                        SET winter = COALESCE(%s, winter), 
                            summer = COALESCE(%s, summer), 
                            autumn = COALESCE(%s, autumn), 
                            spring = COALESCE(%s, spring)
                        WHERE pereval_id = %s
                    """, (level.get('winter'), level.get('summer'), level.get('autumn'),
                          level.get('spring'), pereval_id))

                # Обновляем основную информацию о перевале если предоставлена
                update_fields = []
                update_values = []

                for field in ['beauty_title', 'title', 'other_titles', 'connect']:
                    if field in data and data[field] is not None:
                        update_fields.append(f"{field} = %s")
                        update_values.append(data[field])

                if update_fields:
                    update_values.append(pereval_id)
                    cursor.execute(f"""
                        UPDATE pereval_added 
                        SET {', '.join(update_fields)}
                        WHERE id = %s
                    """, update_values)

                # Обновляем изображения если они предоставлены
                if 'images' in data and data['images'] is not None:
                    # Удаляем старые изображения
                    cursor.execute("""
                        DELETE FROM pereval_images WHERE pereval_id = %s;
                        DELETE FROM images WHERE id IN (
                            SELECT image_id FROM pereval_images WHERE pereval_id = %s
                        );
                    """, (pereval_id, pereval_id))

                    # Добавляем новые изображения
                    images = data['images']
                    for image in images:
                        cursor.execute(
                            "INSERT INTO images (data, title) VALUES (%s, %s) RETURNING id",
                            (image.get('data'), image.get('title'))
                        )
                        image_id = cursor.fetchone()[0]
                        cursor.execute(
                            "INSERT INTO pereval_images (pereval_id, image_id) VALUES (%s, %s)",
                            (pereval_id, image_id)
                        )

                self.connection.commit()
                return {"state": 1, "message": "Запись успешно обновлена"}

        except Exception as e:
            self.connection.rollback()
            print(f"Error updating pereval: {e}")
            return {"state": 0, "message": f"Ошибка при обновлении: {str(e)}"}

    def get_perevals_by_user_email(self, email: str) -> List[Dict]:
        """Получить все перевалы пользователя по email"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        pa.id, pa.beauty_title, pa.title, pa.other_titles, pa.connect, 
                        pa.add_time, pa.status,
                        u.email, u.phone, u.fam, u.name, u.otc,
                        c.latitude, c.longitude, c.height
                    FROM pereval_added pa
                    JOIN users u ON pa.user_id = u.id
                    JOIN coords c ON pa.coord_id = c.id
                    WHERE u.email = %s
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
                        "add_time": result[5].isoformat() if result[5] else None,
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
            with self.connection.cursor() as cursor:
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
                        "add_time": result[3].isoformat() if result[3] else None,
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
            with self.connection.cursor() as cursor:
                # Получаем текущий статус
                cursor.execute("SELECT status FROM pereval_added WHERE id = %s", (pereval_id,))
                result = cursor.fetchone()

                if not result:
                    return {"success": False, "message": "Перевал не найден"}

                old_status = result[0]

                # Обновляем статус
                cursor.execute(
                    "UPDATE pereval_added SET status = %s WHERE id = %s",
                    (new_status, pereval_id)
                )

                # Логируем изменение статуса
                cursor.execute(
                    """INSERT INTO status_logs 
                    (pereval_id, old_status, new_status, moderator_id, change_reason) 
                    VALUES (%s, %s, %s, %s, %s)""",
                    (pereval_id, old_status, new_status, moderator_id, change_reason)
                )

                self.connection.commit()
                return {"success": True, "message": "Статус успешно обновлен"}

        except Exception as e:
            self.connection.rollback()
            print(f"Error updating pereval status: {e}")
            return {"success": False, "message": f"Ошибка при обновлении статуса: {str(e)}"}