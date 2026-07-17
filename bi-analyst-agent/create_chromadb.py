import chromadb

def create_vector_store():
    print("Initializing ChromaDB...")
    # Initialize ChromaDB client. We'll use a persistent client to store data locally in a ./chroma_db folder.
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Create or get the collection for our SQL examples
    collection = client.get_or_create_collection(name="sql_examples")
    
    # 10 High-Quality Question-SQL Pairs based on the provided schema
    # The 'documents' will be vectorized and searched against.
    documents = [
        "What is the total revenue generated across all sales?",
        "What are the top 5 selling products by total quantity sold?",
        "List all customers who have purchased products in the 'Electronics' category.",
        "What was our total sales amount in August 2025?",
        "What is the average order value (total_amount) per sale?",
        "How many unique customers have made at least one purchase?",
        "Who are our top 3 customers based on total spending?",
        "Show me the total revenue grouped by product category.",
        "What is the month-over-month sales trend?",
        "Give me the details of the most recent sale."
    ]
    
    # The 'metadatas' hold the corresponding SQL query for the question.
    # This metadata will be returned when a semantic search matches the question.
    metadatas = [
        # 1. Total revenue
        {"sql": "SELECT SUM(total_amount) FROM fact_sales;"},
        
        # 2. Top 5 products by quantity
        {"sql": "SELECT p.product_name, SUM(s.quantity) as total_qty FROM fact_sales s JOIN dim_products p ON s.product_id = p.product_id GROUP BY p.product_name ORDER BY total_qty DESC LIMIT 5;"},
        
        # 3. Customers who bought electronics
        {"sql": "SELECT DISTINCT c.first_name, c.last_name, c.email FROM dim_customers c JOIN fact_sales s ON c.customer_id = s.customer_id JOIN dim_products p ON s.product_id = p.product_id WHERE p.category = 'Electronics';"},
        
        # 4. Total sales for August 2025
        {"sql": "SELECT SUM(total_amount) FROM fact_sales WHERE sale_date >= '2025-08-01' AND sale_date < '2025-09-01';"},
        
        # 5. Average order value
        {"sql": "SELECT AVG(total_amount) FROM fact_sales;"},
        
        # 6. Unique purchasing customers
        {"sql": "SELECT COUNT(DISTINCT customer_id) FROM fact_sales;"},
        
        # 7. Top 3 customers by spend
        {"sql": "SELECT c.first_name, c.last_name, SUM(s.total_amount) as total_spent FROM dim_customers c JOIN fact_sales s ON c.customer_id = s.customer_id GROUP BY c.customer_id, c.first_name, c.last_name ORDER BY total_spent DESC LIMIT 3;"},
        
        # 8. Revenue by category
        {"sql": "SELECT p.category, SUM(s.total_amount) as revenue FROM fact_sales s JOIN dim_products p ON s.product_id = p.product_id GROUP BY p.category ORDER BY revenue DESC;"},
        
        # 9. Monthly sales trend
        {"sql": "SELECT TO_CHAR(sale_date, 'YYYY-MM') as month, SUM(total_amount) as monthly_revenue FROM fact_sales GROUP BY TO_CHAR(sale_date, 'YYYY-MM') ORDER BY month;"},
        
        # 10. Most recent sale details
        {"sql": "SELECT s.sale_id, c.first_name, c.last_name, p.product_name, s.quantity, s.total_amount, s.sale_date FROM fact_sales s JOIN dim_customers c ON s.customer_id = c.customer_id JOIN dim_products p ON s.product_id = p.product_id ORDER BY s.sale_date DESC LIMIT 1;"}
    ]
    
    ids = [f"query_{i}" for i in range(1, 11)]
    
    # Add pairs to the vector store (this will automatically embed the documents using the default embedding function)
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print("Successfully added 10 question-SQL pairs to the ChromaDB vector store!")
    print(f"Total pairs in 'sql_examples' collection: {collection.count()}")
    
    # Demonstrate a quick semantic search
    print("\n--- Testing Vector Search ---")
    query = "Who spent the most money?"
    print(f"Query: '{query}'")
    
    results = collection.query(
        query_texts=[query],
        n_results=1
    )
    
    print("\nTop Matching Question:", results['documents'][0][0])
    print("Corresponding SQL:", results['metadatas'][0][0]['sql'])

if __name__ == "__main__":
    create_vector_store()
