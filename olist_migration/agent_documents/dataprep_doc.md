We want to create a weekly sales matrix with weekly product revenue by product id, ignoring products that sell very less.

Here is the clean, production-ready script formatted for your coding agent. It combines the data preparation, inventory trim logic, and output formatting into one cohesive module.

```python
"""
Olist E-commerce Data Preparation Script
Purpose: Filter 2017 product revenue for São Paulo (SP) and trim low-revenue inventory.
"""

importpandasas pd


defload_and_clean_data():
    # 1. Load the required Olist datasets
    print("Loading datasets...")
    orders = pd.read_csv("olist_orders_dataset.csv")
    items = pd.read_csv("olist_order_items_dataset.csv")
    products = pd.read_csv("olist_products_dataset.csv")
    customers = pd.read_csv("olist_customers_dataset.csv")

    # 2. Convert timestamps and filter strictly for delivered orders in 2017
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"]
    )
    orders_2017 = orders[
        (orders["order_status"] == "delivered")
        & (orders["order_purchase_timestamp"].dt.year == 2017)
    ]

    # 3. Filter for SP region customers
    sp_customers = customers[customers["customer_state"] == 'SP']
    merged_orders = pd.merge(
        orders_2017,
        sp_customers[["customer_id", "customer_state"]],
        on="customer_id",
    )

    # 4. Merge order details with items and product categories
    df_filtered = pd.merge(
        items,
        merged_orders[["order_id", "order_purchase_timestamp"]],
        on="order_id",
    )
    df_filtered = pd.merge(
        df_filtered,
        products[["product_id", "product_category_name"]],
        on="product_id",
    )

    # 5. Extract ISO week identifier (%Y-%U)
    df_filtered["year_week"] = (
        df_filtered["order_purchase_timestamp"]
        .dt.to_period("W")
        .dt.strftime("%Y-%U")
    )

    return df_filtered


deftrim_low_revenue(df, min_revenue_threshold=100):
    """Filters out products falling below a specified total revenue threshold."""
    print(f"Applying inventory trim (Threshold: {min_revenue_threshold} BRL)...")

    # Calculate total 2017 SP revenue per individual product
    product_total_revenue = (
        df.groupby("product_id")["price"].sum().reset_index()
    )

    # Identify high-performing product IDs
    high_revenue_products = product_total_revenue[
        product_total_revenue["price"] >= min_revenue_threshold
    ]["product_id"]

    # Filter dataframe
    df_trimmed = df[df["product_id"].isin(high_revenue_products)]

    # Print summary metrics
    print(f" -> Original unique products: {df['product_id'].nunique()}")
    print(f" -> Trimmed unique products: {df_trimmed['product_id'].nunique()}")

    return df_trimmed


defgenerate_outputs(df_trimmed):
    """Generates both the long-format weekly breakdown and the matrix view."""
    # Format 1: Long format weekly revenue per product
    weekly_sp_revenue = (
        df_trimmed.groupby(["year_week", "product_id"])["price"]
        .sum()
        .reset_index()
    )
    weekly_sp_revenue.rename(columns={"price": "weekly_revenue"}, inplace=True)

    # Format 2: Matrix/Pivot format by category name
    sp_revenue_matrix = df_trimmed.pivot_table(
        index="year_week",
        columns="product_category_name",
        values="price",
        aggfunc="sum",
        fill_value=0,
    )

    return weekly_sp_revenue, sp_revenue_matrix


if __name__ == "__main__":
    # Execute Pipeline
    raw_filtered_df = load_and_clean_data()

    # Trim bottom inventory (Adjust min_revenue_threshold as needed)
    trimmed_df = trim_low_revenue(
        raw_filtered_df, min_revenue_threshold=100
    )

    # Extract DataFrames
    weekly_revenue_df, revenue_matrix_df = generate_outputs(trimmed_df)

    # Display Previews
    print("\n--- Long Format Preview (Weekly Product Revenue) ---")
    print(weekly_revenue_df.head())

    print("\n--- Matrix Format Preview (Weekly Category Revenue) ---")
    print(revenue_matrix_df.head())
```

If you plan to have your coding agent build further on this script, tell me if you would like me to add:

* An automated export step to save these outputs directly to CSV files
* An outlier detection routine to flag massive revenue spikes
* A data validation check to catch missing product categories or invalid timestamps [1]

Let me know what your coding agent needs next!

[1] [https://medium.com](https://medium.com/versent-tech-blog/seamlessly-migrate-digital-user-identities-a-step-by-step-guide-7f1db4a9c997)
