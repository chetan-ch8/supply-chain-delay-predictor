SELECT
customer_state,
COUNT(*) AS total_orders,
SUM(is_late) AS late_orders,
ROUND(100.0 * (1-AVG(is_late::numeric)),2) AS on_time_rate_pct,
ROUND(AVG(delivery_delay_days)::numeric,2) AS avg_delay_days
FROM olist_master
GROUP BY customer_state
ORDER BY on_time_rate_pct ASC;