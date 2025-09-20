import requests
import re
import logging
import time
import json
from typing import TypedDict, Optional, Literal, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from django.db import connection
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    question: str
    sql_query: Optional[str]
    validation_result: Optional[Literal["valid", "invalid"]]
    execution_result: Optional[List[Dict]]
    error: Optional[str]
    execution_time: Optional[float]
    tokens_used: Optional[int]
    query_complexity: Optional[Literal["simple", "medium", "complex"]]

class QueryHistory:
    """Simple in-memory query history storage"""
    def __init__(self, max_history=50):
        self.history = []
        self.max_history = max_history
    
    def add_entry(self, question, sql_query, results, execution_time, error=None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "sql_query": sql_query,
            "results": results,
            "execution_time": execution_time,
            "error": error
        }
        
        self.history.append(entry)
        
        # Keep only the most recent entries
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        return entry
    
    def get_history(self, limit=10):
        return self.history[-limit:] if limit else self.history
    
    def clear_history(self):
        self.history = []

class QueryCraftLangGraphAgent:
    def __init__(self):
        self.ollama_url = "http://ollama:11434/api/generate"
        self.workflow = self.build_workflow()
        self.query_history = QueryHistory()
        self.complex_queries = {
            "joins": ["JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"],
            "aggregations": ["COUNT", "SUM", "AVG", "MIN", "MAX", "GROUP BY"],
            "subqueries": ["SELECT.*SELECT", "EXISTS", "IN .*SELECT", "ANY.*SELECT"],
            "window_functions": ["ROW_NUMBER", "RANK", "DENSE_RANK", "NTILE", "LEAD", "LAG"]
        }
    
    def build_workflow(self):
        # Define the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_complexity", self.analyze_complexity_node)
        workflow.add_node("generate_sql", self.generate_sql_node)
        workflow.add_node("validate_sql", self.validate_sql_node)
        workflow.add_node("execute_sql", self.execute_sql_node)
        workflow.add_node("handle_error", self.handle_error_node)
        workflow.add_node("log_to_history", self.log_to_history_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_complexity")
        
        # Add edges
        workflow.add_edge("analyze_complexity", "generate_sql")
        workflow.add_edge("generate_sql", "validate_sql")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "validate_sql",
            self.decide_after_validation,
            {
                "valid": "execute_sql",
                "invalid": "handle_error",
            }
        )
        
        workflow.add_edge("execute_sql", "log_to_history")
        workflow.add_edge("log_to_history", END)
        workflow.add_edge("handle_error", "log_to_history")
        
        return workflow.compile()
    
    def analyze_complexity_node(self, state: AgentState) -> AgentState:
        """Analyze the complexity of the natural language question"""
        question = state.get("question", "").lower()
        
        complexity = "simple"
        
        # Check for indicators of complex queries
        complex_indicators = [
            "join", "aggregate", "sum", "average", "count", "group by",
            "subquery", "nested", "window", "rank", "partition", "having"
        ]
        
        complex_count = sum(1 for indicator in complex_indicators if indicator in question)
        
        if complex_count >= 3:
            complexity = "complex"
        elif complex_count >= 1:
            complexity = "medium"
        
        return {"query_complexity": complexity}
    
    def generate_sql_node(self, state: AgentState) -> AgentState:
        """Generate SQL from natural language question"""
        question = state.get("question", "")
        complexity = state.get("query_complexity", "simple")
        
        # Adjust prompt based on query complexity
        complexity_instructions = {
            "simple": "Generate a simple SELECT query.",
            "medium": "Generate a SELECT query that may include basic aggregations or joins.",
            "complex": "Generate a complex SELECT query that may include multiple joins, subqueries, or window functions."
        }
        
        # Enhanced prompt with specific column mappings and examples
        prompt = f"""
        You are a SQL expert. Convert this natural language question to a PostgreSQL SELECT query only.

        Database Schema:
        - core_customer (id, name, email, registration_date)
        - core_product (id, name, category, price) 
        - core_order (id, customer_id, product_id, order_date, quantity, status)

        CRITICAL COLUMN MAPPINGS:
        - "most expensive" or "highest price" should map to the "price" column in core_product
        - "quantity" refers to order quantities in core_order
        - "cost" or "price" refers to the product price in core_product
        - "customer" refers to core_customer table
        - "order" refers to core_order table

        Natural Language Question: "{question}"

        IMPORTANT INSTRUCTIONS:
        1. Generate ONLY a valid PostgreSQL SELECT query
        2. {complexity_instructions[complexity]}
        3. Do NOT include any explanations, comments, or additional text
        4. Do NOT use markdown formatting
        5. Return only the pure SQL query
        6. Use proper SQL syntax with correct table and column names
        7. Pay close attention to what the question is actually asking for
        8. For "most expensive" questions, use the price column from core_product
        9. For quantity-related questions, use the quantity column from core_order
        10. For date-related queries, use appropriate date functions like CURRENT_DATE, INTERVAL, etc.

        EXAMPLE: For "What is the most expensive product?", generate:
        SELECT name, price FROM core_product ORDER BY price DESC LIMIT 1;

        EXAMPLE: For "How many customers registered last month?", generate:
        SELECT COUNT(*) FROM core_customer WHERE registration_date >= CURRENT_DATE - INTERVAL '1 month';

        SQL Query:
        """
        
        payload = {
            "model": "sqlcoder:7b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 4096 if complexity == "complex" else 2048,
                "num_predict": 512 if complexity == "complex" else 256
            }
        }
        
        try:
            start_time = time.time()
            response = requests.post(self.ollama_url, json=payload, timeout=120)
            response_data = response.json()
            generation_time = time.time() - start_time
            
            raw_response = response_data.get("response", "").strip()
            tokens_used = response_data.get("eval_count", 0)
            
            logger.info(f"Raw model response: {raw_response}")
            logger.info(f"Generation time: {generation_time:.2f}s, Tokens used: {tokens_used}")
            
            # Extract SQL query
            sql_query = self.extract_sql_query(raw_response)
            
            return {
                "sql_query": sql_query,
                "execution_time": generation_time,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return {"error": f"SQL Generation Error: {str(e)}"}
    
    def validate_sql_node(self, state: AgentState) -> AgentState:
        """Validate the generated SQL query"""
        sql_query = state.get("sql_query", "")
        question = state.get("question", "").lower()
        
        if not sql_query:
            return {"validation_result": "invalid", "error": "No SQL query generated"}
        
        # Convert to uppercase for validation
        upper_query = sql_query.upper()
        
        # Check if it's a SELECT statement
        if not upper_query.startswith('SELECT'):
            return {"validation_result": "invalid", "error": "Generated query is not a SELECT statement"}
        
        # Check for unauthorized operations
        dangerous_operations = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'EXEC', 'GRANT', 'REVOKE']
        if any(keyword in upper_query for keyword in dangerous_operations):
            return {"validation_result": "invalid", "error": "Generated query contains unauthorized SQL operations"}
        
        # Check for essential SQL components
        if 'FROM' not in upper_query:
            return {"validation_result": "invalid", "error": "Generated query missing FROM clause"}
        
        # Additional validation for query intent
        if "expensive" in question or "price" in question or "cost" in question:
            if "PRICE" not in upper_query:
                return {"validation_result": "invalid", "error": "Query about price but doesn't reference price column"}
        
        if "quantity" in question and "QUANTITY" not in upper_query:
            return {"validation_result": "invalid", "error": "Query about quantity but doesn't reference quantity column"}
        
        # Additional validation for complex queries
        complexity = state.get("query_complexity", "simple")
        if complexity == "complex":
            # For complex queries, check if they actually use complex features
            has_complex_features = any(
                any(pattern in upper_query for pattern in self.complex_queries[feature])
                for feature in self.complex_queries
            )
            
            if not has_complex_features:
                logger.warning("Query marked as complex but doesn't use complex features")
        
        return {"validation_result": "valid"}
    
    def execute_sql_node(self, state: AgentState) -> AgentState:
        """Execute the validated SQL query against the database"""
        sql_query = state.get("sql_query", "")
        
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                
                # Get column names
                columns = [col[0] for col in cursor.description] if cursor.description else []
                
                # Get results
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                execution_time = time.time() - start_time
                
                logger.info(f"Query executed successfully in {execution_time:.2f}s, returned {len(results)} results")
                
                return {
                    "execution_result": results,
                    "validation_result": "valid",
                    "execution_time": execution_time
                }
                
        except Exception as e:
            logger.error(f"SQL Execution Error: {str(e)}")
            return {
                "error": f"SQL Execution Error: {str(e)}",
                "validation_result": "invalid"
            }
    
    def handle_error_node(self, state: AgentState) -> AgentState:
        """Handle error state"""
        error_msg = state.get("error", "Unknown error occurred")
        return {"error": error_msg, "validation_result": "invalid"}
    
    def log_to_history_node(self, state: AgentState) -> AgentState:
        """Log the query and results to history"""
        question = state.get("question", "")
        sql_query = state.get("sql_query", "")
        execution_result = state.get("execution_result", [])
        error = state.get("error")
        execution_time = state.get("execution_time", 0)
        
        # Add to history
        self.query_history.add_entry(
            question=question,
            sql_query=sql_query,
            results=execution_result,
            execution_time=execution_time,
            error=error
        )
        
        return state
    
    def decide_after_validation(self, state: AgentState) -> Literal["valid", "invalid"]:
        """Decision function for conditional edge"""
        return state.get("validation_result", "invalid")
    
    def extract_sql_query(self, text: str) -> str:
        """Extract SQL query from model response"""
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
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s_,.*=()\'\-\+]', ' ', text).strip()
        if cleaned_text and any(word in cleaned_text.upper() for word in ['SELECT', 'FROM', 'WHERE']):
            if not cleaned_text.endswith(';'):
                cleaned_text += ';'
            return cleaned_text
        
        return text.strip()
    
    def process_question(self, question: str):
        """Process a natural language question through the workflow"""
        initial_state = AgentState(question=question)
        
        try:
            result = self.workflow.invoke(initial_state)
            
            # Add some metadata to the response
            result["history_count"] = len(self.query_history.history)
            result["query_complexity"] = initial_state.get("query_complexity", "simple")
            
            return result
        except Exception as e:
            logger.error(f"Workflow execution error: {str(e)}")
            return {"error": f"Workflow execution error: {str(e)}"}
    
    def get_query_history(self, limit=10):
        """Get query history"""
        return self.query_history.get_history(limit)
    
    def clear_query_history(self):
        """Clear query history"""
        self.query_history.clear_history()
        return {"message": "Query history cleared"}
    
    def get_query_stats(self):
        """Get statistics about queries"""
        history = self.query_history.get_history()
        
        if not history:
            return {"total_queries": 0}
        
        successful_queries = [q for q in history if not q.get("error")]
        failed_queries = [q for q in history if q.get("error")]
        
        total_execution_time = sum(q.get("execution_time", 0) for q in successful_queries)
        avg_execution_time = total_execution_time / len(successful_queries) if successful_queries else 0
        
        return {
            "total_queries": len(history),
            "successful_queries": len(successful_queries),
            "failed_queries": len(failed_queries),
            "avg_execution_time": round(avg_execution_time, 2),
            "total_execution_time": round(total_execution_time, 2)
        }