import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* Root theme */
:root {
    --bg: #0a0e1a;
    --surface: #111827;
    --surface2: #1a2235;
    --border: #1e2d45;
    --accent: #3b82f6;
    --accent2: #06b6d4;
    --success: #10b981;
    --warning: #f59e0b;
    --text: #e2e8f0;
    --muted: #64748b;
    --font-mono: 'Space Mono', monospace;
    --font-body: 'DM Sans', sans-serif;
}

html, body, [class*="css"] {
    font-family: var(--font-body);
    background-color: var(--bg);
    color: var(--text);
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 100%; }

/* Title bar */
.dash-title {
    font-family: var(--font-mono);
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.2rem;
}
.dash-subtitle {
    font-size: 0.75rem;
    color: var(--muted);
    font-family: var(--font-mono);
    margin-bottom: 1.5rem;
}

/* KPI Cards */
.kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: var(--accent); }
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}
.kpi-label {
    font-size: 0.7rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: var(--font-mono);
    margin-bottom: 0.4rem;
}
.kpi-value {
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--text);
    font-family: var(--font-mono);
    line-height: 1;
}
.kpi-icon {
    position: absolute;
    top: 1rem; right: 1rem;
    font-size: 1.4rem;
    opacity: 0.3;
}

/* Section headers */
.section-header {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 1.5rem 0 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* Drill-down panel */
.drilldown-panel {
    background: var(--surface2);
    border: 1px solid var(--accent);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-top: 0.8rem;
}
.drilldown-title {
    font-family: var(--font-mono);
    font-size: 0.85rem;
    color: var(--accent2);
    margin-bottom: 0.8rem;
}

/* Chat panel */
.chat-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem;
    height: 100%;
}
.chat-header {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0.8rem;
}

