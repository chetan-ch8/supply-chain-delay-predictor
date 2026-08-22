SELECT
    seller_id,
    seller_state,
    COUNT(*)                                    AS total_orders,
    ROUND(100.0 * AVG(is_late::numeric), 2)       AS late_rate_pct,
    ROUND(AVG(delivery_delay_days)::numeric, 2)   AS avg_delay_days,
    ROUND(AVG(distance_km)::numeric, 1)           AS avg_distance_km
FROM olist_master
GROUP BY seller_id, seller_state
HAVING COUNT(*) >= 20
ORDER BY late_rate_pct DESC
LIMIT 25;