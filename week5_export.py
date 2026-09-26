"""
Olist Week 5: forecast + CSV exports for Tableau
Run: pip install pandas sqlalchemy pyodbc scipy
"""
import os
import pandas as pd
from sqlalchemy import create_engine

# ---------- 1. CONNECT ----------
# Change SERVER to what you see in SSMS when you log in (e.g. localhost or localhost\SQLEXPRESS)
# If you get a driver error, try "ODBC Driver 18 for SQL Server" and add &TrustServerCertificate=yes
SERVER = r"localhost"
DATABASE = "Olist"
engine = create_engine(
    f"mssql+pyodbc://@{SERVER}/{DATABASE}"
    "?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)

os.makedirs("tableau_data", exist_ok=True)


def run(sql):
    return pd.read_sql(sql, engine)


# ---------- 2. MONTHLY REVENUE ----------
# Only delivered orders. Cut off the thin months at the start and end of the dataset.
monthly = run("""
SELECT DATEFROMPARTS(YEAR(o.order_purchase_timestamp), MONTH(o.order_purchase_timestamp), 1) AS month,
       SUM(oi.price + oi.freight_value) AS revenue,
       COUNT(DISTINCT o.order_id) AS orders
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
GROUP BY DATEFROMPARTS(YEAR(o.order_purchase_timestamp), MONTH(o.order_purchase_timestamp), 1)
ORDER BY month
""")
monthly["month"] = pd.to_datetime(monthly["month"])
monthly["aov"] = monthly["revenue"] / monthly["orders"]


# ---------- 3. FORECAST (3 month moving average) ----------
# Each future month = average of the 3 months before it (uses its own forecasts as it goes)
history = list(monthly["revenue"])
last_month = monthly["month"].max()
forecast_rows = []
for i in range(1, 4):
    next_value = sum(history[-3:]) / 3
    history.append(next_value)
    forecast_rows.append({
        "month": last_month + pd.DateOffset(months=i),
        "revenue": next_value,
        "type": "Forecast",
    })

actuals = monthly[["month", "revenue"]].assign(type="Actual")
forecast = pd.concat([actuals, pd.DataFrame(forecast_rows)], ignore_index=True)

monthly.to_csv("tableau_data/monthly_revenue.csv", index=False)
forecast.to_sql("revenue_forecast", engine, if_exists="replace", index=False)


# ---------- 4. COHORT RETENTION (your query) ----------
cohort = run("""
WITH first_orders AS (
    SELECT c.customer_unique_id, MIN(o.order_purchase_timestamp) AS first_order_date
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
),
customer_activity AS (
    SELECT c.customer_unique_id,
           DATEFROMPARTS(YEAR(fo.first_order_date), MONTH(fo.first_order_date), 1) AS cohort_month,
           DATEDIFF(month, fo.first_order_date, o.order_purchase_timestamp) AS months_since_first
    FROM first_orders fo
    JOIN customers c ON fo.customer_unique_id = c.customer_unique_id
    JOIN orders o ON c.customer_id = o.customer_id
),
cohort_counts AS (
    SELECT cohort_month, months_since_first, COUNT(DISTINCT customer_unique_id) AS customers
    FROM customer_activity
    GROUP BY cohort_month, months_since_first
)
SELECT cohort_month, months_since_first, customers,
       MAX(CASE WHEN months_since_first = 0 THEN customers END)
           OVER (PARTITION BY cohort_month) AS cohort_size,
       CAST(100.0 * customers /
           MAX(CASE WHEN months_since_first = 0 THEN customers END)
               OVER (PARTITION BY cohort_month) AS DECIMAL(5,2)) AS retention_pct
FROM cohort_counts
""")
cohort.to_csv("tableau_data/cohort_retention.csv", index=False)


# ---------- 5. RFM SEGMENTS ----------
rfm = run("""
SELECT c.customer_unique_id,
       MAX(c.customer_state) AS state,
       MAX(o.order_purchase_timestamp) AS last_order,
       COUNT(DISTINCT o.order_id) AS frequency,
       SUM(oi.price + oi.freight_value) AS monetary
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_unique_id
""")
snapshot = pd.to_datetime(rfm["last_order"]).max() + pd.Timedelta(days=1)
rfm["recency_days"] = (snapshot - pd.to_datetime(rfm["last_order"])).dt.days

# 1 to 5 scores (5 = best). Frequency is almost always 1 in Olist, so we lean on R and M.
rfm["R"] = pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["M"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)


def segment(row):
    if row["frequency"] >= 2:
        return "Loyal"
    if row["R"] >= 4 and row["M"] >= 4:
        return "High Value New"
    if row["R"] >= 4:
        return "Recent"
    if row["R"] <= 2 and row["M"] >= 4:
        return "At Risk"
    if row["R"] <= 2:
        return "Lost"
    return "Needs Attention"


rfm["segment"] = rfm.apply(segment, axis=1)
rfm.to_sql("rfm_segments", engine, if_exists="replace", index=False)


# ---------- 6. DELIVERY VS REVIEWS ----------
# Skipped here: Tableau reads vw_delivery_reviews straight from SQL Server,
# and you already ran the t-test in Week 4.


# ---------- 7. SUMMARY ----------
print("Done. Files are in tableau_data/")
print(f"Forecast next 3 months: {[round(r['revenue']) for r in forecast_rows]}")
print(rfm["segment"].value_counts())
