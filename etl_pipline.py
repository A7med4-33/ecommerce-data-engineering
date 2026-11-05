import pandas as pd
from sqlalchemy import create_engine, text , URL
from pymongo import MongoClient
from config import PG_HOST , PG_PORT , PG_USER , PG_DATABASE , PG_PASSWORD


# ==============================
# PostgreSQL Connection
# ==============================


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

source_engine = create_engine(
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}"
    f"@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
)

# Data Warehouse Connection
DW_DATABASE = "ecommerce_dw"

warehouse_engine = create_engine(
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}"
    f"@{PG_HOST}:{PG_PORT}/{DW_DATABASE}"
)

# ==============================
# MongoDB Connection
# ==============================

mongo_client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=5000
)

mongo_db = mongo_client["ecommerce_nosql"]


# ==============================
# Extract Data
# ==============================

def extract_data():

    print("Connecting to PostgreSQL...")

    with source_engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    print("PostgreSQL connected successfully!")

    customers_df = pd.read_sql(
        "SELECT * FROM customers", source_engine
    )

    products_df = pd.read_sql(
        "SELECT * FROM products", source_engine
    )

    orders_df = pd.read_sql(
        "SELECT * FROM orders", source_engine
    )

    order_items_df = pd.read_sql(
        "SELECT * FROM order_items", source_engine
    )

    payments_df = pd.read_sql(
        "SELECT * FROM payments", source_engine
    )

    print("\nConnecting to MongoDB...")

    mongo_client.admin.command("ping")

    print("MongoDB connected successfully!")

    reviews_df = pd.DataFrame(
        list(mongo_db["reviews"].find({}, {"_id": 0}))
    )

    activities_df = pd.DataFrame(
        list(mongo_db["user_activity"].find({}, {"_id": 0}))
    )

    dataframes = {
        "Customers": customers_df,
        "Products": products_df,
        "Orders": orders_df,
        "Order Items": order_items_df,
        "Payments": payments_df,
        "Reviews": reviews_df,
        "User Activity": activities_df
    }

    print("\n========== EXTRACT RESULTS ==========")

    for name, df in dataframes.items():
        print(f"{name}: {len(df):,} rows")

    return dataframes

# ==============================
# Transform Data
# ==============================

def transform_data(dataframes):

    print("\n========== TRANSFORM RESULTS ==========")

    cleaned_data = {}

    for name, df in dataframes.items():

        original_rows = len(df)

        # Remove completely empty rows
        df = df.dropna(how="all").copy()

        # Remove duplicate rows safely,
        # including rows containing lists or dictionaries
        if not df.empty:
            comparable_df = df.astype("string")
            df = df.loc[
                ~comparable_df.duplicated()
            ].copy()

        cleaned_data[name] = df

        removed_rows = original_rows - len(df)

        print(f"{name}:")
        print(f"  Original rows: {original_rows:,}")
        print(f"  Cleaned rows: {len(df):,}")
        print(f"  Removed duplicate/empty rows: {removed_rows:,}")

    print("\nTransformation completed successfully!")

    return cleaned_data


# ==============================
# Data Quality Checks
# ==============================

def validate_data(dataframes):

    print("\n========== DATA QUALITY CHECKS ==========")

    checks_passed = 0
    checks_failed = 0

    def check(condition, message):
        nonlocal checks_passed, checks_failed

        if condition:
            print(f"PASS: {message}")
            checks_passed += 1
        else:
            print(f"FAIL: {message}")
            checks_failed += 1

    customers = dataframes["Customers"]
    products = dataframes["Products"]
    orders = dataframes["Orders"]
    order_items = dataframes["Order Items"]
    reviews = dataframes["Reviews"]

    # Primary key checks
    check(
        customers["customer_id"].notna().all()
        and customers["customer_id"].is_unique,
        "Customer IDs are present and unique"
    )

    check(
        products["product_id"].notna().all()
        and products["product_id"].is_unique,
        "Product IDs are present and unique"
    )

    check(
        orders["order_id"].notna().all()
        and orders["order_id"].is_unique,
        "Order IDs are present and unique"
    )

    check(
        order_items["order_item_id"].notna().all()
        and order_items["order_item_id"].is_unique,
        "Order item IDs are present and unique"
    )

    # Business rules
    check(
        (pd.to_numeric(products["price"], errors="coerce").dropna() >= 0).all()
        and pd.to_numeric(products["price"], errors="coerce").notna().all(),
        "Product prices are valid and non-negative"
    )

    check(
        (pd.to_numeric(order_items["quantity"], errors="coerce").dropna() > 0).all()
        and pd.to_numeric(order_items["quantity"], errors="coerce").notna().all(),
        "Order item quantities are valid and greater than zero"
    )

    # Foreign key checks
    check(
        orders["customer_id"].isin(customers["customer_id"]).all(),
        "Every order references an existing customer"
    )

    check(
        order_items["order_id"].isin(orders["order_id"]).all(),
        "Every order item references an existing order"
    )

    check(
        order_items["product_id"].isin(products["product_id"]).all(),
        "Every order item references an existing product"
    )

    # MongoDB review checks
    if "rating" in reviews.columns and not reviews.empty:
        ratings = pd.to_numeric(reviews["rating"], errors="coerce")

        check(
            ratings.notna().all() and ratings.between(1, 5).all(),
            "Review ratings are between 1 and 5"
        )
    else:
        check(False, "Review ratings column exists and contains data")

    print("\n========== QUALITY SUMMARY ==========")
    print(f"Checks passed: {checks_passed}")
    print(f"Checks failed: {checks_failed}")

    return checks_failed == 0