/* Streamlit metric overrides */
[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
}
[data-testid="metric-container"] label {
    font-family: var(--font-mono) !important;
    font-size: 0.65rem !important;
    color: var(--muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-size: 1.6rem !important;
    color: var(--text) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem !important;
}

/* Spinner */
[data-testid="stSpinner"] { color: var(--accent) !important; }

/* Plotly charts background match */
.js-plotly-plot { border-radius: 10px; overflow: hidden; }

/* Divider */
hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Plotly theme ───────────────────────────────────────────
PLOT_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Mono, monospace", color="#94a3b8", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45", tickcolor="#1e2d45"),
    yaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45", tickcolor="#1e2d45"),
    colorway=["#3b82f6", "#06b6d4", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"],
)

# ── Auto Refresh every 60 seconds ─────────────────────────
st_autorefresh(interval=60000, key="dashboard_refresh")

# ── DB Connection ──────────────────────────────────────────
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

@st.cache_data(ttl=60)
def run_query(query: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

def run_query_uncached(query: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

# ── Agent (cached per question) ────────────────────────────
@st.cache_resource
def load_agent():
    try:
        from agent_graph import app as agent_app
        return agent_app
    except Exception as e:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def run_agent_cached(question: str):
    """Cache agent results for 5 minutes — same question won't re-call LLM."""
    agent = load_agent()
    if agent is None:
        return None, "Agent not loaded"
    try:
        result = agent.invoke({"question": question})
        sql = result.get("sql", "")
        # Clean up SQL
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql, None
    except Exception as e:
        return None, str(e)

# ══════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="dash-title">◈ BI ANALYST AGENT</div>
<div class="dash-subtitle">LIVE DASHBOARD · LANGGRAPH + HUGGINGFACE · AUTO-REFRESH 60s</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════
dash_col, chat_col = st.columns([2.2, 1], gap="medium")

# ══════════════════════════════════════════════════════════
# LEFT: DASHBOARD
# ══════════════════════════════════════════════════════════
with dash_col:

    # ── KPI Row ───────────────────────────────────────────
    st.markdown('<div class="section-header">◆ KEY METRICS</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)

    try:
        rev = run_query("SELECT total_revenue FROM vw_total_revenue")
        k1.metric("💰 Total Revenue", f"₹{rev['total_revenue'].iloc[0]:,.0f}")
    except: k1.metric("💰 Total Revenue", "—")

    try:
        ord_ = run_query("SELECT COUNT(*) AS n FROM fact_sales")
        k2.metric("🛒 Total Orders", f"{ord_['n'].iloc[0]:,}")
    except: k2.metric("🛒 Total Orders", "—")

    try:
        cust = run_query("SELECT COUNT(DISTINCT customer_id) AS n FROM fact_sales")
        k3.metric("👥 Customers", f"{cust['n'].iloc[0]:,}")
    except: k3.metric("👥 Customers", "—")

    try:
        avg_ = run_query("SELECT ROUND(AVG(total_amount)::numeric, 0) AS n FROM fact_sales")
        k4.metric("🧾 Avg Order", f"₹{avg_['n'].iloc[0]:,.0f}")
    except: k4.metric("🧾 Avg Order", "—")

    st.divider()

    # ══════════════════════════════════════════════════════
    # DRILL-DOWN 1: Category → Products
    # ══════════════════════════════════════════════════════
    st.markdown('<div class="section-header">◆ REVENUE BY CATEGORY <span style="color:#64748b;font-size:0.65rem">— CLICK BAR TO DRILL DOWN</span></div>', unsafe_allow_html=True)

    try:
        cat_df = run_query("SELECT * FROM vw_category_revenue")

        fig1 = go.Figure(go.Bar(
            x=cat_df["category"],
            y=cat_df["revenue"],
            marker=dict(
                color=cat_df["revenue"],
                colorscale=[[0, "#1e3a5f"], [0.5, "#3b82f6"], [1, "#06b6d4"]],
                line=dict(width=0)
            ),
            hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.0f}<extra></extra>"
        ))
        fig1.update_layout(**PLOT_THEME, height=280,
                           bargap=0.3, clickmode="event+select")

        sel1 = st.plotly_chart(fig1, use_container_width=True,
                               on_select="rerun", key="cat_chart")

        clicked_cat = None
        if sel1 and sel1.get("selection", {}).get("points"):
            clicked_cat = sel1["selection"]["points"][0]["x"]

        if clicked_cat:
            st.markdown(f'<div class="drilldown-panel"><div class="drilldown-title">⬇ DRILL-DOWN · {clicked_cat.upper()}</div>', unsafe_allow_html=True)
            drill = run_query(f"""
                SELECT product_name, units_sold, revenue, orders,
                       ROUND(avg_order_value::numeric, 0) AS avg_order_value
                FROM vw_category_product_drilldown
                WHERE category = '{clicked_cat}'
                ORDER BY revenue DESC
            """)

            d1, d2, d3 = st.columns(3)
            d1.metric("Revenue", f"₹{drill['revenue'].sum():,.0f}")
            d2.metric("Products", str(len(drill)))
            d3.metric("Orders", f"{drill['orders'].sum():,}")

            fig_d = go.Figure(go.Bar(
                x=drill["product_name"], y=drill["revenue"],
                marker=dict(color="#06b6d4", line=dict(width=0)),
                hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>"
            ))
            fig_d.update_layout(**PLOT_THEME, height=220,
                                xaxis_tickangle=-25, bargap=0.3)
            st.plotly_chart(fig_d, use_container_width=True)
            st.dataframe(drill, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Category chart error: {e}")

    st.divider()

    # ══════════════════════════════════════════════════════
    # DRILL-DOWN 2: Monthly Trend → Daily Breakdown
    # ══════════════════════════════════════════════════════
    st.markdown('<div class="section-header">◆ MONTHLY REVENUE TREND <span style="color:#64748b;font-size:0.65rem">— CLICK POINT TO SEE DAILY</span></div>', unsafe_allow_html=True)

    try:
        trend_df = run_query("SELECT * FROM vw_monthly_trend ORDER BY month")

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=trend_df["month"], y=trend_df["monthly_revenue"],
            mode="lines+markers",
            line=dict(color="#3b82f6", width=2.5),
            marker=dict(size=7, color="#06b6d4",
                       line=dict(color="#0a0e1a", width=2)),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.07)",
            hovertemplate="<b>%{x}</b><br>Revenue: ₹%{y:,.0f}<extra></extra>"
        ))
        fig2.update_layout(**PLOT_THEME, height=280, clickmode="event+select")

        sel2 = st.plotly_chart(fig2, use_container_width=True,
                               on_select="rerun", key="month_chart")

        clicked_month = None
        if sel2 and sel2.get("selection", {}).get("points"):
            clicked_month = sel2["selection"]["points"][0]["x"]

        if clicked_month:
            st.markdown(f'<div class="drilldown-panel"><div class="drilldown-title">⬇ DAILY BREAKDOWN · {clicked_month}</div>', unsafe_allow_html=True)
            daily = run_query(f"""
                SELECT sale_day, daily_revenue, orders
                FROM vw_monthly_daily_drilldown
                WHERE month = '{clicked_month}'
                ORDER BY sale_day
            """)

            d1, d2 = st.columns(2)
            d1.metric("Month Revenue", f"₹{daily['daily_revenue'].sum():,.0f}")
            d2.metric("Month Orders", f"{daily['orders'].sum():,}")

            fig_d2 = go.Figure(go.Bar(
                x=daily["sale_day"].astype(str), y=daily["daily_revenue"],
                marker=dict(color="#10b981", line=dict(width=0)),
                hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>"
            ))
            fig_d2.update_layout(**PLOT_THEME, height=220, bargap=0.2)
            st.plotly_chart(fig_d2, use_container_width=True)
            st.dataframe(daily, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Monthly chart error: {e}")

    st.divider()

    # ══════════════════════════════════════════════════════
    # DRILL-DOWN 3: Top Customers → Their Orders
    # ══════════════════════════════════════════════════════
    st.markdown('<div class="section-header">◆ TOP CUSTOMERS <span style="color:#64748b;font-size:0.65rem">— CLICK BAR TO SEE ORDERS</span></div>', unsafe_allow_html=True)

    try:
        top_cust = run_query("SELECT * FROM vw_top_customers ORDER BY total_spent DESC")

        fig3 = go.Figure(go.Bar(
            x=top_cust["customer_name"], y=top_cust["total_spent"],
            marker=dict(
                color=top_cust["total_spent"],
                colorscale=[[0, "#064e3b"], [0.5, "#10b981"], [1, "#34d399"]],
                line=dict(width=0)
            ),
            hovertemplate="<b>%{x}</b><br>Spent: ₹%{y:,.0f}<extra></extra>"
        ))
        fig3.update_layout(**PLOT_THEME, height=280,
                           bargap=0.3, clickmode="event+select")

        sel3 = st.plotly_chart(fig3, use_container_width=True,
                               on_select="rerun", key="cust_chart")

        clicked_cust = None
        if sel3 and sel3.get("selection", {}).get("points"):
            clicked_cust = sel3["selection"]["points"][0]["x"]

        if clicked_cust:
            st.markdown(f'<div class="drilldown-panel"><div class="drilldown-title">⬇ ORDERS BY · {clicked_cust.upper()}</div>', unsafe_allow_html=True)
            orders = run_query(f"""
                SELECT product_name, category, sale_date, quantity, total_amount
                FROM vw_customer_orders_drilldown
                WHERE customer_name = '{clicked_cust}'
                ORDER BY sale_date DESC
            """)

            d1, d2, d3 = st.columns(3)
            d1.metric("Total Spent", f"₹{orders['total_amount'].sum():,.0f}")
            d2.metric("Orders", str(len(orders)))
            d3.metric("Avg Order", f"₹{orders['total_amount'].mean():,.0f}")

            st.dataframe(orders, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Customer chart error: {e}")

    st.divider()

    # ── Top Products ───────────────────────────────────────
    st.markdown('<div class="section-header">◆ TOP 5 PRODUCTS</div>', unsafe_allow_html=True)
    try:
        top_prod = run_query("SELECT product_name, category, units_sold, revenue FROM vw_top_products")

        fig4 = go.Figure(go.Bar(
            x=top_prod["revenue"], y=top_prod["product_name"],
            orientation="h",
            marker=dict(
                color=top_prod["revenue"],
                colorscale=[[0, "#3b0764"], [0.5, "#7c3aed"], [1, "#a78bfa"]],
                line=dict(width=0)
            ),
            hovertemplate="<b>%{y}</b><br>Revenue: ₹%{x:,.0f}<extra></extra>"
        ))
        fig4.update_layout(**PLOT_THEME, height=250, bargap=0.3)
        st.plotly_chart(fig4, use_container_width=True)

    except Exception as e:
        st.error(f"Products error: {e}")


# ══════════════════════════════════════════════════════════
# RIGHT: AI CHAT
# ══════════════════════════════════════════════════════════
with chat_col:
    st.markdown('<div class="section-header">◆ ASK YOUR DATA</div>', unsafe_allow_html=True)

    # Load agent
    agent = load_agent()
    if agent is None:
        st.error("⚠️ Agent not loaded. Check agent_graph.py")

    # Session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Suggested questions
    if len(st.session_state.messages) == 0:
        st.markdown('<div style="font-size:0.7rem;color:#64748b;font-family:Space Mono;margin-bottom:0.5rem">TRY ASKING:</div>', unsafe_allow_html=True)
        suggestions = [
            "Who spent the most money?",
            "Top 3 products by revenue?",
            "Monthly sales trend?",
            "Total orders this month?"
        ]
        for s in suggestions:
            if st.button(s, use_container_width=True, key=f"sug_{s}"):
                st.session_state.pending_question = s
                st.rerun()

    # Handle suggestion click
    if "pending_question" in st.session_state:
        prompt = st.session_state.pop("pending_question")
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("⏳ Generating SQL..."):
            sql, err = run_agent_cached(prompt)
            if err:
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {err}", "sql": None, "df": None})
            else:
                try:
                    df = run_query_uncached(sql)
                    st.session_state.messages.append({"role": "assistant", "content": sql, "sql": sql, "df": df})
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": sql, "sql": sql, "df": None, "db_err": str(e)})
        st.rerun()

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(f"**{msg['content']}**")
            else:
                if msg.get("sql"):
                    st.code(msg["sql"], language="sql")
                if msg.get("df") is not None:
                    if not msg["df"].empty:
                        st.dataframe(msg["df"], use_container_width=True, hide_index=True)
                        # Mini chart if numeric result
                        df = msg["df"]
                        num_cols = df.select_dtypes(include="number").columns.tolist()
                        str_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
                        if len(num_cols) >= 1 and len(str_cols) >= 1 and len(df) > 1:
                            fig_chat = go.Figure(go.Bar(
                                x=df[str_cols[0]], y=df[num_cols[0]],
                                marker=dict(color="#3b82f6", line=dict(width=0))
                            ))
                            fig_chat.update_layout(**PLOT_THEME, height=180, bargap=0.3)
                            st.plotly_chart(fig_chat, use_container_width=True)
                    else:
                        st.info("✅ Query executed successfully but returned no results.")
                elif msg.get("sql") and msg.get("df") is None and not msg.get("db_err"):
                    st.warning("⚠️ Query was generated but could not be executed.")
                if msg.get("db_err"):
                    st.error(f"❌ Database error: {msg['db_err']}")
                if not msg.get("sql") and msg.get("df") is None:
                    st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask anything about your data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("⏳ Generating SQL... (15-30s first time, cached after)"):
            sql, err = run_agent_cached(prompt)

            if err:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Agent error: {err}",
                    "sql": None, "df": None
                })
            else:
                try:
                    df = run_query_uncached(sql)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": sql,
                        "sql": sql,
                        "df": df
                    })
                except Exception as db_err:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": sql,
                        "sql": sql,
                        "df": None,
                        "db_err": str(db_err)
                    })

        st.rerun()

    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.cache_data.clear()
            st.rerun()