import streamlit as st

st.set_page_config(
    page_title="E-Commerce Data Engineering",
    page_icon="🛒",
    layout="wide"
)

# Define pages
postgres_page = st.Page(
    "pages/postgresql.py",
    title="PostgreSQL",
    icon="🐘"
)

mongo_page = st.Page(
    "pages/mongo.py",
    title="MongoDB",
    icon="🍃"
)

etl_page = st.Page(
    "pages/etl.py",
    title="ETL Pipeline",
    icon="🔄"
)

sales_page=st.Page(
    "pages/sales_dashboard.py",
    title="Sales Dashboard",
    icon="📊"
)

# Navigation
pg = st.navigation(
    {
        "Data Sources": [
            postgres_page,
            mongo_page
        ],
        "Data Engineering": [
            etl_page
        ],
        "Analytics": [
            sales_page
        ]
    }
)

pg.run()