# ==============================
# Prepare Data Warehouse Tables
# ==============================

def prepare_warehouse_data(dataframes):

    print("\n========== PREPARING DATA WAREHOUSE ==========")

    customers = dataframes["Customers"].copy()
    products = dataframes["Products"].copy()
    orders = dataframes["Orders"].copy()
    order_items = dataframes["Order Items"].copy()
    payments = dataframes["Payments"].copy()

    # 1. Customer Dimension
    dim_customer = customers[
        ["customer_id", "name", "email", "country", "signup_date"]
    ].copy()

    # 2. Product Dimension
    dim_product = products[
        ["product_id", "name", "category", "price"]
    ].copy()

    # 3. Payment Dimension
    dim_payment = payments[
        ["payment_id", "payment_method", "status"]
    ].copy()

    # 4. Prepare order dates
    orders["order_date"] = pd.to_datetime(
        orders["order_date"], errors="coerce"
    )

    valid_orders = orders.dropna(subset=["order_date"]).copy()

    valid_orders["date_id"] = (
        valid_orders["order_date"].dt.strftime("%Y%m%d").astype("int64")
    )

    unique_dates = valid_orders["order_date"].drop_duplicates()

    dim_date = pd.DataFrame({
        "full_date": unique_dates
    })

    dim_date["date_id"] = (
        dim_date["full_date"].dt.strftime("%Y%m%d").astype("int64")
    )
    dim_date["day"] = dim_date["full_date"].dt.day
    dim_date["month"] = dim_date["full_date"].dt.month
    dim_date["year"] = dim_date["full_date"].dt.year

    dim_date = dim_date[
        ["date_id", "full_date", "day", "month", "year"]
    ].sort_values("date_id")

    # 5. Prepare Sales Fact
    sales = order_items.merge(
        valid_orders[["order_id", "customer_id", "date_id"]],
        on="order_id",
        how="inner",
        validate="many_to_one"
    )

    sales = sales.merge(
        products[["product_id", "price"]],
        on="product_id",
        how="inner",
        validate="many_to_one"
    )

    sales = sales.merge(
        payments[["payment_id", "order_id"]],
        on="order_id",
        how="inner",
        validate="many_to_one"
    )

    sales["quantity"] = pd.to_numeric(
        sales["quantity"], errors="coerce"
    )
    sales["unit_price"] = pd.to_numeric(
        sales["price"], errors="coerce"
    )

    sales["total_amount"] = (
        sales["quantity"] * sales["unit_price"]
    ).round(2)

    fact_sales = sales[
        [
            "order_item_id",
            "order_id",
            "date_id",
            "customer_id",
            "product_id",
            "payment_id",
            "quantity",
            "unit_price",
            "total_amount"
        ]
    ].copy()

    # Display prepared row counts
    warehouse_tables = {
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_date": dim_date,
        "dim_payment": dim_payment,
        "fact_sales": fact_sales
    }

    print("\n========== PREPARATION RESULTS ==========")

    for table_name, df in warehouse_tables.items():
        print(f"{table_name}: {len(df):,} rows")

    print("\nWarehouse data preparation completed!")

    return warehouse_tables

# ==============================
# Load Data into Data Warehouse
# ==============================

def load_warehouse_data(warehouse_tables):

    print("\n========== LOADING DATA WAREHOUSE ==========")

    # Verify that each order has at most one payment.
    # The current fact table design expects one payment per order.
    payments = warehouse_tables["dim_payment"]

    # Check the source payment-to-order relationship before loading.
    # This check is performed on the source data in the main block below.

    load_order = [
        "dim_customer",
        "dim_product",
        "dim_date",
        "dim_payment",
        "fact_sales"
    ]

    try:
        with warehouse_engine.begin() as connection:

            # Stop if the destination tables are not empty.
            for table_name in load_order:
                row_count = connection.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                ).scalar_one()

                if row_count != 0:
                    raise ValueError(
                        f"{table_name} is not empty. "
                        "Loading cancelled to prevent duplicate data."
                    )

            for table_name in load_order:

                df = warehouse_tables[table_name]

                print(f"Loading {table_name}: {len(df):,} rows...")

                df.to_sql(
                    name=table_name,
                    con=connection,
                    if_exists="append",
                    index=False,
                    chunksize=5000
                )

                print(f"Loaded {table_name} successfully.")

        print("\nAll warehouse tables loaded successfully!")

    except Exception as error:
        print(f"\nWarehouse loading failed: {error}")
        raise

# ==============================
# Run ETL
# ==============================

if __name__ == "__main__":

    try:
        # Step 1: Extract
        extracted_data = extract_data()

        # Step 2: Transform
        cleaned_data = transform_data(extracted_data)

        # Step 3: Validate
        quality_passed = validate_data(cleaned_data)

        if not quality_passed:
            raise ValueError(
                "Data quality checks failed. Loading cancelled."
            )

        # Step 4: Prepare warehouse tables
        warehouse_data = prepare_warehouse_data(cleaned_data)

        # Step 5: Check that each order has at most one payment
        if not cleaned_data["Payments"]["order_id"].is_unique:
            raise ValueError(
                "Multiple payments exist for an order. "
                "Loading cancelled to prevent duplicate sales."
            )

        # Step 6: Load
        load_warehouse_data(warehouse_data)

        print("\nETL Pipeline completed successfully!")

    except Exception as error:
        print(f"\nETL Pipeline failed: {error}")

    finally:
        mongo_client.close()
        source_engine.dispose()
        warehouse_engine.dispose()