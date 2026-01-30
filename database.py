import sqlite3
import threading
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from config import DB_PATH, BASE_PRICE


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._lock = threading.Lock()

    @contextmanager
    def connection(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def init_db(self):
        with self.connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    quantity INTEGER DEFAULT 0 CHECK(quantity >= 0),
                    price INTEGER DEFAULT 650,
                    photo_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1 CHECK(quantity >= 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, product_id),
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_name TEXT,
                    total_amount INTEGER NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price INTEGER NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            ''')

    # ... (остальные методы без изменений до get_all_products) ...

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Получить все товары из базы данных"""
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM products ORDER BY id')
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Ошибка при получении товаров: {e}")
            return []

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM products WHERE id = ?', (product_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Ошибка при получении товара: {e}")
            return None

    def update_product_quantity(self, product_id: int, quantity: int) -> bool:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE products 
                    SET quantity = ?
                    WHERE id = ?
                ''', (max(0, quantity), product_id))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при обновлении количества: {e}")
            return False

    def update_product_price(self, product_id: int, price: int) -> bool:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE products 
                    SET price = ?
                    WHERE id = ?
                ''', (max(0, price), product_id))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при обновлении цены: {e}")
            return False

    def update_product_photo(self, product_id: int, photo_id: str) -> bool:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE products 
                    SET photo_id = ?
                    WHERE id = ?
                ''', (photo_id, product_id))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при обновлении фото: {e}")
            return False

    def add_product(self, name: str, quantity: int, price: int, photo_id: str = "") -> Optional[int]:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO products (name, quantity, price, photo_id)
                    VALUES (?, ?, ?, ?)
                ''', (name.strip(), max(0, quantity), price, photo_id))
                return cursor.lastrowid
        except Exception as e:
            print(f"Ошибка при добавлении товара: {e}")
            return None

    def delete_product(self, product_id: int) -> bool:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM products WHERE id = ?', (product_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при удалении товара: {e}")
            return False

    def get_cart_items(self, user_id: int) -> List[Dict[str, Any]]:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT c.*, p.name, p.price, p.photo_id, 
                           p.quantity as available_quantity
                    FROM cart c
                    LEFT JOIN products p ON c.product_id = p.id
                    WHERE c.user_id = ? AND p.id IS NOT NULL
                ''', (user_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Ошибка при получении корзины: {e}")
            return []

    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> Tuple[bool, str]:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT quantity FROM products 
                    WHERE id = ?
                ''', (product_id,))

                result = cursor.fetchone()
                if not result:
                    return False, "Товар не найден"

                available = result[0]

                cursor.execute('''
                    SELECT quantity FROM cart 
                    WHERE user_id = ? AND product_id = ?
                ''', (user_id, product_id))

                result = cursor.fetchone()
                current_qty = result[0] if result else 0
                total_qty = current_qty + quantity

                if total_qty > available:
                    return False, f"Нельзя добавить больше {available} шт."

                if result:
                    cursor.execute('''
                        UPDATE cart SET quantity = ?
                        WHERE user_id = ? AND product_id = ?
                    ''', (total_qty, user_id, product_id))
                else:
                    cursor.execute('''
                        INSERT INTO cart (user_id, product_id, quantity)
                        VALUES (?, ?, ?)
                    ''', (user_id, product_id, quantity))

                return True, "Успешно добавлено"

        except Exception as e:
            print(f"Ошибка при добавлении в корзину: {e}")
            return False, "Ошибка базы данных"

    def remove_from_cart(self, user_id: int, product_id: int, quantity: int = 1) -> Tuple[bool, str]:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT quantity FROM cart 
                    WHERE user_id = ? AND product_id = ?
                ''', (user_id, product_id))

                result = cursor.fetchone()
                if not result:
                    return False, "Товар не найден в корзине"

                current_qty = result[0]
                new_qty = current_qty - quantity

                if new_qty <= 0:
                    cursor.execute('''
                        DELETE FROM cart 
                        WHERE user_id = ? AND product_id = ?
                    ''', (user_id, product_id))
                    return True, "Товар удален из корзины"
                else:
                    cursor.execute('''
                        UPDATE cart 
                        SET quantity = ?
                        WHERE user_id = ? AND product_id = ?
                    ''', (new_qty, user_id, product_id))
                    return True, f"Количество уменьшено до {new_qty}"

        except Exception as e:
            print(f"Ошибка при удалении из корзины: {e}")
            return False, "Ошибка базы данных"

    def clear_cart(self, user_id: int) -> bool:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM cart WHERE user_id = ?', (user_id,))
                return True
        except Exception as e:
            print(f"Ошибка при очистке корзины: {e}")
            return False

    def get_cart_total(self, user_id: int) -> Dict[str, Any]:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        COALESCE(SUM(c.quantity), 0) as total_items,
                        COALESCE(SUM(c.quantity * p.price), 0) as total_price
                    FROM cart c
                    JOIN products p ON c.product_id = p.id
                    WHERE c.user_id = ?
                ''', (user_id,))
                result = cursor.fetchone()
                return {
                    'total_items': result[0] if result else 0,
                    'total_price': result[1] if result else 0
                }
        except Exception as e:
            print(f"Ошибка при получении суммы корзины: {e}")
            return {'total_items': 0, 'total_price': 0}

    def create_order(self, user_id: int, user_name: str, comment: str = "") -> Tuple[Optional[int], str, List[Dict[str, Any]]]:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()

            cursor.execute('''
                SELECT c.product_id, c.quantity, p.price, p.quantity as available, p.name
                FROM cart c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
            ''', (user_id,))

            rows = cursor.fetchall()
            cart_items = [dict(row) for row in rows]

            if not cart_items:
                return None, "Корзина пуста", []

            for item in cart_items:
                if item['quantity'] > item['available']:
                    return None, f"Недостаточно товара ID {item['product_id']} на складе", []

            # Рассчитываем общую сумму с учетом скидок
            total = 0
            cart_items_with_discount = []

            for item in cart_items:
                quantity = item['quantity']
                # Применяем скидку в зависимости от количества
                if quantity == 1:
                    price_with_discount = 650
                elif quantity == 2:
                    price_with_discount = 625
                elif quantity == 3:
                    price_with_discount = 600
                elif quantity == 4:
                    price_with_discount = 575
                else:  # 5 и более
                    price_with_discount = 550

                item_total = quantity * price_with_discount
                total += item_total

                # Создаем копию элемента с ценой со скидкой
                item_with_discount = item.copy()
                item_with_discount['price_with_discount'] = price_with_discount
                item_with_discount['total_with_discount'] = item_total
                cart_items_with_discount.append(item_with_discount)

            cursor.execute('''
                INSERT INTO orders (user_id, user_name, total_amount, comment)
                VALUES (?, ?, ?, ?)
            ''', (user_id, user_name, total, comment))

            order_id = cursor.lastrowid

            # Сохраняем товары с ценами со скидкой
            for item in cart_items_with_discount:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, item['product_id'], item['quantity'], item['price_with_discount']))

                cursor.execute('''
                    UPDATE products 
                    SET quantity = quantity - ?
                    WHERE id = ?
                ''', (item['quantity'], item['product_id']))

            cursor.execute(
                'DELETE FROM cart WHERE user_id = ?', (user_id,))

            return order_id, f"{total} рублей", cart_items_with_discount

        except Exception as e:
            print(f"Ошибка при создании заказа: {e}")
            return None, f"Ошибка создания заказа: {str(e)[:50]}", []

    def get_all_orders(self) -> List[Dict[str, Any]]:
        try:
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT o.*, 
                           GROUP_CONCAT(p.name || ' x' || oi.quantity) as items
                    FROM orders o
                    JOIN order_items oi ON o.id = oi.order_id
                    JOIN products p ON oi.product_id = p.id
                    GROUP BY o.id
                    ORDER BY o.created_at DESC
                ''')
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Ошибка при получении заказов: {e}")
            return []


db = Database()
