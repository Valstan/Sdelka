#!/usr/bin/env python3
"""
Упрощенный скрипт для запуска PostgreSQL в Docker
Автор: AI Assistant
"""

import subprocess
import time
import logging
import psycopg2
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_docker_postgresql():
    """Запуск PostgreSQL в Docker контейнере"""
    
    logger.info("🚀 Запуск PostgreSQL в Docker...")
    
    try:
        # Проверяем, запущен ли уже контейнер
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", "name=postgres-sdelka"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            logger.info("✅ PostgreSQL контейнер уже запущен")
            return True
        
        # Запускаем PostgreSQL контейнер
        cmd = [
            "docker", "run", "-d",
            "--name", "postgres-sdelka",
            "-e", "POSTGRES_DB=sdelka_v4",
            "-e", "POSTGRES_USER=sdelka_user", 
            "-e", "POSTGRES_PASSWORD=sdelka_password",
            "-p", "5432:5432",
            "postgres:15"
        ]
        
        logger.info(f"Выполняем команду: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ PostgreSQL контейнер запущен успешно")
            
            # Ждем запуска базы данных
            logger.info("⏳ Ожидаем запуска PostgreSQL...")
            time.sleep(10)
            
            # Проверяем подключение
            if test_postgresql_connection():
                logger.info("✅ PostgreSQL готов к работе!")
                return True
            else:
                logger.error("❌ Не удалось подключиться к PostgreSQL")
                return False
        else:
            logger.error(f"❌ Ошибка запуска контейнера: {result.stderr}")
            return False
            
    except FileNotFoundError:
        logger.error("❌ Docker не найден. Установите Docker Desktop")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False

def test_postgresql_connection():
    """Тестирование подключения к PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="sdelka_v4",
            user="sdelka_user",
            password="sdelka_password"
        )
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения: {e}")
        return False

def stop_docker_postgresql():
    """Остановка PostgreSQL контейнера"""
    try:
        subprocess.run(["docker", "stop", "postgres-sdelka"], capture_output=True)
        subprocess.run(["docker", "rm", "postgres-sdelka"], capture_output=True)
        logger.info("✅ PostgreSQL контейнер остановлен")
    except Exception as e:
        logger.error(f"Ошибка остановки: {e}")

def main():
    """Главная функция"""
    logger.info("=== Управление PostgreSQL в Docker ===")
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_docker_postgresql()
        return
    
    success = run_docker_postgresql()
    
    if success:
        logger.info("🎉 PostgreSQL готов к использованию!")
        logger.info("📋 Параметры подключения:")
        logger.info("   Host: localhost")
        logger.info("   Port: 5432") 
        logger.info("   Database: sdelka_v4")
        logger.info("   User: sdelka_user")
        logger.info("   Password: sdelka_password")
        logger.info("")
        logger.info("💡 Для остановки выполните: python docker_postgresql.py stop")
    else:
        logger.error("❌ Не удалось запустить PostgreSQL")

if __name__ == "__main__":
    main()
