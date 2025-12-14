"""
Скрипт для виконання SQL міграцій
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Отримуємо параметри підключення
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_NAME]):
    print(
        "Помилка: Переконайтеся, що в .env файлі встановлені DB_USER, DB_PASSWORD, DB_NAME"
    )
    exit(1)

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}"
)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Шлях до файлу міграції
migration_file = Path(__file__).parent / "migrations" / "add_audit_log_protection.sql"

if not migration_file.exists():
    print(f"Помилка: Файл міграції не знайдено: {migration_file}")
    exit(1)

print(f"Виконуємо міграцію: {migration_file}")
print("-" * 50)

try:
    with engine.connect() as connection:
        # Читаємо SQL файл
        sql_content = migration_file.read_text(encoding="utf-8")

        # Виконуємо SQL
        connection.execute(text(sql_content))
        connection.commit()

    print("✅ Міграція успішно виконана!")
    print("\nСтворено:")
    print("  - Тригери для захисту від UPDATE/DELETE")
    print("  - Індекси для оптимізації пошуку")

except Exception as e:
    print(f"❌ Помилка при виконанні міграції: {e}")
    exit(1)
