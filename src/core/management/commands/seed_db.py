from django.core.management.base import BaseCommand
from faker import Faker
import random
from core.models import Customer, Product, Order
from datetime import datetime, timedelta

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds the database with fake data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')
        self.create_customers(100)
        self.create_products(50)
        self.create_orders(1000)
        self.stdout.write('Seeding completed!')

    def create_customers(self, count):
        for _ in range(count):
            Customer.objects.create(
                name=fake.name(),
                email=fake.email(),
                registration_date=fake.date_this_decade()
            )

    def create_products(self, count):
        categories = ['Electronics', 'Books', 'Clothing', 'Home', 'Food']
        for _ in range(count):
            Product.objects.create(
                name=fake.word(),
                category=random.choice(categories),
                price=random.uniform(10, 1000)
            )

    def create_orders(self, count):
        customers = list(Customer.objects.all())
        products = list(Product.objects.all())
        statuses = ['pending', 'completed', 'cancelled']
        for _ in range(count):
            Order.objects.create(
                customer=random.choice(customers),
                product=random.choice(products),
                order_date=fake.date_this_year(),
                quantity=random.randint(1, 10),
                status=random.choice(statuses)
            )