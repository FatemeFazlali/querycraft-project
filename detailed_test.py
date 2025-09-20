import requests
import json

def test_ollama_detailed():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "sqlcoder",
        "prompt": "Generate a PostgreSQL SELECT query to get all customers from the customers table. Return only the SQL, no explanations.",
        "stream": False
    }
    
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Full Response:", json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_ollama_detailed()