import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"🔗 Testing connection to: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print(" Connection successful!")
        
        # Проверяем версию PostgreSQL
        result = conn.execute(text("SELECT version();"))
        print(f" PostgreSQL version: {result.fetchone()[0]}")
        
        # Проверяем существующие таблицы
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        tables = [row[0] for row in result]
        print(f" Existing tables: {tables}")
        
except Exception as e:
    print(f" Connection failed: {e}")
