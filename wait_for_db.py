import time
import psycopg2
import os
from django.db import connection
def wait_for_db():
    attempts = 0
    max_attempts = 20
    
    db_config = {
        'host': os.environ.get('DB_HOST', 'db'),
        'database': os.environ.get('DB_NAME', 'bitpin'),
        'user': os.environ.get('DB_USER', 'bitpin'),
        'password': os.environ.get('DB_PASSWORD', 'bitpin'),
        'port': os.environ.get('DB_PORT', 5432)
    }
    
    while attempts < max_attempts:
        try:
            conn = psycopg2.connect(**db_config)
            conn.close()
            print("Database is available!")
            return True
        except Exception as e:
            attempts += 1
            print(f"Waiting for database... ({attempts}/{max_attempts}) - {str(e)}")
            time.sleep(2)
    
    print("Could not connect to database after multiple attempts")
    return False

if __name__ == "__main__":
    wait_for_db()