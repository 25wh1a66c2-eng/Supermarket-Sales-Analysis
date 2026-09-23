# 🛒 Supermarket Sales Analysis Dashboard

Interactive Streamlit dashboard that analyses 500 supermarket sales transactions across branches, product lines, customer segments, payment methods, and ratings.

---

## 📁 Project Structure

```
supermarket_project/
├── app.py               ← Streamlit dashboard (main entry point)
├── generate_data.py     ← Script to create sample supermarket_sales.csv
├── supermarket_sales.csv  ← Generated dataset (run generate_data.py first)
├── requirements.txt     ← Python dependencies
└── README.md
```

---

## 🚀 Quick Start

### 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### 2 — Generate sample data
```bash
python generate_data.py
```
This creates `supermarket_sales.csv` with 500 realistic transactions.

> **Or** paste the [Google Sheets link](https://docs.google.com/spreadsheets/d/1QIX__4VObHFMEXnRM2xJyXmB5JAB2peHrJcQ41_U9TE/edit?usp=sharing) exported as CSV and upload it via the sidebar.

### 3 — Run the dashboard
```bash
streamlit run app.py
```
Open **http://localhost:8501** in your browser.

---

## 📊 Dashboard Tabs

| Tab | Contents |
|-----|----------|
| **Overview** | KPI cards, branch & city sales, monthly trend, heatmap |
| **Products** | Sales & quantity by product line, radar comparison, summary table |
| **Customers** | Customer type & gender breakdown, cross-analysis with product lines |
| **Payments** | Payment method share, transaction count, avg order value |
| **Ratings** | Distribution histogram, box plots, scatter vs sales, stats table |
| **Raw Data** | Searchable filtered table with CSV export |

---

## 📋 Dataset Columns

| Column | Description |
|--------|-------------|
| Invoice ID | Unique transaction ID |
| Branch | Store branch (A / B / C) |
| City | Yangon / Mandalay / Naypyitaw |
| Customer type | Member / Normal |
| Gender | Male / Female |
| Product line | 6 product categories |
| Unit price | Price per unit (USD) |
| Quantity | Items purchased |
| Tax 5% | 5% tax on subtotal |
| Total | Final amount incl. tax |
| Date | Transaction date |
| Time | Transaction time |
| Payment | Ewallet / Cash / Credit card |
| Rating | Customer rating (4–10) |
| **Sales** | *(computed)* Quantity × Unit price |

---

## 🔍 Analysis Steps

1. Load CSV and strip whitespace from column names  
2. Parse dates/times; coerce numerics; drop fully-empty rows  
3. Compute `Sales = Quantity × Unit Price`  
4. Group & aggregate by branch, city, product, customer, payment  
5. Render interactive Plotly charts inside a Streamlit multi-tab layout  
6. Surface business insights via KPI cards and summary tables  
