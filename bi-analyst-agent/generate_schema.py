import random
import datetime

# Seed data for realism
first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
               "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
               "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
               "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
               "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
               "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Melissa", "George", "Deborah"]

last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", 
              "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", 
              "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", 
              "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", 
              "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
              "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell"]

domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "company.net", "corporate.org", "enterprise.com"]

products = [
    ("Laptop Pro 15", "Electronics", 1299.99),
    ("Wireless Gaming Mouse", "Electronics", 59.99),
    ("Mechanical Keyboard", "Electronics", 109.99),
    ("27-inch 4K Monitor", "Electronics", 349.99),
    ("Ergonomic Desk Chair", "Furniture", 249.99),
    ("Standing Desk", "Furniture", 599.99),
    ("Coffee Mug", "Accessories", 14.99),
    ("Noise-cancelling Headphones", "Electronics", 199.99),
    ("USB-C Hub", "Accessories", 49.99),
    ("Leather Notebook", "Office", 19.99),
    ("Webcam 1080p", "Electronics", 69.99),
    ("Desk Lamp", "Furniture", 39.99),
    ("Tablet Air", "Electronics", 499.99),
    ("Smartphone Stand", "Accessories", 12.99),
    ("External HDD 2TB", "Electronics", 89.99)
]

# Generate customers
customers = []
used_emails = set()
for i in range(1, 501):
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    
    # Generate a realistic email
    email_variant = random.randint(1, 4)
    if email_variant == 1:
        base_email = f"{fname.lower()}.{lname.lower()}"
    elif email_variant == 2:
        base_email = f"{fname.lower()[0]}{lname.lower()}"
    elif email_variant == 3:
        base_email = f"{fname.lower()}{random.randint(10,99)}"
    else:
        base_email = f"{lname.lower()}_{fname.lower()}"
        
    email = f"{base_email}@{random.choice(domains)}"
    
    # Deduplicate emails
    while email in used_emails:
        email = f"{base_email}{random.randint(100,999)}@{random.choice(domains)}"
    used_emails.add(email)
    
    phone = f"{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
    customers.append((i, fname, lname, email, phone))

