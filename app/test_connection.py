import psycopg2
from app.database import SQLALCHEMY_DATABASE_URL

def test_connection():
    try:
        print("🔗 Testing database connection...")
        print(f"URL: {SQLALCHEMY_DATABASE_URL}")
        
        conn = psycopg2.connect(SQLALCHEMY_DATABASE_URL)
        cursor = conn.cursor()
        
        # Простой запрос
        cursor.execute("SELECT version();")
        result = cursor.fetchone()
        
        print("✅ Connection successful!")
        print(f"PostgreSQL version: {result[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_connection()