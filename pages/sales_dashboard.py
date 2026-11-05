import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from pymongo import MongoClient
from config import PG_HOST , PG_PORT , PG_DATABASE , PG_USER , PG_PASSWORD
from sqlalchemy.engine import URL
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    layout="wide"
)

st.title("📊 Sales Analytics Dashboard")
st.caption("E-Commerce Data Warehouse")


# MongoDB connection
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "ecommerce_nosql"

# PostgreSQL connection

@st.cache_resource
def get_engine():
    
    connection_url=URL.create(
    "postgresql+psycopg2",
    username=PG_USER,
    password=PG_PASSWORD,
    host=PG_HOST,
    port=int(PG_PORT),
    database=PG_DATABASE
)
    return create_engine(connection_url)


@st.cache_resource
def get_mongo_client():
    return MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )


engine = get_engine()

try:
    with engine.connect() as connection:

        # Available sales dates
        dates_df = pd.read_sql(
            text("""
                SELECT MIN(d.full_date) AS min_date,
                       MAX(d.full_date) AS max_date
                FROM fact_sales f
                JOIN dim_date d ON f.date_id = d.date_id
            """),
            connection
        )

        if (
            dates_df.empty
            or pd.isna(dates_df.iloc[0]["min_date"])
        ):
            st.warning("No sales data available.")
            st.stop()

        min_date = pd.to_datetime(
            dates_df.iloc[0]["min_date"]
        ).date()

        max_date = pd.to_datetime(
            dates_df.iloc[0]["max_date"]
        ).date()

        # Filters
        st.subheader("🔎 Dashboard Filters")

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            start_date = st.date_input(
                "Start date",
                value=min_date,
                min_value=min_date,
                max_value=max_date
            )

        with filter_col2:
            end_date = st.date_input(
                "End date",
                value=max_date,
                min_value=min_date,
                max_value=max_date
            )

        categories_df = pd.read_sql(
            text("""
                SELECT DISTINCT category
                FROM dim_product
                WHERE category IS NOT NULL
                ORDER BY category
            """),
            connection
        )

        categories = categories_df["category"].tolist()

        with filter_col3:
            selected_category = st.selectbox(
                "Product category",
                ["All Categories"] + categories
            )

        if start_date > end_date:
            st.error(
                "Start date must be before or equal to end date."
            )
            st.stop()

        # Shared filters
        filter_sql = """
            JOIN dim_date d ON f.date_id = d.date_id
            JOIN dim_product p ON f.product_id = p.product_id
            WHERE d.full_date BETWEEN :start_date AND :end_date
        """

        params = {
            "start_date": start_date,
            "end_date": end_date
        }

        if selected_category != "All Categories":
            filter_sql += " AND p.category = :category"
            params["category"] = selected_category

        # KPIs
        st.subheader("📌 Key Performance Indicators")

        kpi_query = f"""
            SELECT
                COALESCE(SUM(f.total_amount), 0) AS revenue,
                COUNT(DISTINCT f.order_id) AS orders,
                COUNT(DISTINCT f.customer_id) AS customers,
                COALESCE(
                    SUM(f.total_amount) /
                    NULLIF(COUNT(DISTINCT f.order_id), 0),
                    0
                ) AS average_order_value
            FROM fact_sales f
            {filter_sql}
        """

        kpis = pd.read_sql(
            text(kpi_query),
            connection,
            params=params
        ).iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Revenue",
            f"{kpis['revenue']:,.2f}"
        )
        col2.metric(
            "Total Orders",
            f"{kpis['orders']:,}"
        )
        col3.metric(
            "Customers",
            f"{kpis['customers']:,}"
        )
        col4.metric(
            "Average Order Value",
            f"{kpis['average_order_value']:,.2f}"
        )

        st.divider()

        # Monthly revenue
        st.subheader("📈 Monthly Revenue")

        monthly_query = f"""
            SELECT
                d.year,
                d.month,
                SUM(f.total_amount) AS revenue
            FROM fact_sales f
            {filter_sql}
            GROUP BY d.year, d.month
            ORDER BY d.year, d.month
        """

        monthly_df = pd.read_sql(
            text(monthly_query),
            connection,
            params=params
        )

        if not monthly_df.empty:
            monthly_df["Period"] = (
                monthly_df["year"].astype(str)
                + "-"
                + monthly_df["month"].astype(str).str.zfill(2)
            )

            st.line_chart(
                monthly_df.set_index("Period")["revenue"]
            )
        else:
            st.info("No sales found for the selected filters.")

        # Top products
        st.subheader("🏆 Top 5 Products by Revenue")

        products_query = f"""
            SELECT
                p.name AS product_name,
                SUM(f.total_amount) AS revenue,
                SUM(f.quantity) AS units_sold
            FROM fact_sales f
            {filter_sql}
            GROUP BY p.product_id, p.name
            ORDER BY revenue DESC
            LIMIT 5
        """

        products_df = pd.read_sql(
            text(products_query),
            connection,
            params=params
        )

        if not products_df.empty:
            st.bar_chart(
                products_df.set_index("product_name")["revenue"]
            )
            st.dataframe(
                products_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No products found for the selected filters.")

        # Revenue by category
        st.subheader("📦 Revenue by Category")

        category_query = f"""
            SELECT
                p.category,
                SUM(f.total_amount) AS revenue
            FROM fact_sales f
            {filter_sql}
            GROUP BY p.category
            ORDER BY revenue DESC
        """

        category_df = pd.read_sql(
            text(category_query),
            connection,
            params=params
        )

        if not category_df.empty:
            st.bar_chart(
                category_df.set_index("category")["revenue"]
            )
            st.dataframe(
                category_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No categories found for the selected filters.")

except Exception as error:
    st.error(f"Could not load dashboard data: {error}")


# MongoDB Reviews & Ratings
st.divider()
st.header("⭐ Customer Reviews & Ratings")

try:
    mongo_client = get_mongo_client()
    mongo_client.admin.command("ping")

    mongo_db = mongo_client[MONGO_DATABASE]
    reviews_collection = mongo_db["reviews"]

    reviews_data = list(
        reviews_collection.find(
            {},
            {
                "_id": 0,
                "customer_id": 1,
                "product_id": 1,
                "rating": 1,
                "comment": 1,
                "tags": 1,
                "created_at": 1
            }
        )
    )

    if reviews_data:
        reviews_df = pd.DataFrame(reviews_data)

        if "rating" in reviews_df.columns:
            reviews_df["rating"] = pd.to_numeric(
                reviews_df["rating"],
                errors="coerce"
            )

            valid_ratings = reviews_df[
                reviews_df["rating"].between(1, 5)
            ]

            review_col1, review_col2, review_col3 = st.columns(3)

            review_col1.metric(
                "Total Reviews",
                f"{len(reviews_df):,}"
            )

            review_col2.metric(
                "Average Rating",
                (
                    f"{valid_ratings['rating'].mean():.2f} / 5"
                    if not valid_ratings.empty
                    else "N/A"
                )
            )

            review_col3.metric(
                "5-Star Reviews",
                f"{(valid_ratings['rating'] == 5).sum():,}"
            )

            st.subheader("Rating Distribution")

            if not valid_ratings.empty:
                rating_counts = (
                    valid_ratings["rating"]
                    .value_counts()
                    .reindex([1, 2, 3, 4, 5], fill_value=0)
                    .sort_index()
                )

                st.bar_chart(rating_counts)

        st.subheader("📝 Customer Feedback")
        st.dataframe(
            reviews_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No customer reviews found in MongoDB.")

except Exception as error:
    st.warning(
        f"Could not load reviews from MongoDB: {error}"
    )