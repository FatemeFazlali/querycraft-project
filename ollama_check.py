import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.ai_agent import QueryCraftAgent

def test_improved_agent():
    agent = QueryCraftAgent()
    
    test_queries = [
        "Show me all customers",
        "SELECT * FROM customers",
        "What are the top 5 products by sales?",
        "How many customers registered last month?"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        try:
            sql = agent.generate_sql(query)
            print(f"Generated SQL: {sql}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_improved_agent()