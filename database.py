import os
import psycopg
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
from datetime import datetime
import base64
import binascii

load_dotenv()


class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        """Установка соединения с базой данных"""
        try:
            self.conn = psycopg.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                dbname=os.getenv('DB_NAME', 'mountain_pass_db'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432')
            )
            print("✅ Успешное подключение к БД")
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")

    # --- МЕТОДЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ---
    def add_user(self, email: str, phone: str, fam: str, name: str, otc: str = None) -> int:
        """Добавляет пользователя и возвращает его ID."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (email, phone, fam, name, otc)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                """, (email, phone, fam, name, otc))
                result = cur.fetchone()
                self.conn.commit()
                user_id = result[0]
                print(f"✅ Пользователь добавлен, ID: {user_id}")
                return user_id
        except psycopg.IntegrityError:
            # Если пользователь уже существует, возвращаем его ID
            self.conn.rollback()
            with self.conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                result = cur.fetchone()
                if result:
                    print(f"✅ Пользователь уже существует, ID: {result[0]}")
                    return result[0]
                raise
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Ошибка при добавлении пользователя: {e}")
            raise

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Получает пользователя по email."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, email, phone, fam, name, otc
                    FROM users 
                    WHERE email = %s;
                """, (email,))
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            print(f"❌ Ошибка при получении пользователя: {e}")
            return None

    # --- МЕТОДЫ ДЛЯ КООРДИНАТ ---
    def add_coords(self, latitude: float, longitude: float, height: int) -> int:
        """Добавляет координаты и возвращает их ID."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO coords (latitude, longitude, height)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (latitude, longitude, height))
                result = cur.fetchone()
                self.conn.commit()
                coord_id = result[0]
                print(f"✅ Координаты добавлены, ID: {coord_id}")
                return coord_id
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Ошибка при добавлении координат: {e}")
            raise

    # --- МЕТОДЫ ДЛЯ ПЕРЕВАЛОВ ---
    def add_pereval(self, beauty_title: str, title: str, other_titles: str, connect: str, user_id: int, coord_id: int,
                    status: str = "new") -> int:
        """Добавляет перевал и возвращает его ID."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO pereval_added (beauty_title, title, other_titles, connect, user_id, coord_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (beauty_title, title, other_titles, connect, user_id, coord_id, status))
                result = cur.fetchone()
                self.conn.commit()
                pereval_id = result[0]
                print(f"✅ Перевал добавлен, ID: {pereval_id}")
                return pereval_id
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Ошибка при добавлении перевала: {e}")
            raise

    def get_pereval_by_id(self, pereval_id: int) -> Optional[Dict[str, Any]]:
        """Получает перевал по ID со всей связанной информацией."""
        try:
            with self.conn.cursor() as cur:
                # Основная информация о перевале
                cur.execute("""
                    SELECT 
                        pa.*,
                        u.email, u.phone, u.fam, u.name, u.otc,
                        c.latitude, c.longitude, c.height,
                        pl.winter, pl.summer, pl.autumn, pl.spring
                    FROM pereval_added pa
                    LEFT JOIN users u ON pa.user_id = u.id
                    LEFT JOIN coords c ON pa.coord_id = c.id
                    LEFT JOIN pereval_levels pl ON pa.id = pl.pereval_id
                    WHERE pa.id = %s;
                """, (pereval_id,))
                result = cur.fetchone()

                if not result:
                    return None

                pereval_data = dict(result)

                # Получаем изображения
                cur.execute("""
                    SELECT i.id, i.title 
                    FROM images i
                    JOIN pereval_images pi ON i.id = pi.image_id
                    WHERE pi.pereval_id = %s;
                """, (pereval_id,))
                images = [dict(row) for row in cur.fetchall()]
                pereval_data['images'] = images

                return pereval_data

        except Exception as e:
            print(f"❌ Ошибка при получении перевала: {e}")
            return None

    def get_perevals_by_user(self, user_email: str) -> List[Dict[str, Any]]:
        """Получает все перевалы, добавленные пользователем."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        pa.id, pa.beauty_title, pa.title, pa.status, pa.add_time,
                        c.latitude, c.longitude, c.height
                    FROM pereval_added pa
                    JOIN users u ON pa.user_id = u.id
                    JOIN coords c ON pa.coord_id = c.id
                    WHERE u.email = %s
                    ORDER BY pa.add_time DESC;
                """, (user_email,))
                results = [dict(row) for row in cur.fetchall()]
                return results

        except Exception as e:
            print(f"❌ Ошибка при получении перевалов пользователя: {e}")
            return []

    # --- МЕТОДЫ ДЛЯ УРОВНЕЙ СЛОЖНОСТИ ---
    def add_levels(self, pereval_id: int, winter: str = None, summer: str = None, autumn: str = None,
                   spring: str = None):
        """Добавляет уровни сложности для перевала."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO pereval_levels (pereval_id, winter, summer, autumn, spring)
                    VALUES (%s, %s, %s, %s, %s);
                """, (pereval_id, winter, summer, autumn, spring))
                self.conn.commit()
                print(f"✅ Уровни сложности добавлены для перевала ID: {pereval_id}")
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Ошибка при добавлении уровней сложности: {e}")
            raise

    # --- МЕТОДЫ ДЛЯ ИЗОБРАЖЕНИЙ ---
    def add_image(self, image_data: bytes, title: str) -> int:
        """Добавляет изображение и возвращает его ID."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO images (data, title)
                    VALUES (%s, %s)
                    RETURNING id;
                """, (image_data, title))
                result = cur.fetchone()
                self.conn.commit()
                image_id = result[0]
                print(f"✅ Изображение добавлено, ID: {image_id}")
                return image_id
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Ошибка при добавлении изображения: {e}")
            raise

    def add_image_base64(self, image_base64: str, title: str) -> int:
        """Добавляет изображение из base64 строки."""
        try:
            # Проверяем и очищаем base64 строку
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]

            # Декодируем base64
            image_data = base64.b64decode(image_base64)
            return self.add_image(image_data, title)
        except binascii.Error as e:
            print(f"❌ Ошибка декодирования base64: {e}")
            raise ValueError("Invalid base64 string")
        except Exception as e:
            print(f"❌ Ошибка при обработке base64 изображения: {e}")
            raise

    def link_image_to_pereval(self, pereval_id: int, image_id: int):
        """Связывает изображение с перевалом."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO pereval_images (pereval_id, image_id)
                    VALUES (%s, %s);
                """, (pereval_id, image_id))
                self.conn.commit()
                print(f"✅ Изображение {image_id} связано с перевалом {pereval_id}")
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Ошибка при связывании изображения: {e}")
            raise

    def get_pereval_images(self, pereval_id: int) -> List[Dict[str, Any]]:
        """Получает все изображения перевала."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT i.id, i.title, i.created_at
                    FROM images i
                    JOIN pereval_images pi ON i.id = pi.image_id
                    WHERE pi.pereval_id = %s
                    ORDER BY i.created_at;
                """, (pereval_id,))

                images = [dict(row) for row in cur.fetchall()]
                return images

        except Exception as e:
            print(f"❌ Ошибка при получении изображений: {e}")
            return []

    # --- МЕТОДЫ ДЛЯ МОДЕРАЦИИ ---
    def get_perevals_paginated(self, status: str = None, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        """Получает перевалы с пагинацией и фильтрацией по статусу."""
        try:
            with self.conn.cursor() as cur:
                # Базовый запрос
                query = """
                    SELECT 
                        pa.id, pa.beauty_title, pa.title, pa.status, pa.add_time,
                        u.fam, u.name, u.otc, u.email,
                        c.latitude, c.longitude, c.height
                    FROM pereval_added pa
                    JOIN users u ON pa.user_id = u.id
                    JOIN coords c ON pa.coord_id = c.id
                """
                count_query = "SELECT COUNT(*) FROM pereval_added pa"

                params = []
                where_conditions = []

                # Фильтр по статусу
                if status:
                    where_conditions.append("pa.status = %s")
                    params.append(status)

                # Добавляем условия WHERE если есть
                if where_conditions:
                    where_clause = " WHERE " + " AND ".join(where_conditions)
                    query += where_clause
                    count_query += where_clause

                # Добавляем сортировку и пагинацию
                query += " ORDER BY pa.add_time DESC LIMIT %s OFFSET %s"
                params.extend([limit, skip])

                # Получаем данные
                cur.execute(query, params)
                perevals = [dict(row) for row in cur.fetchall()]

                # Получаем общее количество
                cur.execute(count_query, params[:len(where_conditions)])
                total = cur.fetchone()[0]

                return {
                    "perevals": perevals,
                    "total": total,
                    "skip": skip,
                    "limit": limit
                }

        except Exception as e:
            print(f"❌ Ошибка при получении перевалов: {e}")
            return {"perevals": [], "total": 0, "skip": skip, "limit": limit}

    def update_pereval_status(self, pereval_id: int, status: str, moderator_id: int = None,
                              reject_reason: str = None) -> bool:
        """Обновляет статус перевала и логирует изменение."""
        try:
            with self.conn.cursor() as cur:
                # Получаем текущий статус
                cur.execute("SELECT status FROM pereval_added WHERE id = %s", (pereval_id,))
                result = cur.fetchone()
                if not result:
                    return False

                old_status = result[0]

                # Обновляем статус перевала
                if reject_reason:
                    cur.execute("""
                        UPDATE pereval_added 
                        SET status = %s, reject_reason = %s
                        WHERE id = %s;
                    """, (status, reject_reason, pereval_id))
                else:
                    cur.execute("""
                        UPDATE pereval_added 
                        SET status = %s, reject_reason = NULL
                        WHERE id = %s;
                    """, (status, pereval_id))

                # Логируем изменение статуса
                cur.execute("""
                    INSERT INTO status_logs (pereval_id, old_status, new_status, moderator_id, change_reason)
                    VALUES (%s, %s, %s, %s, %s);
                """, (pereval_id, old_status, status, moderator_id, reject_reason))

                self.conn.commit()
                print(f"✅ Статус перевала {pereval_id} обновлен с '{old_status}' на '{status}'")
                return True

        except Exception as e:
            self.conn.rollback()
            print(f"❌ Ошибка при обновлении статуса: {e}")
            return False

    def get_status_history(self, pereval_id: int) -> List[Dict[str, Any]]:
        """Получает историю изменений статуса перевала."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        sl.old_status, sl.new_status, sl.change_reason, sl.changed_at,
                        m.username as moderator_name
                    FROM status_logs sl
                    LEFT JOIN moderators m ON sl.moderator_id = m.id
                    WHERE sl.pereval_id = %s
                    ORDER BY sl.changed_at DESC;
                """, (pereval_id,))

                history = [dict(row) for row in cur.fetchall()]
                return history

        except Exception as e:
            print(f"❌ Ошибка при получении истории статусов: {e}")
            return []

    # --- МЕТОДЫ ДЛЯ МОДЕРАТОРОВ ---
    def create_moderator(self, username: str, email: str, password_hash: str) -> bool:
        """Создает нового модератора."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO moderators (username, email, password_hash)
                    VALUES (%s, %s, %s);
                """, (username, email, password_hash))
                self.conn.commit()
                print(f"✅ Модератор {username} создан")
                return True

        except Exception as e:
            self.conn.rollback()
            print(f"❌ Ошибка при создании модератора: {e}")
            return False

    def get_moderator_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Получает модератора по email."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, email, password_hash, is_active
                    FROM moderators 
                    WHERE email = %s AND is_active = TRUE;
                """, (email,))
                result = cur.fetchone()
                return dict(result) if result else None

        except Exception as e:
            print(f"❌ Ошибка при получении модератора: {e}")
            return None

    def get_moderator_by_id(self, moderator_id: int) -> Optional[Dict[str, Any]]:
        """Получает модератора по ID."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, email, is_active, created_at
                    FROM moderators 
                    WHERE id = %s AND is_active = TRUE;
                """, (moderator_id,))
                result = cur.fetchone()
                return dict(result) if result else None

        except Exception as e:
            print(f"❌ Ошибка при получении модератора: {e}")
            return None

    def close(self):
        """Закрывает соединение с БД."""
        if self.conn:
            self.conn.close()
            print("✅ Соединение с БД закрыто")