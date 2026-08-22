SELECT 
product_category_name_english AS category,
COUNT(*) AS total_orders,
ROUND(AVG(delivery_delay_days)::numeric,2) AS avg_delay_days,
ROUND(100.0 *AVG(is_late::numeric),2) AS late_rate_pct
FROM olist_master
GROUP BY product_category_name_english
HAVING COUNT(*)>=30
ORDER BY avg_delay_days DESC;