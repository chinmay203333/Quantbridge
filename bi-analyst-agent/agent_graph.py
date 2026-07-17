import os
from pathlib import Path
from dotenv import load_dotenv

# Fix: explicitly load .env relative to this file
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from openai import OpenAI

# ✅ FIX 1: Import what actually exists in your files
try:
    from mask_pii import mask_text, mask_text_with_mapping
except ImportError:
    print("⚠️ mask_pii.py not found. PII masking will be skipped.")
    mask_text = None
    mask_text_with_mapping = None

try:
    from create_chromadb import create_vector_store
    import chromadb
except ImportError:
    print("⚠️ create_chromadb.py not found. SQL hints will be skipped.")
    chromadb = None

# Initialize ChromaDB persistent client globally for performance
db_client = None
collection = None
if chromadb:
    try:
        db_client = chromadb.PersistentClient(path="./chroma_db")
        collection = db_client.get_or_create_collection(name="sql_examples")
    except Exception as e:
        print(f"⚠️ Error initializing ChromaDB globally: {e}")

# 1. Define the State
class AgentState(TypedDict):
    question: str
    masked_query: Optional[str]
    pii_map: Optional[dict]
    sql: Optional[str]
    error: Optional[str]
    results: Optional[list]
    retry_count: int

# ✅ FIX 2: load_dotenv() already called above, so HF_TOKEN is now available
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN")
)

# --- NODES ---

def masking_node(state: AgentState):
    if mask_text_with_mapping:
        masked, pii_map = mask_text_with_mapping(state["question"])
    else:
        masked = state["question"]
        pii_map = {}
    return {"masked_query": masked, "pii_map": pii_map, "retry_count": 0}

def retriever_node(state: AgentState):
    hint = "No specific template found."
    if collection:
        try:
            results = collection.query(
                query_texts=[state["masked_query"]],
                n_results=1
            )
            if results and results['metadatas'] and results['metadatas'][0]:
                hint = results['metadatas'][0][0]['sql']
        except Exception as e:
            print(f"⚠️ ChromaDB query error: {e}")
    return {"sql": hint}

def generator_node(state: AgentState):
    prompt = f"""
    You are a Senior Data Engineer. Convert the following natural language question into a valid PostgreSQL query.
    
    ### DATABASE SCHEMA:
    - fact_sales (sale_id, customer_id, product_id, sale_date, quantity, total_amount)
    - dim_customers (customer_id, first_name, last_name, email, phone)
    - dim_products (product_id, product_name, category, price, stock_quantity)
    
    ### IMPORTANT RULES:
    - dim_customers has NO customer_name column. Always use first_name || ' ' || last_name AS customer_name
    - dim_customers has NO city column. Available columns: customer_id, first_name, last_name, email, phone
    - Always qualify column names with table alias (e.g. c.first_name, not just first_name)
    - If you see placeholders like PERSON_PLACEHOLDER_0, PERSON_PLACEHOLDER_1, or EMAIL_PLACEHOLDER_0 in the question, treat them as the actual customer names or email values in your WHERE clauses. For example: WHERE c.first_name || ' ' || c.last_name = 'PERSON_PLACEHOLDER_0'. Keep the placeholder exactly as is in the generated SQL.
    
    ### TARGET QUESTION:
    {state['masked_query']}
    
    ### GUIDANCE TEMPLATE:
    {state['sql']}
    
    ### CONSTRAINTS:
    - Return ONLY the SQL code.
    - Use standard PostgreSQL syntax.
    - Wrap the SQL in a markdown code block.
    """
    
    if state.get("error"):
        prompt += f"\n\n### PREVIOUS ERROR (FIX THIS):\nYour last query failed with: {state['error']}. Check column names and joins."

    completion = client.chat.completions.create(
        model="MiniMaxAI/MiniMax-M2.5:novita",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    raw_content = completion.choices[0].message.content
    clean_sql = raw_content.replace("```sql", "").replace("```", "").strip()
    
    return {"sql": clean_sql}

def unmasking_node(state: AgentState):
    sql = state.get("sql", "")
    pii_map = state.get("pii_map", {})
    if pii_map and sql:
        for placeholder, original in pii_map.items():
            sql = sql.replace(placeholder, original)
    return {"sql": sql}

# 3. Graph Construction
workflow = StateGraph(AgentState)
workflow.add_node("masking", masking_node)
workflow.add_node("retriever", retriever_node)
workflow.add_node("generator", generator_node)
workflow.add_node("unmasking", unmasking_node)

workflow.set_entry_point("masking")
workflow.add_edge("masking", "retriever")
workflow.add_edge("retriever", "generator")
workflow.add_edge("generator", "unmasking")
workflow.add_edge("unmasking", END)

app = workflow.compile()

# --- TEST RUN ---
if __name__ == "__main__":
    # Test with a common question containing a name (PII)
    inputs = {"question": "How much did Rahul spend in total?"}
    print("Starting Agent Graph...")
    for output in app.stream(inputs):
        for node_name, result in output.items():
            print(f"\n--- Node: {node_name} ---")
            if 'masked_query' in result: print(f"Masked Query: {result['masked_query']}")
            if 'pii_map' in result: print(f"PII Map: {result['pii_map']}")
            if 'sql' in result: print(f"SQL/Hint: {result['sql']}")
