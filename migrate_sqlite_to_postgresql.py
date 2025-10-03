#!/usr/bin/env python3
"""
Скрипт миграции данных из SQLite в PostgreSQL для проекта "Сделка"
Автор: AI Assistant
Дата: 2025
"""

import sqlite3
import psycopg2
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Класс для миграции данных между базами данных"""
    
    def __init__(self, sqlite_path: str, postgres_config: Dict[str, Any]):
        self.sqlite_path = sqlite_path
        self.postgres_config = postgres_config
        self.sqlite_conn = None
        self.postgres_conn = None
        
    def connect_sqlite(self) -> bool:
        """Подключение к SQLite"""
        try:
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"Подключение к SQLite установлено: {self.sqlite_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к SQLite: {e}")
            return False
    
    def connect_postgresql(self) -> bool:
        """Подключение к PostgreSQL"""
        try:
            self.postgres_conn = psycopg2.connect(
                host=self.postgres_config['host'],
                port=self.postgres_config['port'],
                database=self.postgres_config['database'],
                user=self.postgres_config['user'],
                password=self.postgres_config['password']
            )
            logger.info(f"Подключение к PostgreSQL установлено: {self.postgres_config['host']}:{self.postgres_config['port']}")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            return False
    
    def create_postgresql_tables(self) -> bool:
        """Создание таблиц в PostgreSQL"""
        try:
            cursor = self.postgres_conn.cursor()
            
            # Создание таблицы сотрудников
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    position VARCHAR(255) NOT NULL,
                    department VARCHAR(255) NOT NULL,
                    phone VARCHAR(50),
                    email VARCHAR(255),
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Создание таблицы изделий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    unit VARCHAR(50) NOT NULL,
                    article VARCHAR(100),
                    category VARCHAR(255),
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Создание таблицы видов работ
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS work_types (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    unit VARCHAR(50) NOT NULL,
                    price REAL NOT NULL DEFAULT 0.0,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Создание таблицы контрактов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contracts (
                    id VARCHAR(36) PRIMARY KEY,
                    number VARCHAR(100) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    client VARCHAR(255) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    total_amount REAL NOT NULL DEFAULT 0.0,
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Создание таблицы нарядов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS work_orders (
                    id VARCHAR(36) PRIMARY KEY,
                    number VARCHAR(100) NOT NULL UNIQUE,
                    date DATE NOT NULL,
                    department VARCHAR(255) NOT NULL,
                    description TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'draft',
                    total_amount REAL NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Создание таблицы элементов наряда
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS work_order_items (
                    id VARCHAR(36) PRIMARY KEY,
                    work_order_id VARCHAR(36) NOT NULL,
                    work_type_id VARCHAR(36) NOT NULL,
                    employee_id VARCHAR(36) NOT NULL,
                    quantity REAL NOT NULL,
                    unit_price REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (work_type_id) REFERENCES work_types(id),
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                );
            ''')
            
            # Создание таблицы изделий наряда
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS work_order_products (
                    id VARCHAR(36) PRIMARY KEY,
                    work_order_id VARCHAR(36) NOT NULL,
                    product_id VARCHAR(36) NOT NULL,
                    quantity REAL NOT NULL,
                    unit_price REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                );
            ''')
            
            # Создание таблицы рабочих наряда
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS work_order_workers (
                    id VARCHAR(36) PRIMARY KEY,
                    work_order_id VARCHAR(36) NOT NULL,
                    employee_id VARCHAR(36) NOT NULL,
                    role VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                );
            ''')
            
            # Создание таблицы истории контрактов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contract_history (
                    id VARCHAR(36) PRIMARY KEY,
                    contract_id VARCHAR(36) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    description TEXT,
                    amount REAL,
                    date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
                );
            ''')
            
            # Создание индексов
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_date ON work_orders(date);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_order_items_work_order ON work_order_items(work_order_id);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);')
            
            self.postgres_conn.commit()
            cursor.close()
            logger.info("Таблицы PostgreSQL созданы успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка создания таблиц PostgreSQL: {e}")
            if self.postgres_conn:
                self.postgres_conn.rollback()
            return False
    
    def migrate_table(self, table_name: str, columns: List[str], 
                     id_mapping: Optional[Dict[str, str]] = None) -> bool:
        """Миграция данных из одной таблицы"""
        try:
            cursor_sqlite = self.sqlite_conn.cursor()
            cursor_postgres = self.postgres_conn.cursor()
            
            # Получаем данные из SQLite
            cursor_sqlite.execute(f"SELECT * FROM {table_name}")
            rows = cursor_sqlite.fetchall()
            
            logger.info(f"Найдено {len(rows)} записей в таблице {table_name}")
            
            # Подготавливаем данные для вставки
            for row in rows:
                row_dict = dict(row)
                
                # Генерируем новый UUID если нужно
                if id_mapping and row_dict['id'] in id_mapping:
                    row_dict['id'] = id_mapping[row_dict['id']]
                elif 'id' in row_dict and not row_dict['id']:
                    row_dict['id'] = str(uuid.uuid4())
                
                # Конвертируем данные для PostgreSQL
                values = []
                placeholders = []
                
                for col in columns:
                    value = row_dict.get(col)
                    
                    # Конвертация типов данных
                    if col in ['is_active'] and value is not None:
                        value = bool(value) if isinstance(value, int) else value
                    elif col in ['created_at', 'updated_at'] and value:
                        if isinstance(value, str):
                            try:
                                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            except:
                                value = datetime.now()
                    
                    values.append(value)
                    placeholders.append('%s')
                
                # Вставляем данные в PostgreSQL
                insert_query = f"""
                    INSERT INTO {table_name} ({', '.join(columns)}) 
                    VALUES ({', '.join(placeholders)})
                    ON CONFLICT (id) DO UPDATE SET
                    {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'])}
                """
                
                cursor_postgres.execute(insert_query, values)
            
            self.postgres_conn.commit()
            cursor_sqlite.close()
            cursor_postgres.close()
            
            logger.info(f"Таблица {table_name} мигрирована успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка миграции таблицы {table_name}: {e}")
            if self.postgres_conn:
                self.postgres_conn.rollback()
            return False
    
    def migrate_all_data(self) -> bool:
        """Миграция всех данных"""
        try:
            logger.info("Начинаем миграцию данных...")
            
            # Создаем таблицы в PostgreSQL
            if not self.create_postgresql_tables():
                return False
            
            # Миграция справочных данных
            tables_config = [
                ('employees', ['id', 'name', 'position', 'department', 'phone', 'email', 'is_active', 'created_at', 'updated_at']),
                ('products', ['id', 'name', 'description', 'unit', 'article', 'category', 'is_active', 'created_at', 'updated_at']),
                ('work_types', ['id', 'name', 'description', 'unit', 'price', 'is_active', 'created_at', 'updated_at']),
                ('contracts', ['id', 'number', 'name', 'client', 'start_date', 'end_date', 'total_amount', 'status', 'created_at', 'updated_at']),
            ]
            
            for table_name, columns in tables_config:
                if not self.migrate_table(table_name, columns):
                    logger.error(f"Не удалось мигрировать таблицу {table_name}")
                    return False
            
            # Миграция основных данных
            main_tables_config = [
                ('work_orders', ['id', 'number', 'date', 'department', 'description', 'status', 'total_amount', 'created_at', 'updated_at']),
                ('work_order_items', ['id', 'work_order_id', 'work_type_id', 'employee_id', 'quantity', 'unit_price', 'total_amount', 'created_at']),
                ('work_order_products', ['id', 'work_order_id', 'product_id', 'quantity', 'unit_price', 'total_amount', 'created_at']),
                ('work_order_workers', ['id', 'work_order_id', 'employee_id', 'role', 'created_at']),
                ('contract_history', ['id', 'contract_id', 'action', 'description', 'amount', 'date', 'created_at']),
            ]
            
            for table_name, columns in main_tables_config:
                if not self.migrate_table(table_name, columns):
                    logger.error(f"Не удалось мигрировать таблицу {table_name}")
                    return False
            
            logger.info("Миграция данных завершена успешно!")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка миграции данных: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Проверка корректности миграции"""
        try:
            cursor_sqlite = self.sqlite_conn.cursor()
            cursor_postgres = self.postgres_conn.cursor()
            
            tables = ['employees', 'products', 'work_types', 'contracts', 'work_orders']
            
            for table in tables:
                # Подсчет записей в SQLite
                cursor_sqlite.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = cursor_sqlite.fetchone()[0]
                
                # Подсчет записей в PostgreSQL
                cursor_postgres.execute(f"SELECT COUNT(*) FROM {table}")
                postgres_count = cursor_postgres.fetchone()[0]
                
                logger.info(f"Таблица {table}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
                
                if sqlite_count != postgres_count:
                    logger.warning(f"Несоответствие количества записей в таблице {table}")
                    return False
            
            cursor_sqlite.close()
            cursor_postgres.close()
            
            logger.info("Проверка миграции завершена успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки миграции: {e}")
            return False
    
    def close_connections(self):
        """Закрытие соединений"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.postgres_conn:
            self.postgres_conn.close()
        logger.info("Соединения закрыты")

def main():
    """Главная функция"""
    logger.info("=== Миграция данных SQLite → PostgreSQL ===")
    
    # Конфигурация
    sqlite_path = "data/base_sdelka_rmz.db"  # Путь к SQLite базе
    postgres_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'sdelka_v4',
        'user': 'sdelka_user',
        'password': 'sdelka_password'
    }
    
    # Проверяем существование SQLite файла
    if not Path(sqlite_path).exists():
        logger.error(f"SQLite файл не найден: {sqlite_path}")
        return False
    
    # Создаем мигратор
    migrator = DatabaseMigrator(sqlite_path, postgres_config)
    
    try:
        # Подключаемся к базам данных
        if not migrator.connect_sqlite():
            logger.error("Не удалось подключиться к SQLite")
            return False
        
        if not migrator.connect_postgresql():
            logger.error("Не удалось подключиться к PostgreSQL")
            logger.info("Убедитесь, что PostgreSQL установлен и запущен")
            logger.info("Создайте базу данных: CREATE DATABASE sdelka_v4;")
            logger.info("Создайте пользователя: CREATE USER sdelka_user WITH PASSWORD 'sdelka_password';")
            logger.info("Предоставьте права: GRANT ALL PRIVILEGES ON DATABASE sdelka_v4 TO sdelka_user;")
            return False
        
        # Выполняем миграцию
        if migrator.migrate_all_data():
            # Проверяем результат
            if migrator.verify_migration():
                logger.info("✅ Миграция завершена успешно!")
                return True
            else:
                logger.error("❌ Ошибки при проверке миграции")
                return False
        else:
            logger.error("❌ Ошибка миграции данных")
            return False
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return False
    finally:
        migrator.close_connections()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
