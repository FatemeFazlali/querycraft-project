import os
import django

# Point Django to your settings file
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "querycraft.settings")

# Setup Django
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM core_customer")
    result = cursor.fetchone()
    print("Customers count:", result[0])
