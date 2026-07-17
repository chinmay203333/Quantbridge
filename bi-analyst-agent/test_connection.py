import os
import psycopg2
from dotenv import load_dotenv

# 1. Load the variables from the .env file
load_dotenv()

def connect_db():
    try:
        # 2. Get the credentials using os.getenv
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
        )
        print("✅ Connection Successful! The BI Agent can now talk to the database.")
        
        # 3. Test a quick query
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM fact_sales;")  
        count = cursor.fetchone()[0]
        print(f"📊 Verified: Found {count} rows in the fact_sales table.")
        
        cursor.close()
        connection.close()
        
    except Exception as error:
        print(f"❌ Error connecting to the database: {error}")

if __name__ == "__main__":
    connect_db()