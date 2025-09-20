import socket
import requests
import time

def test_connectivity():
    print("Testing connection to Ollama...")
    
    # Test 1: Basic socket connection
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect(('ollama', 11434))
        print("✅ Socket connection successful")
    except Exception as e:
        print(f"❌ Socket connection failed: {e}")
        return False
    
    # Test 2: HTTP API connection
    try:
        start_time = time.time()
        response = requests.get('http://ollama:11434/api/tags', timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"✅ HTTP API connection successful ({round(end_time - start_time, 2)}s)")
            print(f"Available models: {[m['name'] for m in response.json().get('models', [])]}")
            return True
        else:
            print(f"❌ HTTP API returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ HTTP API connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connectivity()