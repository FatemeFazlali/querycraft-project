from django.urls import path
from core.views import natural_language_query, test_db_connection, query_interface, query_history, query_stats

urlpatterns = [
    path('', query_interface, name='query_interface'),
    path('api/test-db/', test_db_connection, name='test_db_connection'),
    path('api/query/', natural_language_query, name='natural_language_query'),
    path('api/query/history/', query_history, name='query_history'),
    path('api/query/stats/', query_stats, name='query_stats'),
]