# Generate sales
sales = []
start_date = datetime.datetime.now() - datetime.timedelta(days=365)
for i in range(1, 501):  # 500 transactions for fact_sales
    customer_id = random.randint(1, 500)
    product_idx = random.randint(0, len(products) - 1)
    product_id = product_idx + 1
    qty = random.randint(1, 5)
    price = products[product_idx][2]
    total = round(qty * price, 2)
    
    sale_date = start_date + datetime.timedelta(days=random.randint(0, 365), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    sale_date_str = sale_date.strftime("%Y-%m-%d %H:%M:%S")
    
    sales.append((i, customer_id, product_id, qty, total, sale_date_str))


# Write to SQL file
with open("schema.sql", "w", encoding="utf-8") as f:
    f.write("-- ============================================\n")
    f.write("-- DDL: Schema Definitions\n")
    f.write("-- ============================================\n\n")
    
    f.write("DROP TABLE IF EXISTS fact_sales;\n")
    f.write("DROP TABLE IF EXISTS dim_products;\n")
    f.write("DROP TABLE IF EXISTS dim_customers;\n\n")
    
    f.write("""CREATE TABLE dim_customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20)
);

CREATE TABLE dim_products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2) NOT NULL
);

CREATE TABLE fact_sales (
    sale_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES dim_customers(customer_id),
    product_id INT REFERENCES dim_products(product_id),
    quantity INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    sale_date TIMESTAMP NOT NULL
);

CREATE INDEX idx_fact_sales_customer_id ON fact_sales(customer_id);
CREATE INDEX idx_fact_sales_product_id ON fact_sales(product_id);
CREATE INDEX idx_fact_sales_sale_date ON fact_sales(sale_date);

""")

    f.write("-- ============================================\n")
    f.write("-- DML: Insert Seeds\n")
    f.write("-- ============================================\n\n")
    
    f.write("-- Inserting Products\n")
    for i, p in enumerate(products, 1):
        f.write(f"INSERT INTO dim_products (product_id, product_name, category, price) VALUES ({i}, '{p[0]}', '{p[1]}', {p[2]});\n")
    
    f.write("\n-- Inserting Customers (500 rows with PII)\n")
    for c in customers:
        f.write(f"INSERT INTO dim_customers (customer_id, first_name, last_name, email, phone) VALUES ({c[0]}, '{c[1]}', '{c[2]}', '{c[3]}', '{c[4]}');\n")
        
    f.write("\n-- Inserting Sales (500 rows)\n")
    for s in sales:
        f.write(f"INSERT INTO fact_sales (sale_id, customer_id, product_id, quantity, total_amount, sale_date) VALUES ({s[0]}, {s[1]}, {s[2]}, {s[3]}, {s[4]}, '{s[5]}');\n")

    f.write("\n-- Auto-increment sequence updates\n")
    f.write("SELECT setval('dim_customers_customer_id_seq', (SELECT MAX(customer_id) FROM dim_customers));\n")
    f.write("SELECT setval('dim_products_product_id_seq', (SELECT MAX(product_id) FROM dim_products));\n")
    f.write("SELECT setval('fact_sales_sale_id_seq', (SELECT MAX(sale_id) FROM fact_sales));\n\n")

    f.write("-- ============================================\n")
    f.write("-- Views for Streamlit Dashboard\n")
    f.write("-- ============================================\n\n")
    
    f.write("CREATE OR REPLACE VIEW vw_total_revenue AS\n")
    f.write("SELECT COALESCE(SUM(total_amount), 0) AS total_revenue FROM fact_sales;\n\n")
    
    f.write("CREATE OR REPLACE VIEW vw_category_revenue AS\n")
    f.write("SELECT p.category, COALESCE(SUM(s.total_amount), 0) AS revenue\n")
    f.write("FROM dim_products p\n")
    f.write("LEFT JOIN fact_sales s ON p.product_id = s.product_id\n")
    f.write("GROUP BY p.category;\n\n")
    
    f.write("CREATE OR REPLACE VIEW vw_category_product_drilldown AS\n")
    f.write("SELECT \n")
    f.write("    p.category, \n")
    f.write("    p.product_name, \n")
    f.write("    COALESCE(SUM(s.quantity), 0) AS units_sold, \n")
    f.write("    COALESCE(SUM(s.total_amount), 0) AS revenue,\n")
    f.write("    COUNT(s.sale_id) AS orders,\n")
    f.write("    CASE WHEN COUNT(s.sale_id) > 0 THEN SUM(s.total_amount) / COUNT(s.sale_id) ELSE 0 END AS avg_order_value\n")
    f.write("FROM dim_products p\n")
    f.write("LEFT JOIN fact_sales s ON p.product_id = s.product_id\n")
    f.write("GROUP BY p.category, p.product_name;\n\n")
    
    f.write("CREATE OR REPLACE VIEW vw_monthly_trend AS\n")
    f.write("SELECT TO_CHAR(sale_date, 'YYYY-MM') AS month, SUM(total_amount) AS monthly_revenue\n")
    f.write("FROM fact_sales\n")
    f.write("GROUP BY TO_CHAR(sale_date, 'YYYY-MM');\n\n")
    
    f.write("CREATE OR REPLACE VIEW vw_monthly_daily_drilldown AS\n")
    f.write("SELECT \n")
    f.write("    TO_CHAR(sale_date, 'YYYY-MM') AS month,\n")
    f.write("    CAST(sale_date AS DATE) AS sale_day,\n")
    f.write("    SUM(total_amount) AS daily_revenue,\n\n")
    f.write("    COUNT(sale_id) AS orders\n")
    f.write("FROM fact_sales\n")
    f.write("GROUP BY TO_CHAR(sale_date, 'YYYY-MM'), CAST(sale_date AS DATE);\n\n")
    
    f.write("CREATE OR REPLACE VIEW vw_top_customers AS\n")
    f.write("SELECT c.first_name || ' ' || c.last_name AS customer_name, SUM(s.total_amount) AS total_spent\n")
    f.write("FROM dim_customers c\n")
    f.write("JOIN fact_sales s ON c.customer_id = s.customer_id\n")
    f.write("GROUP BY c.customer_id, c.first_name, c.last_name\n")
    f.write("ORDER BY total_spent DESC\n")
    f.write("LIMIT 5;\n\n")
    
    f.write("CREATE OR REPLACE VIEW vw_customer_orders_drilldown AS\n")
    f.write("SELECT \n")
    f.write("    c.first_name || ' ' || c.last_name AS customer_name,\n")
    f.write("    p.product_name,\n")
    f.write("    p.category,\n")
    f.write("    s.sale_date,\n")
    f.write("    s.quantity,\n")
    f.write("    s.total_amount\n")
    f.write("FROM fact_sales s\n")
    f.write("JOIN dim_customers c ON s.customer_id = c.customer_id\n")
    f.write("JOIN dim_products p ON s.product_id = p.product_id;\n\n")
    
    f.write("CREATE OR REPLACE VIEW vw_top_products AS\n")
    f.write("SELECT p.product_name, p.category, SUM(s.quantity) AS units_sold, SUM(s.total_amount) AS revenue\n")
    f.write("FROM dim_products p\n")
    f.write("JOIN fact_sales s ON p.product_id = s.product_id\n")
    f.write("GROUP BY p.product_id, p.product_name, p.category\n")
    f.write("ORDER BY revenue DESC\n")
    f.write("LIMIT 5;\n")
    
print("Successfully generated schema.sql with 500 rows of customer and sales data and all needed views.")
