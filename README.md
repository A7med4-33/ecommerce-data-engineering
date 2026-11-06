E-Commerce Data Engineering Project

📌 Project Overview

This project implements an end-to-end Data Engineering pipeline for an e-commerce business. It integrates structured data from PostgreSQL with semi-structured data from MongoDB, applies data cleaning and validation, and loads the transformed data into a PostgreSQL Data Warehouse for analytical reporting.

A Streamlit dashboard provides insights into sales performance, customer behavior, product revenue, and customer reviews.

🎯 Project Objectives

- Extract data from PostgreSQL and MongoDB.
- Clean and transform data using Python and Pandas.
- Validate data quality and check key constraints.
- Build a PostgreSQL Data Warehouse using a Star Schema.
- Perform analytical SQL queries.
- Develop an interactive Streamlit dashboard.
- Analyze customer reviews and ratings from MongoDB.

🛠️ Technologies Used

- Python — Data processing and ETL orchestration
- PostgreSQL — Source database and Data Warehouse
- MongoDB — NoSQL customer reviews and activity data
- Pandas — Data extraction, cleaning, and transformation
- SQLAlchemy — Database connectivity
- PyMongo — MongoDB connectivity
- Streamlit — Interactive dashboard
- Git & GitHub — Version control and project hosting

🏗️ Architecture

1. Data Sources
   
   - PostgreSQL: customers, products, orders, order items, and payments.
   - MongoDB: reviews and user activity.

2. ETL Pipeline
   
   - Extract data from both sources.
   - Clean records and handle duplicates.
   - Validate primary keys, relationships, prices, quantities, and ratings.
   - Transform the data into analytical dimensions and facts.

3. Data Warehouse
   
   The "ecommerce_dw" database contains five tables:
   
   - "dim_customer"
   - "dim_product"
   - "dim_date"
   - "dim_payment"
   - "fact_sales"

4. Analytics and Visualization
   
   - SQL analytical queries.
   - Streamlit sales dashboard.
   - Date and product category filters.
   - Customer review and rating analysis.

📊 Dashboard Features

- Total revenue
- Total orders
- Unique customers
- Average order value
- Monthly revenue trends
- Top five products by revenue
- Revenue by product category
- Customer review statistics
- Average rating and rating distribution

📁 Project Structure

ecommerce-data-engineering/
├── app.py
├── etl_pipeline.py
├── sql_queries.sql
├── README.md
└── pages/
    ├── sales_dashboard.py
    ├── postgres.py
    ├── mongo.py
    ├── etl_pipline.py
    ├── oltp_olap.py
    ├── hadoop_demo.py
    ├── partitioned.py
    └── add_user_pg.py

⚙️ Prerequisites

- Python 3.10 or later
- PostgreSQL
- MongoDB
- Git

🚀 Installation and Setup

1. Clone the Repository

git clone YOUR_GITHUB_REPOSITORY_URL
cd ecommerce-data-engineering

2. Install Dependencies

pip install streamlit pandas sqlalchemy psycopg2-binary pymongo

3. Configure Database Connections

Update the PostgreSQL and MongoDB connection settings in the relevant Python files.

Ensure that the following databases exist and contain the required data:

- "ecommerce_source"
- "ecommerce_dw"
- "ecommerce_nosql"

Security: Never commit database passwords, credentials, or other secrets to GitHub.

4. Run the Dashboard

streamlit run app.py

Open the local URL displayed in the terminal.

🧪 Data Quality

The ETL pipeline includes validation checks for:

- Missing and duplicate identifiers
- Invalid product prices
- Invalid order quantities
- Referential integrity between customers, orders, order items, and products
- Customer review ratings outside the valid range

📈 Analytical SQL

The project includes analytical queries covering:

- Total revenue and order counts
- Average order value
- Monthly and yearly revenue
- Revenue by product category
- Top-selling products
- Highest-spending customers
- Payment method statistics
- High-value customer identification

📸 Project Screenshots

🐘 PostgreSQL

Screenshots of the PostgreSQL database and customer management.

🍃 MongoDB

Screenshots of MongoDB collections and NoSQL data.

⚙️ ETL Pipeline

Screenshots of the ETL process and data warehouse loading.

📊 Sales Dashboard

Screenshots of the sales analytics dashboard and visualizations.

🔮 Future Improvements

- Add automated ETL tests.
- Schedule recurring pipeline execution.
- Improve logging and error monitoring.
- Add more customer behavior analytics.
- Deploy the dashboard to a cloud platform.

👨‍💻 Author

Ahmed Mohamed

Data Engineering Learner | Python | SQL | PostgreSQL | MongoDB | ETL | Data Warehousing
