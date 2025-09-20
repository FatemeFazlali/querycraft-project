import requests
import json
import re
import logging
from django.db import connection
logger = logging.getLogger(__name__)

class QueryCraftAgent:
    def __init__(self):
        self.ollama_url = "http://ollama:11434/api/generate"
    
    def generate_sql(self, natural_language_query, max_retries=3):
        for attempt in range(max_retries):
            try:
                # Your existing code here
                response = requests.post(self.ollama_url, json=payload, timeout=120)
                # Process response
                return self.extract_sql_query(response_data.get("response", ""))
                
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Failed after {max_retries} attempts: {str(e)}")
            except Exception as e:
                raise Exception(f"Error generating SQL: {str(e)}")
        # More specific prompt with clear instructions
        prompt = f"""
        You are a SQL expert. Convert this natural language question to a PostgreSQL SELECT query only.
        
        Database Schema:
        - customers (id, name, email, registration_date)
        - products (id, name, category, price) 
        - orders (id, customer_id, product_id, order_date, quantity, status)
        
        Natural Language Question: "{natural_language_query}"
        
        IMPORTANT INSTRUCTIONS:
        1. Generate ONLY a valid PostgreSQL SELECT query
        2. Do NOT include any explanations, comments, or additional text
        3. Do NOT execute the query or show results
        4. Do NOT use markdown formatting
        5. Return only the pure SQL query
        6. Use proper SQL syntax with correct table and column names
        7. If you need to make assumptions, keep them simple and logical
        
        SQL Query:
        """
        
        # Send request to Ollama
        payload = {
            "model": "sqlcoder:7b",  # Use the 7B variant instead of full version
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 2048  # Reduce context size
            }
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=30)
            response_data = response.json()
            raw_response = response_data.get("response", "").strip()
            
            logger.info(f"Raw model response: {raw_response}")
            
            # Extract SQL query from the response
            sql_query = self.extract_sql_query(raw_response)
            
            # Validate it's a SELECT statement
            if not sql_query.upper().startswith('SELECT'):
                raise ValueError("Generated query is not a SELECT statement")
                
            # Additional validation
            if any(keyword in sql_query.upper() for keyword in ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE']):
                raise ValueError("Generated query contains unauthorized SQL operations")
                
            return sql_query
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            raise Exception(f"Error generating SQL: {str(e)}")
    
    def extract_sql_query(self, text):
        """
        Extract SQL query from model response, which might contain extra text
        """
        # Remove any markdown code blocks
        text = re.sub(r'```sql|```', '', text)
        
        # Look for SQL statements
        sql_patterns = [
            r'(SELECT.*?;)',  # SELECT statements ending with ;
            r'(SELECT.*?)(?=SELECT|$)',  # SELECT statements without ;
            r'(SELECT.*?FROM.*?WHERE.*?)',  # SELECT with WHERE
            r'(SELECT.*?FROM.*?)',  # Basic SELECT
        ]
        
        for pattern in sql_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                # Clean up the query
                query = matches[0].strip()
                # Ensure it ends with a semicolon
                if not query.endswith(';'):
                    query += ';'
                return query
        
        # If no SQL pattern found, try to clean up and return the whole text
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s_,.*=()\']', ' ', text).strip()
        if cleaned_text and any(word in cleaned_text.upper() for word in ['SELECT', 'FROM', 'WHERE']):
            if not cleaned_text.endswith(';'):
                cleaned_text += ';'
            return cleaned_text
        
        raise ValueError("No valid SQL query found in the model response")
    
    def validate_and_correct_sql(self, sql_query):
        """
        Validate and attempt to correct SQL queries
        """
        # Convert to uppercase for easier checking
        upper_query = sql_query.upper().strip()
        
        # If it's not a SELECT statement, try to extract one
        if not upper_query.startswith('SELECT'):
            # Look for SELECT statements within the text
            select_pattern = r'SELECT.*?FROM.*?(?:WHERE.*?)?(?:ORDER BY.*?)?(?:LIMIT.*?)?;?'
            matches = re.findall(select_pattern, upper_query, re.IGNORECASE | re.DOTALL)
            
            if matches:
                # Use the first SELECT statement found
                corrected_query = matches[0]
                return corrected_query
            else:
                raise ValueError("No valid SELECT statement found in the generated output")
        
        return sql_query