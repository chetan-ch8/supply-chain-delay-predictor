SELECT
DATE_TRUNC('month',order_purchase_timestamp)::date AS month,
COUNT(*) AS total_orders,
ROUND(100.0 * AVG(is_late::numeric),2) AS late_rate_pct,
ROUND(AVG(delivery_delay_days)::numeric,2) AS avg_delay_days
FROM olist_master
GROUP BY 1
ORDER BY 1;