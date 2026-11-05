import os
from datetime import date
import pandas as pd
import psycopg2
import streamlit as st
from config import PG_HOST , PG_PORT , PG_USER , PG_DATABASE , PG_PASSWORD , PG_SOURCE_DATABASE

# ==================================================
# 1. Streamlit Configuration
# ==================================================

st.set_page_config(
    page_title="PostgreSQL - Customers",
    page_icon="👥",
    layout="wide"
)

st.title("👥 PostgreSQL Customers Dashboard")
st.caption("Explore, search, add, and edit customers")


# ==================================================
# 2. Database Connection
# ==================================================

def get_connection():
    return psycopg2.connect(
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=int(PG_PORT),
            database=PG_SOURCE_DATABASE
        
    )

# ==================================================
# 3. Database Helper Functions
# ==================================================

def fetch_one(query, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchone()
    finally:
        conn.close()


def fetch_dataframe(query, params=None):
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def execute_write(query, params):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
    finally:
        conn.close()


def get_customer(customer_id):
    return fetch_one(
        """
        SELECT customer_id, name, email, country, signup_date
        FROM customers
        WHERE customer_id = %s
        """,
        (customer_id,)
    )


# ==================================================
# 4. Session State
# ==================================================

if "page_number" not in st.session_state:
    st.session_state.page_number = 1

if "edit_customer" not in st.session_state:
    st.session_state.edit_customer = None


# ==================================================
# 5. Database Connection Check
# ==================================================

try:
    fetch_one("SELECT 1")
except Exception as error:
    st.error(
        "Could not connect to PostgreSQL. "
        "Check your database settings and password."
    )
    st.exception(error)
    st.stop()


# ==================================================
# 6. Dashboard Statistics
# ==================================================

st.subheader("📊 Customer Statistics")

total_customers = fetch_one(
    "SELECT COUNT(*) FROM customers"
)[0]

customers_this_year = fetch_one(
    """
    SELECT COUNT(*)
    FROM customers
    WHERE signup_date >= DATE_TRUNC('year', CURRENT_DATE)::date
      AND signup_date < (
          DATE_TRUNC('year', CURRENT_DATE)
          + INTERVAL '1 year'
      )::date
"""
)[0]

countries_count = fetch_one(
    """
    SELECT COUNT(DISTINCT country)
    FROM customers
    WHERE country IS NOT NULL
"""
)[0]

col1, col2, col3 = st.columns(3)

col1.metric("Total Customers", f"{total_customers:,}")
col2.metric("Signed Up This Year", f"{customers_this_year:,}")
col3.metric("Countries", f"{countries_count:,}")


# ==================================================
# 7. Customers Per Year Chart
# ==================================================

st.subheader("📈 Customer Signups by Year")

yearly_data = fetch_dataframe(
    """
    SELECT
        EXTRACT(YEAR FROM signup_date)::INT AS year,
        COUNT(*) AS total_customers
    FROM customers
    WHERE signup_date IS NOT NULL
    GROUP BY EXTRACT(YEAR FROM signup_date)
    ORDER BY year
    """
)

if not yearly_data.empty:
    chart_data = yearly_data.set_index("year")
    st.line_chart(chart_data["total_customers"])
else:
    st.info("No signup dates are available to display.")


# ==================================================
# 8. Filters and Pagination
# ==================================================

st.divider()
st.subheader("🔎 Browse Customers")

filter_col1, filter_col2 = st.columns([1, 2])

with filter_col1:
    selected_year = st.selectbox(
        "Filter by Signup Year",
        options=[
            "All Years", 2020, 2021, 2022, 2023,
            2024, 2025, 2026
        ],
        key="signup_year_filter",
        on_change=lambda: st.session_state.update(
            page_number=1
        )
    )

with filter_col2:
    search_text = st.text_input(
        "Search by Name or Email",
        placeholder="Enter a name or email...",
        key="customer_search"
    )

where_parts = []
query_params = []

if selected_year != "All Years":
    where_parts.append(
        """
        signup_date >= %s
        AND signup_date < %s
        """
    )
    query_params.extend([
        date(int(selected_year), 1, 1),
        date(int(selected_year) + 1, 1, 1)
    ])

if search_text.strip():
    where_parts.append(
        "(name ILIKE %s OR email ILIKE %s)"
    )
    search_pattern = f"%{search_text.strip()}%"
    query_params.extend([search_pattern, search_pattern])

where_clause = (
    "WHERE " + " AND ".join(where_parts)
    if where_parts
    else ""
)

# Reset pagination when filters change.
filter_signature = (
    str(selected_year),
    search_text.strip()
)

if st.session_state.get("previous_filter") != filter_signature:
    st.session_state.page_number = 1
    st.session_state.previous_filter = filter_signature

filtered_count = fetch_one(
    f"SELECT COUNT(*) FROM customers {where_clause}",
    tuple(query_params)
)[0]

page_size = 10
total_pages = max(1, (filtered_count + page_size - 1) // page_size)

if st.session_state.page_number > total_pages:
    st.session_state.page_number = total_pages

offset = (st.session_state.page_number - 1) * page_size

customers_df = fetch_dataframe(
    f"""
    SELECT customer_id, name, email, country, signup_date
    FROM customers
    {where_clause}
    ORDER BY customer_id
    LIMIT %s OFFSET %s
    """,
    tuple(query_params + [page_size, offset])
)

st.caption(
    f"Matching customers: {filtered_count:,} | "
    f"Page {st.session_state.page_number} of {total_pages}"
)

st.dataframe(
    customers_df,
    use_container_width=True,
    hide_index=True
)

previous_col, page_col, next_col = st.columns([1, 2, 1])

with previous_col:
    if st.button(
        "⬅️ Previous",
        disabled=st.session_state.page_number <= 1,
        use_container_width=True
    ):
        st.session_state.page_number -= 1
        st.rerun()

with page_col:
    st.markdown(
        f"<div style='text-align:center'>"
        f"Page <b>{st.session_state.page_number}</b> "
        f"of <b>{total_pages}</b></div>",
        unsafe_allow_html=True
    )

with next_col:
    if st.button(
        "Next ➡️",
        disabled=st.session_state.page_number >= total_pages,
        use_container_width=True
    ):
        st.session_state.page_number += 1
        st.rerun()


# ==================================================
# 9. Add Customer
# ==================================================

st.divider()
st.subheader("➕ Add Customer")

with st.form("add_customer_form", clear_on_submit=True):
    new_name = st.text_input("Customer Name")
    new_email = st.text_input("Email")
    new_country = st.text_input("Country")

    new_signup_date = st.date_input(
        "Signup Date",
        value=date.today()
    )

    add_submitted = st.form_submit_button(
        "Add Customer",
        use_container_width=True
    )

    if add_submitted:
        if not new_name.strip() or not new_email.strip():
            st.error("Name and email are required.")
        else:
            try:
                conn = get_connection()
                try:
                    with conn:
                        with conn.cursor() as cur:
                            # The existing source schema does not
                            # declare customer_id as auto-generated.
                            cur.execute(
                                """
                                SELECT COALESCE(MAX(customer_id), 0) + 1
                                FROM customers
                                """
                            )
                            new_id = cur.fetchone()[0]

                            cur.execute(
                                """
                                INSERT INTO customers
                                    (customer_id, name, email,
                                     country, signup_date)
                                VALUES (%s, %s, %s, %s, %s)
                                """,
                                (
                                    new_id,
                                    new_name.strip(),
                                    new_email.strip(),
                                    new_country.strip() or None,
                                    new_signup_date
                                )
                            )
                finally:
                    conn.close()

                st.success(
                    f"Customer added successfully. ID: {new_id}"
                )
                st.rerun()

            except psycopg2.errors.UniqueViolation:
                st.error(
                    "This email or customer ID already exists."
                )
            except Exception as error:
                st.error(f"Could not add customer: {error}")


# ==================================================
# 10. Find Customer to Edit
# ==================================================

st.divider()
st.subheader("✏️ Edit Customer")

with st.form("find_customer_form"):
    customer_id_to_edit = st.number_input(
        "Enter Customer ID",
        min_value=1,
        step=1
    )

    find_submitted = st.form_submit_button(
        "Load Customer",
        use_container_width=True
    )

    if find_submitted:
        try:
            customer = get_customer(int(customer_id_to_edit))

            if customer is None:
                st.session_state.edit_customer = None
                st.error("Customer ID not found.")
            else:
                st.session_state.edit_customer = customer
                st.rerun()

        except Exception as error:
            st.error(f"Could not load customer: {error}")


# ==================================================
# 11. Edit Customer Form
# ==================================================

customer = st.session_state.edit_customer

if customer is not None:
    customer_id, old_name, old_email, old_country, old_date = customer

    st.write(f"Editing Customer ID: *{customer_id}*")

    with st.form("edit_customer_form"):
        edited_name = st.text_input(
            "Name",
            value=old_name or ""
        )
        edited_email = st.text_input(
            "Email",
            value=old_email or ""
        )
        edited_country = st.text_input(
            "Country",
            value=old_country or ""
        )
        edited_date = st.date_input(
            "Signup Date",
            value=old_date or date.today()
        )

        save_submitted = st.form_submit_button(
            "Save Changes",
            use_container_width=True
        )

        if save_submitted:
            if not edited_name.strip() or not edited_email.strip():
                st.error("Name and email are required.")
            else:
                try:
                    execute_write(
                        """
                        UPDATE customers
                        SET name = %s,
                            email = %s,
                            country = %s,
                            signup_date = %s
                        WHERE customer_id = %s
                        """,
                        (
                            edited_name.strip(),
                            edited_email.strip(),
                            edited_country.strip() or None,
                            edited_date,
                            customer_id
                        )
                    )

                    st.session_state.edit_customer = None
                    st.success("Customer updated successfully.")
                    st.rerun()

                except psycopg2.errors.UniqueViolation:
                    st.error("That email is already used.")
                except Exception as error:
                    st.error(f"Could not update customer: {error}")


# ==================================================
# 12. Footer
# ==================================================

st.divider()
st.caption(
    "E-Commerce Data Engineering Project | PostgreSQL Source"
)