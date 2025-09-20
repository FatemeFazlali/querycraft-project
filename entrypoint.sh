#!/bin/sh

# Wait for database
python /app/wait_for_db.py

# Change to src directory and run Django commands
cd /app/src
python manage.py migrate
python manage.py seed_db
python manage.py runserver 0.0.0.0:8000