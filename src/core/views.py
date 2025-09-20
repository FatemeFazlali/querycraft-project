from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import json
import logging
from .langgraph_agent import QueryCraftLangGraphAgent
from django.shortcuts import render

logger = logging.getLogger(__name__)

# Create a singleton instance of the agent
agent = QueryCraftLangGraphAgent()

def query_interface(request):
    return render(request, 'core/query.html')

@csrf_exempt
def natural_language_query(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            logger.info(f"Question received: {question}")

            if not question:
                return JsonResponse({'error': 'No question provided'}, status=400)
            
            logger.info(f"Received question: {question}")
            
            # Process question with LangGraph agent
            result = agent.process_question(question)
            
            logger.info(f"Generated SQL: {result.get('sql_query', 'No SQL generated')}")
            logger.info(f"Execution results: {result.get('execution_result', 'No results')}")


            # Handle cases where error might be None
            if result.get('error'):
                return JsonResponse({
                    'error': result['error'],
                    'suggestion': 'Please try rephrasing your question or ask a different type of query.'
                }, status=400)
            
            # Additional validation to ensure it's a SELECT query
            sql_query = result.get('sql_query', '')
            if not sql_query.strip().upper().startswith('SELECT'):
                return JsonResponse({
                    'error': 'Generated query is not a SELECT statement',
                    'suggestion': 'Please try rephrasing your question to ask for data retrieval only.'
                }, status=400)
            
            return JsonResponse({
                'sql': sql_query,
                'results': result.get('execution_result', []),
                'validation': result.get('validation_result', 'unknown'),
                'execution_time': result.get('execution_time', 0),
                'tokens_used': result.get('tokens_used', 0),
                'query_complexity': result.get('query_complexity', 'simple'),
                'history_count': result.get('history_count', 0)
            })
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def query_history(request):
    if request.method == 'GET':
        limit = request.GET.get('limit', 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
            
        history = agent.get_query_history(limit)
        return JsonResponse({'history': history})
    
    elif request.method == 'DELETE':
        result = agent.clear_query_history()
        return JsonResponse(result)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def query_stats(request):
    if request.method == 'GET':
        print("before")
        stats = agent.get_query_stats()
        print("after")
        print("after")
        print("after")
        print(stats)
        return JsonResponse(stats)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def test_db_connection(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM customers")
            count = cursor.fetchone()[0]
        return JsonResponse({'status': 'success', 'customer_count': count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})