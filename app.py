"""
Supermarket Sales Analysis Dashboard
=====================================
Run:  streamlit run app.py
Deps: pip install streamlit pandas plotly statsmodels openpyxl
"""

# ── AUTO-INSTALL MISSING PACKAGES ────────────────────────────────────────────
import subprocess, sys

_REQUIRED = ["streamlit", "pandas", "plotly", "statsmodels", "openpyxl"]
for _pkg in _REQUIRED:
    try:
        __import__(_pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", _pkg])
# ─────────────────────────────────────────────────────────────────────────────

import os
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Supermarket Sales Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Main background */
    .stApp { background-color: #f4f6fb; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(160deg, #1a237e 0%, #283593 60%, #3949ab 100%);
    }
    section[data-testid="stSidebar"] * { color: #e8eaf6 !important; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label { color: #b3bcf5 !important; }

    /* KPI cards */
    .kpi-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 22px 28px;
        box-shadow: 0 2px 12px rgba(26,35,126,0.08);
        text-align: center;
        border-left: 5px solid #3949ab;
    }
    .kpi-card .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1a237e;
        margin: 0;
    }
    .kpi-card .kpi-label {
        font-size: 0.85rem;
        color: #5c6bc0;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Section headers */
    .section-header {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1a237e;
        border-bottom: 2px solid #3949ab;
        padding-bottom: 6px;
        margin-bottom: 16px;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #9e9e9e;
        font-size: 0.78rem;
        margin-top: 40px;
        padding-top: 12px;
        border-top: 1px solid #e0e0e0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── DATA LOADING ──────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "supermarket_sales.csv")


@st.cache_data(show_spinner="Loading dataset…")
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # ── Cleaning ──
    df.columns = df.columns.str.strip()
    df.dropna(how="all", inplace=True)
    # Parse date & time
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M", errors="coerce").dt.time
    # Numeric coercions
    for col in ["Unit price", "Quantity", "Rating", "Total", "Tax 5%", "cogs", "gross income"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Recalculate Sales (step 3 of analysis)
    df["Sales"] = df["Quantity"] * df["Unit price"]
    df["Month"] = df["Date"].dt.strftime("%b %Y")
    df["Hour"] = df["Date"].apply(lambda d: None) if "Time" not in df.columns else df.apply(
        lambda r: r["Time"].hour if r["Time"] is not None else None, axis=1
    )
    return df


# ── UPLOAD OR DEFAULT ─────────────────────────────────────────────────────────
def get_dataframe() -> pd.DataFrame:
    uploaded = st.sidebar.file_uploader(
        "📂 Upload CSV (optional)", type=["csv"],
        help="Upload your own supermarket CSV or leave blank to use the bundled dataset.",
    )
    if uploaded is not None:
        raw = pd.read_csv(uploaded)
        raw.to_csv(DATA_PATH, index=False)
        st.sidebar.success("✅ File uploaded — using your data.")
    if not os.path.exists(DATA_PATH):
        st.error(
            "⚠️ **supermarket_sales.csv not found.**\n\n"
            "Run `python generate_data.py` to create sample data, or upload a CSV above."
        )
        st.stop()
    return load_data(DATA_PATH)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Filters
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("## 🛒 Sales Dashboard")
st.sidebar.markdown("---")

df_raw = get_dataframe()

# Date range
min_d, max_d = df_raw["Date"].min(), df_raw["Date"].max()
date_range = st.sidebar.date_input(
    "📅 Date range",
    value=(min_d.date(), max_d.date()),
    min_value=min_d.date(),
    max_value=max_d.date(),
)

# Multi-select filters
branches_all = sorted(df_raw["Branch"].dropna().unique())
cities_all   = sorted(df_raw["City"].dropna().unique())
lines_all    = sorted(df_raw["Product line"].dropna().unique())
pay_all      = sorted(df_raw["Payment"].dropna().unique())

sel_branch  = st.sidebar.multiselect("🏪 Branch",         branches_all, default=branches_all)
sel_city    = st.sidebar.multiselect("🏙️ City",           cities_all,   default=cities_all)
sel_line    = st.sidebar.multiselect("📦 Product Line",   lines_all,    default=lines_all)
sel_pay     = st.sidebar.multiselect("💳 Payment Method", pay_all,      default=pay_all)
sel_ctype   = st.sidebar.multiselect(
    "👥 Customer Type",
    sorted(df_raw["Customer type"].dropna().unique()),
    default=sorted(df_raw["Customer type"].dropna().unique()),
)

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_raw.copy()
if len(date_range) == 2:
    d0 = pd.Timestamp(date_range[0])
    d1 = pd.Timestamp(date_range[1])
    df = df[(df["Date"] >= d0) & (df["Date"] <= d1)]

df = df[
    df["Branch"].isin(sel_branch) &
    df["City"].isin(sel_city) &
    df["Product line"].isin(sel_line) &
    df["Payment"].isin(sel_pay) &
    df["Customer type"].isin(sel_ctype)
]

if df.empty:
    st.warning("⚠️ No data matches the current filters. Adjust the sidebar selections.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h1 style='color:#1a237e;margin-bottom:4px;'>🛒 Supermarket Sales Analysis</h1>"
    "<p style='color:#5c6bc0;margin-top:0;'>Interactive dashboard — explore trends, branches, products, and customer behavior</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# KPI CARDS
# ══════════════════════════════════════════════════════════════════════════════
total_sales    = df["Sales"].sum()
total_revenue  = df["Total"].sum()
total_txn      = len(df)
avg_rating     = df["Rating"].mean()
avg_order_val  = df["Total"].mean()
total_qty      = df["Quantity"].sum()

kpi_cols = st.columns(6)
kpis = [
    ("💰 Total Sales",      f"${total_sales:,.0f}",    "Qty × Unit Price"),
    ("🧾 Total Revenue",    f"${total_revenue:,.0f}",  "incl. 5% tax"),
    ("📋 Transactions",     f"{total_txn:,}",          "invoices"),
    ("⭐ Avg Rating",       f"{avg_rating:.2f} / 10",  "customer score"),
    ("🛍️ Avg Order",        f"${avg_order_val:,.2f}",  "per transaction"),
    ("📦 Units Sold",       f"{total_qty:,}",          "total quantity"),
]
for col, (label, value, sub) in zip(kpi_cols, kpis):
    with col:
        st.markdown(
            f"<div class='kpi-card'>"
            f"<p class='kpi-value'>{value}</p>"
            f"<p class='kpi-label'>{label}</p>"
            f"<p style='font-size:0.72rem;color:#9fa8da;margin:0'>{sub}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════
tab_overview, tab_products, tab_customers, tab_payments, tab_ratings, tab_data = st.tabs([
    "📊 Overview", "📦 Products", "👥 Customers", "💳 Payments", "⭐ Ratings", "🗂️ Raw Data"
])

CHART_COLORS = px.colors.qualitative.Vivid

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:
    st.markdown("<div class='section-header'>Sales by Branch & City</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Branch bar chart
    branch_sales = df.groupby("Branch")["Sales"].sum().reset_index().sort_values("Sales", ascending=False)
    fig_branch = px.bar(
        branch_sales, x="Branch", y="Sales",
        color="Branch", color_discrete_sequence=CHART_COLORS,
        title="Total Sales by Branch",
        labels={"Sales": "Sales ($)"},
        text_auto=".2s",
    )
    fig_branch.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
    col1.plotly_chart(fig_branch, use_container_width=True)

    # City pie
    city_sales = df.groupby("City")["Sales"].sum().reset_index()
    fig_city = px.pie(
        city_sales, names="City", values="Sales",
        title="Sales Share by City",
        color_discrete_sequence=CHART_COLORS,
        hole=0.42,
    )
    fig_city.update_traces(textposition="outside", textinfo="percent+label")
    fig_city.update_layout(paper_bgcolor="white")
    col2.plotly_chart(fig_city, use_container_width=True)

    # Monthly sales trend
    st.markdown("<div class='section-header'>Sales Trend Over Time</div>", unsafe_allow_html=True)
    monthly = df.groupby(df["Date"].dt.to_period("M"))["Sales"].sum().reset_index()
    monthly["Date"] = monthly["Date"].astype(str)
    fig_trend = px.line(
        monthly, x="Date", y="Sales",
        markers=True,
        title="Monthly Sales Trend",
        labels={"Sales": "Sales ($)", "Date": "Month"},
        color_discrete_sequence=["#3949ab"],
    )
    fig_trend.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig_trend, use_container_width=True)

    # Branch × Product heatmap
    st.markdown("<div class='section-header'>Branch × Product Line Heatmap</div>", unsafe_allow_html=True)
    heat_data = df.pivot_table(index="Branch", columns="Product line", values="Sales", aggfunc="sum").fillna(0)
    fig_heat = px.imshow(
        heat_data,
        color_continuous_scale="Blues",
        title="Sales Heatmap (Branch × Product Line)",
        aspect="auto",
        text_auto=".2s",
    )
    fig_heat.update_layout(paper_bgcolor="white")
    st.plotly_chart(fig_heat, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_products:
    st.markdown("<div class='section-header'>Product Line Performance</div>", unsafe_allow_html=True)

    prod = df.groupby("Product line").agg(
        Total_Sales=("Sales", "sum"),
        Transactions=("Invoice ID", "count"),
        Avg_Unit_Price=("Unit price", "mean"),
        Total_Qty=("Quantity", "sum"),
        Avg_Rating=("Rating", "mean"),
    ).reset_index().sort_values("Total_Sales", ascending=False)

    col1, col2 = st.columns(2)

    fig_prod_bar = px.bar(
        prod, x="Total_Sales", y="Product line",
        orientation="h",
        color="Total_Sales",
        color_continuous_scale="Blues",
        title="Total Sales by Product Line",
        labels={"Total_Sales": "Sales ($)", "Product line": ""},
        text_auto=".2s",
    )
    fig_prod_bar.update_layout(plot_bgcolor="white", paper_bgcolor="white", coloraxis_showscale=False)
    col1.plotly_chart(fig_prod_bar, use_container_width=True)

    fig_prod_qty = px.bar(
        prod.sort_values("Total_Qty", ascending=False),
        x="Total_Qty", y="Product line",
        orientation="h",
        color="Total_Qty",
        color_continuous_scale="Purples",
        title="Units Sold by Product Line",
        labels={"Total_Qty": "Units Sold", "Product line": ""},
        text_auto="d",
    )
    fig_prod_qty.update_layout(plot_bgcolor="white", paper_bgcolor="white", coloraxis_showscale=False)
    col2.plotly_chart(fig_prod_qty, use_container_width=True)

    # Radar chart — multi-metric product comparison
    st.markdown("<div class='section-header'>Multi-Metric Product Radar</div>", unsafe_allow_html=True)
    radar_metrics = ["Total_Sales", "Transactions", "Total_Qty", "Avg_Rating"]
    radar_norm = prod.copy()
    for m in radar_metrics:
        rng = radar_norm[m].max() - radar_norm[m].min()
        radar_norm[m] = (radar_norm[m] - radar_norm[m].min()) / (rng if rng else 1)

    fig_radar = go.Figure()
    for _, row in radar_norm.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[row[m] for m in radar_metrics],
            theta=radar_metrics,
            fill="toself",
            name=row["Product line"],
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title="Normalised Product Comparison",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Summary table
    st.markdown("<div class='section-header'>Summary Table</div>", unsafe_allow_html=True)
    prod_display = prod.copy()
    prod_display["Total_Sales"]    = prod_display["Total_Sales"].map("${:,.2f}".format)
    prod_display["Avg_Unit_Price"] = prod_display["Avg_Unit_Price"].map("${:,.2f}".format)
    prod_display["Avg_Rating"]     = prod_display["Avg_Rating"].map("{:.2f}".format)
    st.dataframe(prod_display.rename(columns={
        "Product line": "Product Line", "Total_Sales": "Total Sales",
        "Transactions": "Txn Count", "Avg_Unit_Price": "Avg Unit Price",
        "Total_Qty": "Units Sold", "Avg_Rating": "Avg Rating",
    }), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CUSTOMERS
# ══════════════════════════════════════════════════════════════════════════════
with tab_customers:
    st.markdown("<div class='section-header'>Customer Type & Gender Analysis</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    ctype_sales = df.groupby("Customer type")["Sales"].sum().reset_index()
    fig_ctype = px.pie(
        ctype_sales, names="Customer type", values="Sales",
        title="Sales by Customer Type",
        color_discrete_sequence=CHART_COLORS, hole=0.42,
    )
    fig_ctype.update_layout(paper_bgcolor="white")
    col1.plotly_chart(fig_ctype, use_container_width=True)

    gender_sales = df.groupby("Gender")["Sales"].sum().reset_index()
    fig_gender = px.pie(
        gender_sales, names="Gender", values="Sales",
        title="Sales by Gender",
        color_discrete_sequence=["#e91e63", "#1e88e5"], hole=0.42,
    )
    fig_gender.update_layout(paper_bgcolor="white")
    col2.plotly_chart(fig_gender, use_container_width=True)

    gender_txn = df.groupby("Gender")["Invoice ID"].count().reset_index(name="Transactions")
    fig_gtxn = px.bar(
        gender_txn, x="Gender", y="Transactions",
        color="Gender",
        color_discrete_sequence=["#e91e63", "#1e88e5"],
        title="Transactions by Gender",
        text_auto="d",
    )
    fig_gtxn.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
    col3.plotly_chart(fig_gtxn, use_container_width=True)

    # Grouped bar — customer type × product line
    st.markdown("<div class='section-header'>Customer Type × Product Line</div>", unsafe_allow_html=True)
    ct_prod = df.groupby(["Customer type", "Product line"])["Sales"].sum().reset_index()
    fig_ct_prod = px.bar(
        ct_prod, x="Product line", y="Sales",
        color="Customer type",
        barmode="group",
        title="Sales by Customer Type per Product Line",
        labels={"Sales": "Sales ($)"},
        color_discrete_sequence=CHART_COLORS,
        text_auto=".2s",
    )
    fig_ct_prod.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-20)
    st.plotly_chart(fig_ct_prod, use_container_width=True)

    # Gender × product line
    st.markdown("<div class='section-header'>Gender × Product Line</div>", unsafe_allow_html=True)
    g_prod = df.groupby(["Gender", "Product line"])["Sales"].sum().reset_index()
    fig_g_prod = px.bar(
        g_prod, x="Product line", y="Sales",
        color="Gender",
        barmode="stack",
        title="Sales by Gender per Product Line",
        labels={"Sales": "Sales ($)"},
        color_discrete_sequence=["#e91e63", "#1e88e5"],
        text_auto=".2s",
    )
    fig_g_prod.update_layout(plot_bgcolor="white", paper_bgcolor="white", xaxis_tickangle=-20)
    st.plotly_chart(fig_g_prod, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PAYMENTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_payments:
    st.markdown("<div class='section-header'>Payment Method Analysis</div>", unsafe_allow_html=True)

    pay = df.groupby("Payment").agg(
        Total_Sales=("Sales", "sum"),
        Transactions=("Invoice ID", "count"),
        Avg_Order=("Total", "mean"),
    ).reset_index()

    col1, col2 = st.columns(2)

    fig_pay_pie = px.pie(
        pay, names="Payment", values="Total_Sales",
        title="Sales Share by Payment Method",
        color_discrete_sequence=CHART_COLORS, hole=0.42,
    )
    fig_pay_pie.update_layout(paper_bgcolor="white")
    col1.plotly_chart(fig_pay_pie, use_container_width=True)

    fig_pay_bar = px.bar(
        pay, x="Payment", y="Transactions",
        color="Payment",
        color_discrete_sequence=CHART_COLORS,
        title="Transaction Count by Payment Method",
        text_auto="d",
    )
    fig_pay_bar.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
    col2.plotly_chart(fig_pay_bar, use_container_width=True)

    # Payment × Branch
    st.markdown("<div class='section-header'>Payment Method per Branch</div>", unsafe_allow_html=True)
    pay_branch = df.groupby(["Branch", "Payment"])["Sales"].sum().reset_index()
    fig_pb = px.bar(
        pay_branch, x="Branch", y="Sales",
        color="Payment",
        barmode="group",
        title="Sales by Payment Method per Branch",
        labels={"Sales": "Sales ($)"},
        color_discrete_sequence=CHART_COLORS,
        text_auto=".2s",
    )
    fig_pb.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig_pb, use_container_width=True)

    # Avg order value
    st.markdown("<div class='section-header'>Average Order Value by Payment Method</div>", unsafe_allow_html=True)
    fig_avg = px.bar(
        pay.sort_values("Avg_Order", ascending=False),
        x="Payment", y="Avg_Order",
        color="Payment",
        color_discrete_sequence=CHART_COLORS,
        title="Avg Order Value by Payment Method",
        labels={"Avg_Order": "Avg Order ($)"},
        text_auto=".2f",
    )
    fig_avg.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig_avg, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — RATINGS
# ══════════════════════════════════════════════════════════════════════════════
with tab_ratings:
    st.markdown("<div class='section-header'>Customer Ratings Analysis</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Distribution histogram
    fig_hist = px.histogram(
        df, x="Rating",
        nbins=30,
        title="Rating Distribution",
        labels={"Rating": "Rating (0–10)", "count": "Frequency"},
        color_discrete_sequence=["#3949ab"],
    )
    fig_hist.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    col1.plotly_chart(fig_hist, use_container_width=True)

    # Box plot by branch
    fig_box = px.box(
        df, x="Branch", y="Rating",
        color="Branch",
        color_discrete_sequence=CHART_COLORS,
        title="Rating Distribution by Branch",
        points="outliers",
    )
    fig_box.update_layout(plot_bgcolor="white", paper_bgcolor="white", showlegend=False)
    col2.plotly_chart(fig_box, use_container_width=True)

    # Avg rating by product line
    st.markdown("<div class='section-header'>Average Rating by Product Line</div>", unsafe_allow_html=True)
    rat_prod = df.groupby("Product line")["Rating"].mean().reset_index().sort_values("Rating", ascending=False)
    rat_prod["Rating"] = rat_prod["Rating"].round(2)
    fig_rat_prod = px.bar(
        rat_prod, x="Rating", y="Product line",
        orientation="h",
        color="Rating",
        color_continuous_scale="RdYlGn",
        title="Avg Rating by Product Line",
        text_auto=".2f",
        range_x=[0, 10],
    )
    fig_rat_prod.update_layout(plot_bgcolor="white", paper_bgcolor="white", coloraxis_showscale=False)
    st.plotly_chart(fig_rat_prod, use_container_width=True)

    # Scatter — Rating vs Sales
    st.markdown("<div class='section-header'>Rating vs Sales (Scatter)</div>", unsafe_allow_html=True)
    fig_scatter = px.scatter(
        df, x="Rating", y="Sales",
        color="Product line",
        size="Quantity",
        opacity=0.7,
        title="Rating vs Sales (bubble size = Quantity)",
        labels={"Sales": "Sales ($)"},
        color_discrete_sequence=CHART_COLORS,
        trendline="ols",
        trendline_scope="overall",
    )
    fig_scatter.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Summary stats table
    st.markdown("<div class='section-header'>Rating Summary Statistics</div>", unsafe_allow_html=True)
    rat_stats = df.groupby("Branch")["Rating"].describe()[["count","mean","std","min","50%","max"]].reset_index()
    rat_stats.columns = ["Branch", "Count", "Mean", "Std Dev", "Min", "Median", "Max"]
    rat_stats = rat_stats.round(2)
    st.dataframe(rat_stats, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — RAW DATA
# ══════════════════════════════════════════════════════════════════════════════
with tab_data:
    st.markdown("<div class='section-header'>Filtered Dataset</div>", unsafe_allow_html=True)
    st.markdown(f"Showing **{len(df):,}** rows  ×  **{len(df.columns)}** columns")

    # Search
    search = st.text_input("🔍 Search any column value", placeholder="e.g. Yangon, Ewallet, Member …")
    display_df = df.copy()
    if search.strip():
        mask = display_df.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]

    st.dataframe(display_df, use_container_width=True, height=400)

    # Export
    csv_bytes = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download filtered CSV",
        data=csv_bytes,
        file_name="filtered_sales.csv",
        mime="text/csv",
    )

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='footer'>Supermarket Sales Dashboard · Built with Streamlit & Plotly · Data: 500 transactions</div>",
    unsafe_allow_html=True,
)
