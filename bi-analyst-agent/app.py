import os
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from streamlit_autorefresh import st_autorefresh

# ── Load env ──────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="BI Analyst Agent",
    page_icon="📊",
    layout="wide"
)

# ── Auto Refresh every 60 seconds (not 10 — LLM needs time) ──
st_autorefresh(interval=60000, key="dashboard_refresh")

# ── DB Connection (cached so it doesn't reconnect every refresh) ──
@st.cache_resource
def get_engine():
    url = (
        f"postgresql+psycopg2://"
        f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
        f"/{os.getenv('DB_NAME')}"
    )
    return create_engine(url)

engine = get_engine()

def run_query(query: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

# ── Title ─────────────────────────────────────────────────
st.title("📊 BI Analyst Agent — Live Dashboard")
st.caption("Auto-refreshes every 60 seconds | Powered by LangGraph + HuggingFace")

# ══════════════════════════════════════════════════════════
# LAYOUT: Left = Dashboard | Right = AI Chat
# ══════════════════════════════════════════════════════════
dash_col, chat_col = st.columns([2, 1])

# ──────────────────────────────────────────────────────────
# LEFT: DASHBOARD
# ──────────────────────────────────────────────────────────
with dash_col:

    # ── KPI Cards ─────────────────────────────────────────
    st.subheader("📈 Key Metrics")
    k1, k2, k3, k4 = st.columns(4)

    try:
        revenue_df = run_query("SELECT total_revenue FROM vw_total_revenue")
        total_revenue = revenue_df["total_revenue"].iloc[0]
        k1.metric("💰 Total Revenue", f"₹{total_revenue:,.0f}")
    except Exception as e:
        k1.metric("💰 Total Revenue", "Error")

    try:
        orders_df = run_query("SELECT COUNT(*) AS total_orders FROM fact_sales")
        k2.metric("🛒 Total Orders", f"{orders_df['total_orders'].iloc[0]:,}")
    except:
        k2.metric("🛒 Total Orders", "Error")

    try:
        customers_df = run_query("SELECT COUNT(DISTINCT customer_id) AS customers FROM fact_sales")
        k3.metric("👥 Unique Customers", f"{customers_df['customers'].iloc[0]:,}")
    except:
        k3.metric("👥 Unique Customers", "Error")

    try:
        avg_df = run_query("SELECT AVG(total_amount) AS avg_order FROM fact_sales")
        k4.metric("🧾 Avg Order Value", f"₹{avg_df['avg_order'].iloc[0]:,.0f}")
    except:
        k4.metric("🧾 Avg Order Value", "Error")

    st.divider()

    # ── Charts Row 1 ──────────────────────────────────────
    chart1, chart2 = st.columns(2)

    with chart1:
        st.subheader("📅 Monthly Revenue Trend")
        try:
            trend_df = run_query("SELECT * FROM vw_monthly_trend")
            fig = px.line(
                trend_df, x="month", y="monthly_revenue",
                markers=True, color_discrete_sequence=["#6366f1"]
            )
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error: {e}")

    with chart2:
        st.subheader("🗂️ Revenue by Category")
        try:
            cat_df = run_query("SELECT * FROM vw_category_revenue")
            fig = px.bar(
                cat_df, x="category", y="revenue",
                color="category", color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error: {e}")

    st.divider()

    # ── Charts Row 2 ──────────────────────────────────────
    tbl1, tbl2 = st.columns(2)

    with tbl1:
        st.subheader("🏆 Top 5 Customers")
        try:
            top_cust = run_query("SELECT * FROM vw_top_customers")
            st.dataframe(top_cust, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Table error: {e}")

    with tbl2:
        st.subheader("📦 Top 5 Products")
        try:
            top_prod = run_query("SELECT * FROM vw_top_products")
            st.dataframe(top_prod, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Table error: {e}")

# ──────────────────────────────────────────────────────────
# RIGHT: AI CHAT
# ──────────────────────────────────────────────────────────
with chat_col:
    st.subheader("🤖 Ask Your Data")

    # Import your agent
    try:
        from agent_graph import app as agent_app
        agent_loaded = True
    except Exception as e:
        agent_loaded = False
        st.error(f"Agent not loaded: {e}")

    # Chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ── Guard: stop auto-refresh from clearing in-progress query ──
    if "agent_running" not in st.session_state:
        st.session_state.agent_running = False

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.code(msg["content"], language="sql")
                if "result_df" in msg:
                    st.dataframe(msg["result_df"], use_container_width=True)
            else:
                st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask anything about your data..."):

        # Save user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.agent_running = True

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if agent_loaded:
                with st.spinner("⏳ Generating SQL... (may take 15-30 sec)"):
                    try:
                        result = agent_app.invoke({"question": prompt})
                        sql = result.get("sql", "No SQL generated.")

                        st.markdown("**Generated SQL:**")
                        st.code(sql, language="sql")

                        # Execute and show results
                        try:
                            result_df = run_query(sql)
                            st.markdown("**Results:**")
                            st.dataframe(result_df, use_container_width=True)

                            # Save to history with dataframe
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": sql,
                                "result_df": result_df
                            })
                        except Exception as db_err:
                            st.warning(f"SQL execution error: {db_err}")
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": sql
                            })

                    except Exception as e:
                        st.error(f"Agent error: {e}")
                        st.info("Check your PowerShell terminal for full error details.")
            else:
                st.error("Agent not available.")

        st.session_state.agent_running = False