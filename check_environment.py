import requests
import psycopg2
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ollama():
    """Check if Ollama is running and responding"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Ollama is running")
            models = response.json().get('models', [])
            if any('sqlcoder' in model['name'] for model in models):
                logger.info("✅ SQLCoder model is available")
                return True
            else:
                logger.warning("❌ SQLCoder model not found in Ollama")
                return False
        else:
            logger.error(f"❌ Ollama responded with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to Ollama: {str(e)}")
        return False

def check_postgres():
    """Check if PostgreSQL is accessible"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="bitpin",
            user="bitpin",
            password="bitpin",
            port="5432"
        )
        conn.close()
        logger.info("✅ PostgreSQL is accessible")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect to PostgreSQL: {str(e)}")
        return False

def check_django():
    """Check if Django application is running"""
    try:
        response = requests.get("http://localhost:8000/api/test-db/", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Django application is running")
            return True
        else:
            logger.error(f"❌ Django responded with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to Django application: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Checking QueryCraft environment...")
    
    # Wait a bit for services to start
    time.sleep(5)
    
    ollama_ok = check_ollama()
    postgres_ok = check_postgres()
    django_ok = check_django()
    
    if all([ollama_ok, postgres_ok, django_ok]):
        logger.info("🎉 All services are running correctly!")
    else:
        logger.error("💥 Some services are not working properly")
        exit(1)