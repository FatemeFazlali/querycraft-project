QueryCraft - Natural Language to SQL Query System

Overview
QueryCraft is a web application that allows non-technical users to query databases using natural language (English or Persian). It uses AI to convert questions into SQL queries, executes them against a PostgreSQL database, and returns the results through a simple web interface.

Architecture
Backend Framework: Django with Django REST Framework

AI Agent: LangGraph workflow with conditional logic for SQL generation and validation

Language Model: Ollama with sqlcoder:7b model for SQL generation

Database: PostgreSQL with three main tables (customers, products, orders)

Frontend: Simple HTML/JavaScript interface

Containerization: Docker with Docker Compose for easy deployment

How to Run
Prerequisites
Docker and Docker Compose installed on your system

Installation Steps
Clone the repository:

bash
git clone <https://github.com/FatemeFazlali/querycraft-project>
cd querycraft-project
Start the application with Docker Compose:

bash
docker-compose up
The application will automatically:

Wait for the database to be ready

Apply database migrations

Seed the database with sample data

Start the Django development server

Initialize the Ollama service with the sqlcoder:7b model

Access the application at http://localhost:8000

Technical Decisions
Framework Selection: Django was chosen for its robustness, ORM capabilities, and built-in admin interface

AI Integration: Used Ollama with the sqlcoder:7b model specifically trained for SQL generation tasks

Workflow Management: Implemented LangGraph for managing the complex workflow of SQL generation, validation, and execution

Database Design: Used PostgreSQL for its reliability and support for complex queries

Containerization: Dockerized the entire application for easy deployment and consistency across environments

Validation System: Implemented multiple validation layers to ensure generated SQL queries are safe and appropriate

API Usage
The application provides a REST API endpoint at /api/query/ that accepts POST requests with JSON payloads:

bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the most expensive product?"}'
The response includes the generated SQL query, execution results, and metadata:

json
{
  "sql": "SELECT name, price FROM core_product ORDER BY price DESC LIMIT 1;",
  "results": [{"name": "collection", "price": "986.77"}],
  "execution_time": 0.08,
  "query_complexity": "simple"
}
Ideas for Improvement
Additional Database Support: Extend support to other database systems like MySQL or SQLite

Query Caching: Implement caching of frequently used queries to improve performance

Advanced Security: Add more robust security measures for SQL injection prevention

User Authentication: Implement user accounts and query history persistence

Additional LLM Models: Support for multiple LLM models beyond sqlcoder

Query Explanation: Add feature to explain how the natural language was converted to SQL

Multi-language Support: Expand support for more natural languages beyond English and Persian

Advanced Frontend: Develop a more sophisticated React/Vue-based frontend

API Rate Limiting: Implement rate limiting for production deployment

Monitoring: Add performance monitoring and logging capabilities

Assumptions and Changes
Used sqlcoder:7b model instead of the specified model in the requirements as it was more readily available

Enhanced the prompt engineering to include specific column mappings for better accuracy

Added additional validation to ensure SQL queries match the intent of the natural language question

Used Django's ORM instead of raw SQL for database operations where possible

Implemented in-memory query history instead of database persistence for simplicity

Support
For questions or issues with QueryCraft, please open an issue in the GitHub repository or contact the development team.
