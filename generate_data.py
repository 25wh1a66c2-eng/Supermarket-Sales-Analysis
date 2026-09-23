"""
Script to generate supermarket_sales.csv with 500 realistic transactions.
Run once: python generate_data.py
"""
import csv
import random
from datetime import datetime, timedelta

random.seed(42)

branches      = ["A", "B", "C"]
cities        = {"A": "Yangon", "B": "Mandalay", "C": "Naypyitaw"}
customer_types = ["Member", "Normal"]
genders       = ["Male", "Female"]
product_lines = [
    "Health and beauty",
    "Electronic accessories",
    "Home and lifestyle",
    "Sports and travel",
    "Food and beverages",
    "Fashion accessories",
]
payment_methods = ["Ewallet", "Cash", "Credit card"]

header = [
    "Invoice ID", "Branch", "City", "Customer type", "Gender",
    "Product line", "Unit price", "Quantity", "Tax 5%", "Total",
    "Date", "Time", "Payment", "cogs", "gross margin percentage",
    "gross income", "Rating",
]

start_date = datetime(2019, 1, 1)
rows = []

for i in range(1, 501):
    branch      = random.choice(branches)
    city        = cities[branch]
    ctype       = random.choice(customer_types)
    gender      = random.choice(genders)
    product     = random.choice(product_lines)
    unit_price  = round(random.uniform(10.0, 99.99), 2)
    quantity    = random.randint(1, 10)
    cogs        = round(unit_price * quantity, 2)
    tax         = round(cogs * 0.05, 4)
    total       = round(cogs + tax, 4)
    gross_inc   = tax                       # same as tax at 5%
    gross_margin = round(4.761904762, 9)    # constant for 5% markup
    date        = (start_date + timedelta(days=random.randint(0, 89))).strftime("%m/%d/%Y")
    hour        = random.randint(10, 20)
    minute      = random.randint(0, 59)
    time_str    = f"{hour:02d}:{minute:02d}"
    payment     = random.choice(payment_methods)
    rating      = round(random.uniform(4.0, 10.0), 1)
    inv_id      = f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"

    rows.append([
        inv_id, branch, city, ctype, gender,
        product, unit_price, quantity, tax, total,
        date, time_str, payment, cogs, gross_margin,
        gross_inc, rating,
    ])

with open("supermarket_sales.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(rows)

print("supermarket_sales.csv written with", len(rows), "rows.")
