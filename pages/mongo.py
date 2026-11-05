import streamlit as st
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import PyMongoError


@st.cache_resource
def get_mongo_client():
    return MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=5000
    )


def show_mongo_page():
    st.title("🍃 MongoDB Dashboard")
    st.caption("E-Commerce NoSQL Data")

    try:
        client = get_mongo_client()
        db = client["ecommerce_nosql"]

        # Check connection
        client.admin.command("ping")

        reviews_collection = db["reviews"]
        activity_collection = db["user_activity"]

        # Summary metrics
        total_reviews = reviews_collection.count_documents({})
        total_activities = activity_collection.count_documents({})

        col1, col2 = st.columns(2)

        col1.metric("Total Reviews", f"{total_reviews:,}")
        col2.metric("User Activity Records", f"{total_activities:,}")

        st.divider()

        # Reviews
        st.subheader("⭐ Product Reviews")

        reviews = list(
            reviews_collection.find({}, {"_id": 0})
        )

        if reviews:
            reviews_df = pd.json_normalize(reviews)
            st.dataframe(
                reviews_df,
                use_container_width=True,
                hide_index=True
            )

            if "rating" in reviews_df.columns:
                ratings = pd.to_numeric(
                    reviews_df["rating"],
                    errors="coerce"
                ).dropna()

                if not ratings.empty:
                    avg_rating = ratings.mean()
                    st.metric("Average Rating", f"{avg_rating:.2f} / 5")

                    rating_counts = (
                        ratings.value_counts()
                        .sort_index()
                        .rename_axis("Rating")
                        .reset_index(name="Reviews")
                    )

                    st.bar_chart(
                        rating_counts.set_index("Rating")
                    )
        else:
            st.info("No reviews found in MongoDB.")

        st.divider()

        # User Activity
        st.subheader("🧭 User Activity")

        activities = list(
            activity_collection.find({}, {"_id": 0})
        )

        if activities:
            activity_df = pd.json_normalize(activities)
            st.dataframe(
                activity_df,
                use_container_width=True,
                hide_index=True
            )

            if "actions" in activity_df.columns:
                action_rows = []

                for activity in activities:
                    for action in activity.get("actions", []):
                        action_rows.append({
                            "customer_id": activity.get("customer_id"),
                            "session_id": activity.get("session_id"),
                            "action": action.get("action"),
                            "product_id": action.get("product_id"),
                            "timestamp": action.get("timestamp")
                        })

                if action_rows:
                    actions_df = pd.DataFrame(action_rows)

                    st.subheader("📊 Actions Breakdown")

                    st.bar_chart(
                        actions_df["action"].value_counts()
                    )

                    with st.expander("View flattened actions"):
                        st.dataframe(
                            actions_df,
                            use_container_width=True,
                            hide_index=True
                        )
        else:
            st.info("No user activity found in MongoDB.")

    except PyMongoError as error:
        st.error(f"Could not connect to MongoDB: {error}")


show_mongo_page()