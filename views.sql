/*
  Olist Customer Retention Analysis
  SQL Server views used by the Tableau dashboard.
  Database: Olist
*/

USE Olist;
GO

/* 1. Monthly revenue: delivered orders only, Jan 2017 to Aug 2018
      (months outside this range have very few orders) */
CREATE OR ALTER VIEW vw_monthly_revenue AS
SELECT DATEFROMPARTS(YEAR(o.order_purchase_timestamp), MONTH(o.order_purchase_timestamp), 1) AS month,
       SUM(oi.price + oi.freight_value) AS revenue,
       COUNT(DISTINCT o.order_id) AS orders,
       SUM(oi.price + oi.freight_value) / COUNT(DISTINCT o.order_id) AS aov
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
GROUP BY DATEFROMPARTS(YEAR(o.order_purchase_timestamp), MONTH(o.order_purchase_timestamp), 1);
GO

/* 2. Cohort retention: customers grouped by first purchase month,
      share who ordered again N months later */
CREATE OR ALTER VIEW vw_cohort_retention AS
WITH first_orders AS (
    SELECT c.customer_unique_id,
           MIN(o.order_purchase_timestamp) AS first_order_date
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
    SELECT cohort_month,
           months_since_first,
           COUNT(DISTINCT customer_unique_id) AS customers
    FROM customer_activity
    GROUP BY cohort_month, months_since_first
)
SELECT cohort_month,
       months_since_first,
       customers,
       MAX(CASE WHEN months_since_first = 0 THEN customers END)
           OVER (PARTITION BY cohort_month) AS cohort_size,
       CAST(100.0 * customers /
           MAX(CASE WHEN months_since_first = 0 THEN customers END)
               OVER (PARTITION BY cohort_month) AS DECIMAL(5,2)) AS retention_pct
FROM cohort_counts;
GO

/* 3. Delivery vs reviews: late = delivered after the estimated delivery date */
CREATE OR ALTER VIEW vw_delivery_reviews AS
SELECT o.order_id,
       c.customer_state AS state,
       o.order_purchase_timestamp,
       DATEDIFF(day, o.order_estimated_delivery_date, o.order_delivered_customer_date) AS days_late,
       CASE WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date
            THEN 'Late' ELSE 'On Time' END AS delivery_status,
       r.avg_score AS review_score
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN (
    SELECT order_id, AVG(CAST(review_score AS FLOAT)) AS avg_score
    FROM reviews
    GROUP BY order_id
) r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
  AND o.order_delivered_customer_date IS NOT NULL;
GO
