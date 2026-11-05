import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text , URL
from pymongo import MongoClient
from config import PG_HOST , PG_PORT , PG_USER , PG_DATABASE , PG_PASSWORD

st.title("🔄 ETL Pipeline")
st.caption("Extract • Transform • Validate • Load")

# Database configuration

SOURCE_DATABASE = "ecommerce_source"
DW_DATABASE = "ecommerce_dw"

MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "ecommerce_nosql"


@st.cache_resource
def get_mongo_client():
    return MongoClient(MONGO_URI)


@st.cache_resource
def get_pg_engine(database):
    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=int(PG_PORT),
        database=database
    )
    return create_engine(connection_url)

st.subheader("1️⃣ Extract — Data Sources")

if st.button("🔍 Check Data Sources", type="primary"):
    try:
        source_engine = get_pg_engine(SOURCE_DATABASE)

        with source_engine.connect() as connection:
            tables = [
                "customers",
                "products",
                "orders",
                "order_items",
                "payments"
            ]

            counts = []

            for table in tables:
                count = connection.execute(
                    text(f'SELECT COUNT(*) FROM "{table}"')
                ).scalar_one()

                counts.append({
                    "Table": table,
                    "Records": count
                })

        st.success("PostgreSQL source connected successfully.")
        st.dataframe(
            pd.DataFrame(counts),
            use_container_width=True,
            hide_index=True
        )

        mongo_client = get_mongo_client()
        mongo_client.admin.command("ping")
        mongo_db = mongo_client[MONGO_DATABASE]

        mongo_counts = [
            {
                "Collection": collection,
                "Records": mongo_db[collection].count_documents({})
            }
            for collection in ["reviews", "user_activity"]
        ]

        st.success("MongoDB connected successfully.")
        st.dataframe(
            pd.DataFrame(mongo_counts),
            use_container_width=True,
            hide_index=True
        )

    except Exception as error:
        st.error(f"Connection or extraction check failed: {error}")


st.divider()
st.subheader("2️⃣ Transform — Data Cleaning")

st.write(
    "The ETL script cleans the extracted data, handles duplicates, "
    "and prepares customer, product, date, payment, and sales data."
)

st.divider()
st.subheader("3️⃣ Validate — Data Quality")

st.write(
    "The pipeline checks identifiers, missing values, relationships "
    "between tables, product prices, order quantities, and review ratings."
)

st.info(
    "To see the detailed validation results, run etl_pipeline.py "
    "from the project terminal."
)

st.divider()
st.subheader("4️⃣ Load — Data Warehouse")

if st.button("📦 Check Data Warehouse"):
    try:
        dw_engine = get_pg_engine(DW_DATABASE)

        warehouse_tables = [
            "dim_customer",
            "dim_product",
            "dim_date",
            "dim_payment",
            "fact_sales"
        ]

        with dw_engine.connect() as connection:
            results = []

            for table in warehouse_tables:
                count = connection.execute(
                    text(f'SELECT COUNT(*) FROM "{table}"')
                ).scalar_one()

                results.append({
                    "Warehouse Table": table,
                    "Records": count
                })

        st.success("Data Warehouse checked successfully.")
        st.dataframe(
            pd.DataFrame(results),
            use_container_width=True,
            hide_index=True
        )

    except Exception as error:
        st.error(f"Could not check Data Warehouse: {error}")